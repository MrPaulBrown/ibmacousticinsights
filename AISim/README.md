# AISim script

This script simulates sending a sequence of sounds files to Acoustic Insights for scoring.

## Set-up

Set up the environment and common libraries as per the general README.md

### Models deployed in IBM Acoustic Insights

These scripts require at least one model to be deployed in IBM Acoustic Insights and accessible via the classify API

### Config file

Modify the config file (AISim.config) to set the following options:

[Images]  
Directory:  **Set to the local path location of your sound files**  
WildcardPattern: **Set to match to a wildcard pattern**  

[Score]  
Host: **Set to Visual Insights host URL**  
Tenant: **Set to desired tenant ID**  
Cell: **Set to scoring cell for classification model**  
Product: **Set to product type code for classification model**  

## Usage

Run from python, e.g.

`python AISim.py`

The script will launch a UI to allow the user to configure the simulation.  In addition, the setting of the "Directory" path in the configuration will govern the simulator behavior:

+ If the Directory only contains images (no sub-directories) then the simulator will pick images from random from the Directory.  
+ If the directory contains sub-directories of images then the UI will be configured to allow the user to 'balance' the images from each sub-directory.  At each iteration, the simulator will pick a sub-directory based on the relative balance of all sub-directories and then choose an image at random from that folder.  

The script will create a window showing the current scored image.  This will update as each new image is scored.

UI Controls

The user can control:

+ the request rate (in requests per minute)  
+ the duration of the simulation (in minutes)  
+ starting and stopping of the simulation  

Commands:  
Esc: Quit  

### Explanation of output

Score time is shown as the number of s in the bottom corner of the capture window

The status updates to show the latest scored sound file name, the scoring response (200 if scoring is successful) and the response time for the score (in seconds).  Note that there is a delay between the sound being recorded and the results of scoring.  

The bars on the left are updated to show the classification results of the last sound file scored.  The bars on the right show the cumulative results of scoring.  
