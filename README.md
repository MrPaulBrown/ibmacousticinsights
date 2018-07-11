# ibmacousticinsights

This Git is intended as a repo for utility and demo scripts for IBM Acoustic Insights

## Common Set up

### Python version

The scripts were built for Python 3.x and tested on Python 3.6

### Environment

These scripts use the following environment variables for access to the Acoustic Insights APIs.

You will need to set these in your environment:

AIUSER:  IBM ID of the user account

AIAPIKEY: API Key for the AIUSER

### Required libraries

The scripts use the following libraries:

pyaudio
requests  
watchdog  

Install via pip using:

`python -m pip install <library-name>`

This script also requires the Kivy UI framework.  Follow these [installation instructions](https://kivy.org/docs/installation/installation.html) to install Kivy

Refer to the README.md for each script for further set-up and usage
