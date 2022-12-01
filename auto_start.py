import requests
import os
import time

cmd = 'python3 main.py'

os.system(cmd)
time.sleep(1)
requests.get(url='http://127.0.0.1:5000/video_feed')
