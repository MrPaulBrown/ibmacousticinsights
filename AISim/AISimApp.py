import time
import sys
import threading
from kivy.clock import Clock, mainthread
from configparser import SafeConfigParser
import re
from os import path
import glob
import requests
import json
import random
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.garden.bar import Bar
from kivy.uix.label import Label
from kivy.uix.slider import Slider

default_config = 'AISim.config'
no_defect_path = ''
defect_path = ''
image_wildcard = ''

# colors
color_palette = [
    (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1), (1,0,1,1), (0,1,1,1),
    (1,0,0,0.5), (0,1,0,0.5), (0,0,1,0.5), (1,1,0,0.5), (1,0,1,0.5), (0,1,1,0.5),
    (1,0,0,0.25), (0,1,0,0.25), (0,0,1,0.25), (1,1,0,0.25), (1,0,1,0.25), (0,1,1,0.25),
    (1,0,0,0.75), (0,1,0,0.75), (0,0,1,0.75), (1,1,0,0.75), (1,0,1,0.75), (0,1,1,0.75)
    ]

def getColor(i):
    return color_palette[i % len(color_palette)]

class Timer:
    def __enter__(self):
        self.start = time.clock()
        return self

    def __exit__(self, *args):
        self.end = time.clock()
        self.interval = self.end - self.start

class AIScorer(object):

    def __init__(self, host, cell, product, user, tenant, apikey):
        self.host = host
        self.headers = { 'APIKEY': apikey }
        self.payload = { 'cell': cell, 'user': user, 'solution': 'ai', 'tenant': tenant }
        self.product = product

    def score(self, sound_path):

        # Open file and load into content
        files = {'file': open(sound_path, 'rb')}

        # Get inspect id from filename and add to params
        classify_params = self.payload

        inspectid = path.basename(sound_path)
        classify_params['inspectId'] = inspectid
        classify_params['productKey'] = self.product

        classify_url = self.host + "/ibm/iotm/ai/service/classify"

        # score against the Edge API
        with Timer() as response_time:
            try:
                r = requests.post(classify_url, params=classify_params, headers=self.headers, files=files)

                # print('classify response: ' + str(r.status_code))
                # print(r.text)

            except requests.exceptions.RequestException as e:
                print(e)
                sys.exit(1)

            try:
                parsed = json.loads(r.text)

                errors = parsed['error_message']
                for err in errors:
                    print(str(err))

            except ValueError:
                print("Classify JSON Error: " + r.text)

            # time.sleep(10)
            #
            # if result_id == None:
            #     print('No result ID')
            # else:
            #
            #     try:
            #         result_url = self.host + "/ibm/iotm/service/inspectResult/" + result_id
            #
            #         result_headers = self.headers
            #         result_headers['CSRFid'] = 'ai'
            #
            #         r = requests.get(result_url, params=self.payload, headers=result_headers)
            #
            #         # print(r.text)
            #         # print('inspectResult response: ' + str(r.status_code))
            #         print(r.text)
            #
            #     except requests.exceptions.RequestException as e:
            #         print(e)
            #         sys.exit(1)
            #

        # print('Getting app')
        app = App.get_running_app()

        # print('Updating results')
        app.root.updateResults(r.status_code, response_time.interval, sound_path, r.text)

        # print('Updated')

class AIBar(BoxLayout):

    bar = None
    val_label = None
    key_label = None

    def update(self, key, pvalue, cvalue, color):
        if self.bar == None:
            self.bar = Bar()
            self.bar.value = pvalue
            self.bar.color = color
            self.bar.orientation = 'lr'
            self.bar.size_hint_x = 0.5
            self.add_widget(self.bar)
            self.val_label = Label()
            self.val_label.text = str(cvalue)
            self.val_label.size_hint_x = 0.2
            self.val_label.height = '48dp'
            self.add_widget(self.val_label)
            self.key_label = Label()
            self.key_label.text = key
            self.key_label.size_hint_x = 0.3
            self.val_label.height = '48dp'
            self.add_widget(self.key_label)
        else:
            self.bar.value = pvalue
            self.bar.color = color
            self.val_label.text = str(cvalue)
            self.key_label.text = key

