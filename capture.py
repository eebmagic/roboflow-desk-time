'''
This script is for capturing lots of images from a security camera I have
connected to a linux box in the corner of my room. 

Takes a picture every 20 seconds (SLEEP var) over 48 hours,
for a total of 8,640 images.
'''

import os
import time
from datetime import datetime
import cv2
import subprocess

def capture():
    global E
    try:
        filename = datetime.now().isoformat(timespec='seconds').replace(':', '-')
        filepath = f'images/{filename}.jpg'

        subprocess.check_call("v4l2-ctl -d /dev/video0 -c exposure_auto=1",shell=True)
        subprocess.check_call("v4l2-ctl -d /dev/video0 -c exposure_absolute=156",shell=True)

        # window for exposure reset
        time.sleep(0.5)

        cmd = f'fswebcam -r 1280x720 --no-banner --device /dev/video0 {filepath}'
        subprocess.check_call(cmd, shell=True)

        print(f'IMAGE: {filepath}')

        return filepath
    except Exception as e:
        print('EXCEPTION!')
        print(e)
        return False

HOUR = 60 * 60
SLEEP = 20
START = time.time()
END = START + (48 * HOUR)

print(f'ending at: {END}')

while time.time() < END:
    completed = capture()
    
    if not completed:
        print('ISSUE WITH CAPTURE:')

    time.sleep(SLEEP)
