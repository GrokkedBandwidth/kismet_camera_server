from flask import Flask, render_template, Response, redirect, url_for, request
from flask_bootstrap import Bootstrap
from forms import CreateKismetForm
import requests
import time
import csv
from datetime import datetime as dt
import cv2

# If MOTION_DETECTION set to True, motion detection will be primary means of application making API calls
# and storing data. If set to False, application will do an API call every 5 seconds and store and only take
# photos if a RSSI meets or exceeds TARGET_RSSI
MOTION_DETECTION = True

# If GRAB_APS is set to True, data will be stored for APs as well as other WiFi devices that exceed TARGET_RSSI
# by default, set to False to reduce false positives
GRAB_APS = False

# TARGET_RSSI determines the strength a WiFi device needs to be seen to record into .csv and have a picture taken
# if MOTION_DETECTION is False. Lowering this value can result in more false positives
TARGET_RSSI = -37

# The following parameters are for logging into the monitoring Kismet server. Local machine Kismet server can be set
# with value 'localhost' or '127.0.0.1'
USERNAME = 'kismet'
PASSWORD = 'kismet'
IP = '192.168.1.167'

# COUNT designates how many photos are taken each time the application is triggered to take photos, with a .5 second
# inbetween each photo
COUNT = 3

# CAMERA designates which camera to use for the application. Observed behavior for a Surface Pro is below:
# 0: Front facing camera, if it exists
# 1: Back facing camera, if it exists
# 2: Additional cameras
# With this in mind, if a device, like a Raspberry Pi, does not have an onboard camera, the first camera added will be 0
CAMERA = 0

# START designates whether or not the application is actually 'capturing' meaning that it can be triggered to take
# photos and make API calls by either motion or RSSI detection. If set to True, application will start as soon as
# launched
START = True

params = {
    'fields': [
        "kismet.device.base.signal/kismet.common.signal.last_signal",
        "kismet.device.base.macaddr",
        "kismet.device.base.type",
        "kismet.device.base.last_time"
    ]
}

static_back = None
motion_list = [None, None]
cap = cv2.VideoCapture(CAMERA)
last_api_call = 0

app = Flask(__name__)
app.config['SECRET_KEY'] = 'isdbnfgsijdgnkljang9248921ubpfjna0u32nf30qip'
Bootstrap(app)

def api_call():
    if GRAB_APS:
        aps = ''
    else:
        aps = 'Wi-Fi AP'
    results = requests.post(
        url=f"http://{USERNAME}:{PASSWORD}@{IP}:2501/devices/views/phy-IEEE802.11/devices.json",
        json=params).json()
    mac_list = []
    rssi_above_target = False
    for item in results:
        rssi = int(item['kismet.common.signal.last_signal'])
        last_seen_time = item["kismet.device.base.last_time"]
        if rssi >= TARGET_RSSI \
                and rssi != 0 \
                and item['kismet.device.base.type'] != aps \
                and time.time() - last_seen_time <= 30:
            rssi_above_target = True
            mac = item['kismet.device.base.macaddr'].replace(':', '')
            device_type = item['kismet.device.base.type']
            mac_list.append([mac, device_type, rssi])
    if rssi_above_target:
        name = f'{dt.now().strftime("%Y%m%d_%H%M%S")}'
        for num in range(0, COUNT):
            result, image = cap.read()
            cv2.imwrite(f'images/{name}_{num}.png', image)
            time.sleep(.5)
        with open(f'Possible MAC List_{dt.now().strftime("%Y%m%d")}.csv', mode="a", encoding='utf8') as mac_deck:
            writer = csv.writer(mac_deck)
            for item in mac_list:
                item.append(name)
                writer.writerow(item)

def gen_frames():
    global static_back, last_api_call
    while True:
        check, frame = cap.read()
        if START:
            if MOTION_DETECTION:
                motion = 0
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (21, 21), 0)
                if static_back is None:
                    static_back = gray
                    continue
                diff_frame = cv2.absdiff(static_back, gray)
                thresh_frame = cv2.threshold(diff_frame, 30, 255, cv2.THRESH_BINARY)[1]
                thresh_frame = cv2.dilate(thresh_frame, None, iterations=2)
                cnts, _ = cv2.findContours(thresh_frame.copy(),
                                           cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for contour in cnts:
                    if cv2.contourArea(contour) < 15000:
                        continue
                    motion = 1
                    (x, y, w, h) = cv2.boundingRect(contour)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                    if time.time() > 5 + last_api_call:
                        last_api_call = time.time()
                        api_call()
            else:
                if time.time() > 5 + last_api_call:
                    last_api_call = time.time()
                    api_call()
        if not check:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/', methods=['POST', 'GET'])
def home():
    global USERNAME, PASSWORD
    form = CreateKismetForm()
    form.username.render_kw = {'placeholder': USERNAME}
    form.password.render_kw = {'placeholder': PASSWORD}
    if form.validate_on_submit():
        USERNAME = form.username.data
        PASSWORD = form.password.data
        return redirect(url_for('home'))
    return render_template('index.html',
                           motion=MOTION_DETECTION,
                           aps=GRAB_APS,
                           rssi=TARGET_RSSI,
                           form=form,
                           start=START)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/set_motion_detect')
def set_motion_detect():
    global MOTION_DETECTION
    if MOTION_DETECTION:
        MOTION_DETECTION = False
    else:
        MOTION_DETECTION = True
    return redirect(url_for('home', motion=MOTION_DETECTION))

@app.route('/set_grab_aps')
def set_grab_aps():
    global GRAB_APS
    if GRAB_APS:
        GRAB_APS = False
    else:
        GRAB_APS = True
    return redirect(url_for('home', aps=GRAB_APS))

@app.route('/set_rssi', methods=['POST'])
def set_rssi():
    global TARGET_RSSI
    rssi = request.form['range']
    TARGET_RSSI = int(rssi)
    return redirect(url_for('home', rssi=TARGET_RSSI))

@app.route('/start_capture')
def start_capture():
    global START
    if START:
        START = False
    else:
        START = True
    return redirect(url_for('home', start=START))


if __name__ == "__main__":
    app.run(host='0.0.0.0')

