# If MOTION_DETECTION set to True, motion detection will be primary means of application making API calls
# and storing data. If set to False, application will do an API call every 5 seconds and store and only take
# photos if a RSSI meets or exceeds TARGET_RSSI
MOTION_DETECTION = False

# If GRAB_APS is set to True, data will be stored for APs as well as other WiFi devices that exceed TARGET_RSSI
# by default, set to False to reduce false positives
GRAB_APS = False

# TARGET_RSSI determines the strength a WiFi device needs to be seen to record into .csv and have a picture taken
# if MOTION_DETECTION is False. Lowering this value can result in more false positives
TARGET_RSSI = -72

# The following parameters are for logging into the monitoring Kismet server. Local machine Kismet server can be set
# with value 'localhost' or '127.0.0.1'
USERNAME = 'kismet'
PASSWORD = 'kismet'
IP = '192.168.8.118'

# COUNT designates how many photos are taken each time the application is triggered to take photos, with a .5 second
# inbetween each photo
COUNT = 3

# CAMERA designates which camera to use for the application. Observed behavior for a Surface Pro is below:
# 0: Front facing camera, if it exists
# 1: Back facing camera, if it exists
# 2: Additional cameras
# With this in mind, if a device, like a Raspberry Pi, does not have an onboard camera, the first camera added will be 0
CAMERA = 0

# Start designates whether or not the application is actually 'capturing' meaning that it can be triggered to take
# photos and make API calls by either motion or RSSI detection. If set to True, application will start as soon as
# launched
START = False

# STREAM determines whether the camera feed is live when the server is accessed. This constant does not impact capture
# meaning that even when STREAM is False, the camera server will behave as normal when capturing.
STREAM = True

# SENSITIVITY dictates the size of an object or distance of an object from the camera to trigger motion detection.
# This constant will need to be altered and tested before employment depending on the distance your target spot is from
# your sensor. A value of 10000 will set off motion detection when waving a hand in front of a webcam.
SENSITIVITY = 5000

# ROTATION is an integer variable that designates the rotation of the camera image as well as the images that are taken
# when the camera is triggered. Default is 0
ROTATION = 0

IMAGE_DIRECTORY = 'images'