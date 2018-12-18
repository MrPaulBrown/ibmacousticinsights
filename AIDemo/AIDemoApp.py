import time
import sys
import threading
import _thread
from kivy.clock import Clock, mainthread
from configparser import SafeConfigParser
import re
from os import path
import glob
import requests
import json
import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.garden.bar import Bar
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
import pyaudio
import wave
import os

default_config = 'AIDemo.config'
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

FORMAT = pyaudio.paInt16

def getColor(i):
    return color_palette[i % len(color_palette)]

class Timer:
    def __enter__(self):
        self.start = time.clock()
        return self

    def __exit__(self, *args):
        self.end = time.clock()
        self.interval = self.end - self.start

def score_sound(host, cell, product, user, tenant, apikey, sound_path):

    # Open file and load into content
    files = {'file': open(sound_path, 'rb')}

    # Set API headers

    # Get inspectid
    inspectid = path.basename(sound_path)

    # Get inspect id from filename and add to params
    classify_params = { 'cell': cell, 'user': user, 'solution': 'ai', 'tenant': tenant, 'productKey': product, 'inspectId': inspectid }
    classify_url = host + "/ibm/iotm/ai/service/classify"
    classify_headers = { 'APIKEY': apikey }

    # score against the Edge API
    with Timer() as response_time:
        try:
            r = requests.post(classify_url, params=classify_params, headers=classify_headers, files=files)

            # print('classify response: ' + str(r.status_code))
            # print(r.text)

        except requests.exceptions.RequestException as e:
            print(e)
            sys.exit(1)

        result_id = None

        try:
            parsed = json.loads(r.text)

            errors = parsed['error_message']
            for err in errors:
                print(str(err))

        except ValueError:
            print("Classify JSON Error: " + r.text)

        # # delay before requesting results
        # time.sleep(3.5)
        #
        # if result_id == None:
        #     print('No result ID')
        # else:
        #
        #     try:
        #         result_url = host + "/ibm/iotm/service/inspectResult/" + result_id
        #         result_params = { 'cell': cell, 'user': user, 'solution': 'ai', 'tenant': tenant }
        #         result_headers = { 'APIKEY': apikey, 'CSRFid': 'ai' }
        #
        #         r = requests.get(result_url, params=result_params, headers=result_headers)
        #
        #         # print(r.text)
        #         # print('inspectResult response: ' + str(r.status_code))
        #         print(r.text)
        #
        #     except requests.exceptions.RequestException as e:
        #         print(e)
        #         sys.exit(1)

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

