# Kismet Camera Server

Kismet Camera Server is designed to be hosted on a remote device to take photos that could potentially correlate to MAC addresses based on user defined RSSI threshold.
The trigger for the server to take a photo and perform an API call to the locally hosted Kismet Server is either by motion, detected by the camera, or by the existance 
of a strong RSSI that exceeds the user defined RSSI threshold. 

## Dependencies
- python3.8 or greater

## Installation
'''
$ git clone https://github.com/GrokkedBandwidth/kismet_camera_server.git
$ cd kismet_camera_server/
$ pip3 install -r requirements.txt
'''