class AISim(BoxLayout):

    stop = threading.Event()
    scorer = None
    current_image = None
    bars = {}
    cbars = {}
    bar_colors = {}
    bar_total = 0
    bar_counts = {}

    def __init__(self, **kwargs):
        super(AISim, self).__init__(**kwargs)

        # Create list of sliders
        rates_box = self.ids.rates_box

        img_path = config['Sounds']['Directory']

        self.sliders = {}

        for root, subdirs, files in os.walk(img_path):
            for subdir in subdirs:
                # Create layout
                slider_layout = BoxLayout()
                slider_layout.orientation = 'horizontal'
                slider_layout.size_hint_y = 0.15
                slider_layout.height = '48dp'

                # Create label
                slider_label = Label(text=subdir)

                # Create slider
                slider = Slider()
                slider.min = 0.0
                slider.max = 1.0
                slider.value = 0.5
                slider.step = 0.1

                # Add widgets
                slider_layout.add_widget(slider_label)
                slider_layout.add_widget(slider)

                self.ids.rates_box.add_widget(slider_layout)

                # Add to sliders dictionary
                self.sliders[subdir] = slider

    def updateStatus(self, status):
        self.ids.response_status.text = str(status)
        if str(status) == "200":
            self.ids.response_status.color = (0,1,0,1)
        else:
            self.ids.response_status.color = (1,0,0,1)

    def updateResponseTime(self, time):
        self.ids.response_time.text = "{:10.4f}".format(time)
        if time > 5:
            self.ids.response_time.color = (1,0,0,1)
        elif time > 2:
            self.ids.response_time.color = (1,1,0,1)
        else:
            self.ids.response_time.color = (0,1,0,1)

    def updateResponseText(self, text):
        # self.ids.json_input.text = str(text)

        try:
            parsed = json.loads(text)

            inspect_results = parsed['inspectResult']

            if len(inspect_results) == 0:
                print("Error: no results!")
            else:
                details = inspect_results[0]['detail']

                det_dict = {}
                if details != None:

                    # Use segment with highest confidence (for now)
                    # for det in details:
                    #
                        # det_conf = det['confidence'] * 100
                        # det_type = det['class']
                        #
                        # if det_type not in det_dict:
                        #     det_dict[det_type] = det_conf
                        # else:
                        #     if det_conf > det_dict[det_type]:
                        #         det_dict[det_type] = det_conf

                    # Add other bars
                    majority = inspect_results[0]['majority']

                    for det in majority:
                        det_type = det['class']
                        det_conf = det['confidence']
                        if det_type not in det_dict:
                            det_dict[det_type] = float(det_conf)

                    # First, remove any old bars
                    key_delete_list = []
                    for key in self.bars.keys():
                        if not(key in det_dict):
                            key_delete_list.append(key)

                    for key in key_delete_list:
                        self.ids.bars.remove_widget(self.bars[key])
                        del self.bars[key]

                    # Itertate through new dets, sorted by key
                    i = 0
                    max_key = None
                    max_value = -1
                    max_id = -1
                    for key in sorted(det_dict.keys()):

                        value = det_dict[key]

                        # Get key and value with max value
                        if value > max_value:
                            max_value = value
                            max_key = key
                            max_id = i

                        # If it exists, update it
                        if key in self.bars:
                            bar = self.bars[key]
                            color = self.bar_colors[key]
                            bar.update(key, value, value, color)
                        else:
                            # Else, create a new bar and add it
                            new_bar = AIBar()
                            new_bar.orientation = 'horizontal'
                            new_bar.size_hint_x = 1
                            new_bar.size_hint_y = 1

                            self.ids.bars.add_widget(new_bar)
                            self.bar_colors[key] = getColor(i)
                            new_bar.update(key, value, value, getColor(i))
                            self.bars[key] = new_bar

                        i += 1

                    # Update total
                    self.bar_total += 1

                    # Update cumulative bars
                    for key in sorted(det_dict.keys()):

                        if key not in self.bar_counts:
                            self.bar_counts[key] = 0

                        if key == max_key:
                            self.bar_counts[key] += 1

                    for key in self.bar_counts.keys():

                        cvalue = self.bar_counts[key]
                        pvalue = (cvalue / self.bar_total) * 100

                        cbar = None
                        if key in self.cbars:
                            cbar = self.cbars[key]
                        else:
                            # Else, create a new bar and add it
                            cbar = AIBar()
                            cbar.orientation = 'horizontal'
                            cbar.size_hint_x = 1
                            cbar.size_hint_y = 1

                            self.ids.cbars.add_widget(cbar)
                            self.cbars[key] = cbar

                        cbar.update(key, pvalue, cvalue, self.bar_colors[key])

        except ValueError:  # includes simplejson.decoder.JSONDecodeError
            # If text can't be parsed then print text to console
            print("Response: " + text)

    def updateSound(self, src):
        self.ids.sound_path.text = src

    def updateImage(self, src):
        self.ids.image_path.text = src

        # img = Image()
        # img.source='blank.png'
        # self.ids.image_layout.add_widget(img)

    @mainthread
    def updateResults(self, status, responseTime, imagePath, responseText):
        self.updateStatus(status)
        self.updateResponseTime(responseTime)
        self.updateResponseText(responseText)
        self.updateImage(imagePath)

    @mainthread
    def updateProgress(self, count, pct):
        if count == -1:
            self.ids.progress.text = 'Not Running'
        else:
            self.ids.progress.text = 'Progress: {} images, {:.1f}%'.format(count, pct)

        self.ids.pb.value = pct

    def setScorer(self, scorer):
        self.scorer = scorer

    def prepareSounds(self):

        wildcard = config['Sounds']['WildcardPattern']

        self.file_dict = {}
        if not self.sliders:
            self.files = glob.glob(os.path.join(config['Sounds']['Directory'], wildcard))
        else:
            for key, value in self.sliders.items():
                self.file_dict[key] = glob.glob(os.path.join(config['Sounds']['Directory'], key, wildcard))

    def getSound(self):

        sound_set = None
        # No sliders - return sound from the path
        if not self.sliders:
            sound_set = self.files
        else:
            # Sliders - get cumulative sum
            keys = list(self.sliders.keys())
            sum = 0.0
            for key, value in self.sliders.items():
                sum += value.value

            group = None
            if sum == 0.0:
                # All sliders at zero - select file at random
                sound_set = self.file_dict[random.choice(keys)]
            else:
                # Find the key to use
                rand = random.random() * sum
                cum = 0.0
                for key, value in self.sliders.items():
                    cum += value.value
                    if rand < cum:
                        sound_set = self.file_dict[key]
                        break

        return random.choice(sound_set)


    def simulation(self):

        # print ("Starting simulation")

        start_time = time.time()
        last_time = start_time
        current_duration = 0
        # print("Start Time: %s", time.ctime(start_time))

        self.prepareSounds()

        num_sounds = 0

        # Repeat until duration finishes
        while not(self.stop.is_set()) and \
            ((time.time() - start_time) < (self.ids.durationSlider.value * 60)):

            required_duration = 60 / self.ids.requestRateSlider.value

            # Select image at random based on defect rate
            sound_path = self.getSound()

            # Score the image
            self.scorer.score(sound_path)

            current_time = time.time()
            current_duration = current_time - last_time

            # print("request_rate: %d", self.ids.requestRateSlider.value)
            # print("required_duration: %f", required_duration)

            progress = ((current_time - start_time) / (self.ids.durationSlider.value * 60)) * 100

            self.updateProgress(num_sounds + 1, progress)


            sleep_int = 0.1
            if current_duration < required_duration:
                sleep_int = required_duration - current_duration

            # print("sleep_int: %f", sleep_int)

            time.sleep(sleep_int)

            # print("Time: %s", time.ctime(time.time()))

            last_time = time.time()

            num_sounds += 1

        # print ("Exiting simulation")
        self.stopSimulation()

    def startSimulation(self):
        self.stop.clear()
        self.ids.btn.background_color = (1, 0, 0, 0.5)
        self.ids.btn.text = 'Stop Simulation'
        threading.Thread(target=self.simulation).start()

    def stopSimulation(self):
        self.stop.set()
        self.ids.btn.background_color = (0, 1, 0, 0.5)
        self.ids.btn.text = 'Start Simulation'
        if self.ids.btn.state == 'down':
            self.ids.btn.state = 'normal'
        self.updateProgress(-1, 0.0)

    def click(self):
        if self.ids.btn.state == 'down':
            self.startSimulation()
        else:
            self.stopSimulation()

class AISimApp(App):

    scorer = None

    def build(self):
        root = AISim()
        root.setScorer(self.scorer)
        return root

    def on_stop(self):
        # The Kivy event loop is about to stop, set a stop signal;
        # otherwise the app window will close, but the Python process will
        # keep running until all secondary threads exit.
        self.root.stop.set()

    @mainthread
    def updateResults(self, status, responseTime, imagePath, responseText):
        return self.root.updateResults(status, responseTime,imagePath, responseText)

    def setScorer(self, scorer):
        self.scorer = scorer

if __name__ == '__main__':
    args = sys.argv[1:]

    # Parse config file
    config = SafeConfigParser()
    config_path = args[0] if args else default_config
    config.read(config_path)

    # Scoring options
    host = config['Score']['Host']
    tenant = config['Score']['Tenant']
    cell = config['Score']['Cell']
    product = config['Score']['Product']
    user =  os.environ['AIUSER']
    apikey = os.environ['AIAPIKEY']

    scorer = AIScorer(host=host,cell=cell,product=product,user=user,tenant=tenant,apikey=apikey)

    app = AISimApp()

    app.setScorer(scorer)

    app.run()