class AIDemo(BoxLayout):

    stop = threading.Event()
    scorer = None
    current_image = None
    bars = {}
    cbars = {}
    bar_colors = {}
    bar_total = 0
    bar_counts = {}

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
            result = json.loads(text)

            inspect_results = result['inspectResult']

            if len(inspect_results) == 0:
                print("Error: no results!")
            else:
                details = inspect_results[0]['detail']

                det_dict = {}
                if details != None:

                    # Use segment with highest confidence (for now)
                    # for det in details:
                    #
                    #     det_conf = det['confidence'] * 100
                    #     det_type = det['class']
                    #
                    #     if det_type not in det_dict:
                    #         det_dict[det_type] = det_conf
                    #     else:
                    #         if det_conf > det_dict[det_type]:
                    #             det_dict[det_type] = det_conf

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

    @mainthread
    def updateResults(self, status, responseTime, soundPath, responseText):
        self.updateStatus(status)
        self.updateResponseTime(responseTime)
        self.updateResponseText(responseText)
        self.updateSound(soundPath)

    @mainthread
    def updateProgress(self, count, pct):
        if count == -1:
            self.ids.progress.text = 'Not Running'
        else:
            self.ids.progress.text = 'Progress: {} sounds, {:.1f}%'.format(count, pct)

        self.ids.pb.value = pct

    def setScorer(self, scorer):
        self.scorer = scorer


    """PyAudio example: Record a few seconds of audio and save to a WAVE file."""
    def recordSample(self, filename):

        p = pyaudio.PyAudio()

        stream = p.open(format=FORMAT,
                        channels=self.sound_channels,
                        rate=self.sound_rate,
                        input=True,
                        frames_per_buffer=self.sound_chunk)

        print("* recording")

        frames = []

        # Set it to add 0.1 seconds so that samples are slightly longer than requested
        sampleLength = self.ids.sampleLengthSlider.value + 0.1

        for i in range(0, int(self.sound_rate / self.sound_chunk * sampleLength)):
            data = stream.read(self.sound_chunk)
            frames.append(data)

        print("* done recording")

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.sound_channels)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(self.sound_rate)
        wf.writeframes(b''.join(frames))
        wf.close()

    def record(self):

        # print ("Starting recording")

        start_time = time.time()
        last_time = start_time
        current_duration = 0
        # print("Start Time: %s", time.ctime(start_time))

        num_sounds = 0

        # Repeat until duration finishes
        while not(self.stop.is_set()) and \
            ((time.time() - start_time) < (self.ids.durationSlider.value * 60)):

            # Create sound path Name
            sound_filename = path.join(self.sound_path, self.ids.labelSelect.text + str(time.time()) + ".wav")

            # Record the sample
            self.recordSample(sound_filename)

            if self.ids.scoringSwitch.active == True:

                #(host, cell, product, user, tenant, apikey, product, sound_path):
                # Score the image on a thread
                threading.Thread(target=score_sound,
                    args=(self.host, self.cell, self.product, self.user, self.tenant, self.apikey, sound_filename),
                    kwargs={},
                    ).start()
                # _thread.start_new_thread(self.scorer.score(sound_filename))

                # self.scorer.score(sound_filename)

            current_time = time.time()
            current_duration = current_time - last_time

            # print("request_rate: %d", self.ids.requestRateSlider.value)
            # print("required_duration: %f", required_duration)

            progress = ((current_time - start_time) / (self.ids.durationSlider.value * 60)) * 100

            self.updateProgress(num_sounds + 1, progress)

            time.sleep(0.1)

            # print("Time: %s", time.ctime(time.time()))

            last_time = time.time()

            num_sounds += 1

        print ("Exiting recording")
        self.stopRecording()

    def startRecording(self):
        self.stop.clear()
        self.ids.btn.background_color = (1, 0, 0, 0.5)
        self.ids.btn.text = 'Stop Recording'
        threading.Thread(target=self.record).start()

    def stopRecording(self):
        self.stop.set()
        self.ids.btn.background_color = (0, 1, 0, 0.5)
        self.ids.btn.text = 'Start Recording'
        if self.ids.btn.state == 'down':
            self.ids.btn.state = 'normal'
        self.updateProgress(-1, 0.0)

    def click(self):
        if self.ids.btn.state == 'down':
            self.startRecording()
        else:
            self.stopRecording()

    def buildLabelDropdown(self):
        for label in self.sound_labels:

            print("Adding label: " + label)

            btn = Button(text=label, size_hint_y=None, height=44)

            # for each button, attach a callback that will call the select() method
            # on the dropdown. We'll pass the text of the button as the data of the
            # selection.
            btn.bind(on_release=lambda btn: self.ids.labelDropDown.select(btn.text))

            # then add the button inside the dropdown
            self.ids.labelDropDown.add_widget(btn)


        self.ids.labelSelect.bind(on_release=self.ids.labelDropDown.open)

        # one last thing, listen for the selection in the dropdown list and
        # assign the data to the button text.
        self.ids.labelDropDown.bind(on_select=lambda instance, x: setattr(self.ids.labelSelect, 'text', x))

    def setScoreParams(self, host, cell, product, user, tenant, apikey):
        self.host = host
        self.cell = cell
        self.product = product
        self.user = user
        self.tenant = tenant
        self.apikey = apikey

    def setConfig(self, sound_path, sound_labels, sound_chunk, sound_channels, sound_rate):
        self.sound_path = sound_path
        self.sound_labels = sound_labels
        self.sound_chunk = sound_chunk
        self.sound_channels = sound_channels
        self.sound_rate = sound_rate

class AIDemoApp(App):

    scorer = None

    def build(self):
        root = AIDemo()
        # root.setScorer(self.scorer)
        root.setConfig(self.sound_path, self.sound_labels, self.sound_chunk, self.sound_channels, self.sound_rate)
        root.setScoreParams(self.host, self.cell, self.product, self.user, self.tenant, self.apikey)
        root.buildLabelDropdown()

        return root

    def on_stop(self):
        # The Kivy event loop is about to stop, set a stop signal;
        # otherwise the app window will close, but the Python process will
        # keep running until all secondary threads exit.
        self.root.stop.set()

    @mainthread
    def updateResults(self, status, responseTime, soundPath, responseText):
        return self.root.updateResults(status, responseTime, soundPath, responseText)

    def setScorer(self, scorer):
        self.scorer = scorer

    def setScoreParams(self, host, cell, product, user, tenant, apikey):
        self.host = host
        self.cell = cell
        self.product = product
        self.user = user
        self.tenant = tenant
        self.apikey = apikey

    def setConfig(self, sound_path, sound_labels, sound_chunk, sound_channels, sound_rate):
        self.sound_path = sound_path
        self.sound_labels = sound_labels
        self.sound_chunk = sound_chunk
        self.sound_channels = sound_channels
        self.sound_rate = sound_rate


if __name__ == '__main__':
    args = sys.argv[1:]

    # Parse config file
    parser = SafeConfigParser()
    config_path = args[0] if args else default_config
    config = parser.read(config_path)

    # Record options
    sound_path = parser.get('Record', 'OutputDirectory')
    sound_labels = json.loads(parser.get('Record', 'Labels'))
    sound_labels.append('unknown')
    sound_chunk = int(parser.get('Record', 'Chunk'))
    sound_channels = int(parser.get('Record', 'Channels'))
    sound_rate = int(parser.get('Record', 'Rate'))

    # Scoring options
    host = parser.get('Score', 'Host')
    cell = parser.get('Score', 'Cell')
    product = parser.get('Score', 'Product')
    user =  os.environ['AIUSER']
    apikey = os.environ['AIAPIKEY']
    tenant = parser.get('Score', 'Tenant')

    app = AIDemoApp()
    app.setScoreParams(host=host,cell=cell,product=product,user=user,tenant=tenant,apikey=apikey)
    app.setConfig(sound_path, sound_labels, sound_chunk, sound_channels, sound_rate)

    app.run()
