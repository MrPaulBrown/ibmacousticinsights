# AIDemo script

This script provides a tool for recording sounds from an attached microphone and sending them to IBM Acoustic Insights for scoring.  With scoring turned off, the tool can be used as a way to record sounds for training.

### Models deployed in IBM Acoustic Insights

These scripts require at least one model to be deployed in IBM Acoustic Insights and accessible via the classify API

### Config file

Modify the config file (AIDemo.config) to set the following options:

[Images]  
OutputDirectory:  **Set to the local path location of your images**  
Labels: **Provide a list of labels to pick from in the UI - the label will be used in the filename of the recorded audio file**  
Chunk: **Set the Chunk parameter for the recorded sound file**  
Channels: **Set the Channel parameter for the recorded sound file**  
Rate: **Set the sample rate parameter for the recorded sound file**  

[Cloud]  
Host: **Set to Acoustic Insights host URL**  
Tenant: **Set to desired tenant ID**  
Cell: **Set to scoring cell for model**  
Product: **Set to product type code for classification model**  

## Usage

Run from python, e.g.

`python AIDemo.py`

The script will launch a UI to allow the user to configure the simulation.  

UI Controls

The user can control:

+ the label to apply to the sound file (from the pick list)
+ whether to score the sounds
+ the length (in seconds) of the sound sample  
+ the duration of the simulation (in minutes)  
+ starting and stopping of the simulation  

Commands:  
Esc: Quit  

### Explanation of output

The progress bar updates to show the number of sounds recored.  

The status updates to show the latest scored sound file name, the scoring response (200 if scoring is successful) and the response time for the score (in seconds).  Note that there is a delay between the sound being recorded and the results of scoring.  

The bars on the left are updated to show the classification results of the last sound file scored.  The bars on the right show the cumulative results of scoring.  
