from flask import Flask, render_template, Response, redirect, url_for, request, send_file
from flask_bootstrap import Bootstrap
from forms import CreateKismetForm
from datetime import datetime as dt
import zipfile
import requests
import time
import csv
import cv2
import os
import resolution_check
import constants

# Adjust constants inside of constants.py
MOTION_DETECTION = constants.MOTION_DETECTION
GRAB_APS = constants.GRAB_APS
TARGET_RSSI = constants.TARGET_RSSI
USERNAME = constants.USERNAME
PASSWORD = constants.PASSWORD
IP = constants.IP
COUNT = constants.COUNT
CAMERA = constants.CAMERA
START = constants.START
STREAM = constants.STREAM
SENSITIVITY = constants.SENSITIVITY
ROTATION = constants.ROTATION
IMAGE_DIRECTORY = constants.IMAGE_DIRECTORY

WIDTH = 640
HEIGHT = 480

params = {
    'fields': [
        "kismet.device.base.signal/kismet.common.signal.last_signal",
        "kismet.device.base.macaddr",
        "kismet.device.base.type",
        "kismet.device.base.last_time"
    ]
}
working_resolutions = resolution_check.check_resolution()
print(working_resolutions)

static_back = None
motion_list = [None, None]
cap = cv2.VideoCapture(CAMERA)
last_api_call = 0

app = Flask(__name__)
app.config['SECRET_KEY'] = 'isdbnfgsijdgnkljang9248921ubpfjna0u32nf30qip'
app.config['IMAGES'] = IMAGE_DIRECTORY
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
            image = cv2.resize(image, (WIDTH, HEIGHT))
            if ROTATION == 0:
                cv2.imwrite(f'{IMAGE_DIRECTORY}/{name}_{num}.png', image)
            elif ROTATION == 90:
                cv2.imwrite(f'{IMAGE_DIRECTORY}/{name}_{num}.png', cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE))
            elif ROTATION == 180:
                cv2.imwrite(f'{IMAGE_DIRECTORY}/{name}_{num}.png', cv2.rotate(image, cv2.ROTATE_180))
            elif ROTATION == 270:
                cv2.imwrite(f'{IMAGE_DIRECTORY}/{name}_{num}.png', cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE))
            time.sleep(.25)
        with open(f'{IMAGE_DIRECTORY}/MAC List_{dt.now().strftime("%Y%m%d")}.csv', mode="a", encoding='utf8') as mac_deck:
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
                    if cv2.contourArea(contour) < SENSITIVITY:
                        continue
                    motion = 1
                    (x, y, w, h) = cv2.boundingRect(contour)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                    if time.time() > 2.5 + last_api_call:
                        last_api_call = time.time()
                        api_call()
            else:
                if time.time() > 2.5 + last_api_call:
                    last_api_call = time.time()
                    api_call()
        if not check:
            break
        else:
            if ROTATION == 0:
                ret, buffer = cv2.imencode('.jpg', frame)
            elif ROTATION == 90:
                ret, buffer = cv2.imencode('.jpg', cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE))
            elif ROTATION == 180:
                ret, buffer = cv2.imencode('.jpg', cv2.rotate(frame, cv2.ROTATE_180))
            elif ROTATION == 270:
                ret, buffer = cv2.imencode('.jpg', cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE))
            frame = buffer.tobytes()
            if STREAM:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                pass

@app.route('/', methods=['POST', 'GET'])
def home():
    resolution = f'{WIDTH} x {HEIGHT}'
    return render_template('index.html',
                           motion=MOTION_DETECTION,
                           aps=GRAB_APS,
                           rssi=TARGET_RSSI,
                           start=START,
                           stream=STREAM,
                           rotation=ROTATION,
                           resolutions=working_resolutions,
                           resolution=resolution)

@app.route('/options', methods=['GET', 'POST'])
def options():
    global USERNAME, PASSWORD
    form = CreateKismetForm()
    form.username.render_kw = {'placeholder': f'Current Username: {USERNAME}'}
    form.password.render_kw = {'placeholder': f'Current Password: {PASSWORD}'}
    if form.validate_on_submit():
        USERNAME = form.username.data
        PASSWORD = form.password.data
        return redirect(url_for('options'))
    return render_template('options.html',
                           count=COUNT,
                           form=form,
                           camera=CAMERA,
                           rssi=TARGET_RSSI,
                           motion=MOTION_DETECTION,
                           aps=GRAB_APS,
                           sensitivity=SENSITIVITY,)

@app.route('/downloads')
def downloads():
    filelist = []
    for file in os.listdir(IMAGE_DIRECTORY):
        filelist.append(file)
    return render_template('download.html', filelist=filelist)

@app.route('/downloads/<path:filename>', methods=['GET', 'POST'])
def download_file(filename):
    path = f'{IMAGE_DIRECTORY}/{filename}'
    return send_file(path_or_file=path, as_attachment=True)

@app.route('/downloads/preview/<path:filename>', methods=['GET', 'POST'])
def preview(filename):
    path = f'{IMAGE_DIRECTORY}/{filename}'
    return send_file(path_or_file=path, mimetype='image/jpeg')

@app.route('/downloads/delete/<path:filename>', methods=['GET', 'POST'])
def delete(filename):
    path = f'{IMAGE_DIRECTORY}/{filename}'
    os.remove(path)
    return redirect(url_for('downloads'))

@app.route('/downloads/download_all', methods=['GET', 'POST'])
def download_all():
    filename = f'Extract_{dt.now().strftime("%Y%m%d_%H%M%S")}.zip'
    with zipfile.ZipFile(filename, mode='w') as archive:
        for file in os.listdir(IMAGE_DIRECTORY):
            archive.write(f'{IMAGE_DIRECTORY}/{file}')
    return send_file(path_or_file=filename, as_attachment=True)

@app.route('/downloads/delete_all', methods=['GET', 'POST'])
def delete_all():
    for file in os.listdir(IMAGE_DIRECTORY):
        os.remove(f'{IMAGE_DIRECTORY}/{file}')
    return redirect(url_for('downloads'))

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
    return redirect(url_for('options', motion=MOTION_DETECTION))

@app.route('/set_grab_aps')
def set_grab_aps():
    global GRAB_APS
    if GRAB_APS:
        GRAB_APS = False
    else:
        GRAB_APS = True
    return redirect(url_for('options', aps=GRAB_APS))

@app.route('/set_rssi', methods=['POST'])
def set_rssi():
    global TARGET_RSSI
    rssi = request.form['text']
    TARGET_RSSI = int(rssi)
    return redirect(url_for('options', rssi=TARGET_RSSI))

@app.route('/set_sensitivity', methods=['POST'])
def set_sensitivity():
    global SENSITIVITY
    SENSITIVITY = int(request.form['sensitivity'])
    return redirect(url_for('options', sensitivity=SENSITIVITY))

@app.route('/set_resolution/<resolution>', methods=['GET'])
def set_resolution(resolution):
    global WIDTH, HEIGHT
    WIDTH = int(resolution.split()[0].split('.')[0])
    HEIGHT = int(resolution.split()[2].split('.')[0])
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    return redirect(url_for('home'))

@app.route('/start_capture')
def start_capture():
    global START
    if START:
        START = False
    else:
        START = True
    return redirect(url_for('home', start=START))

@app.route('/start_stream')
def start_stream():
    global STREAM
    if STREAM:
        STREAM = False
    else:
        STREAM = True
    return redirect(url_for('home', start=STREAM))

@app.route('/set_count', methods=['POST'])
def set_count():
    global COUNT
    COUNT = int(request.form['count'])
    return redirect(url_for('options', count=COUNT))

@app.route('/set_camera', methods=['POST'])
def set_camera():
    global CAMERA
    CAMERA = request.form['camera']
    return redirect(url_for('options', camera=CAMERA))

@app.route('/rotate', methods=['POST', 'GET'])
def rotate():
    global ROTATION
    if ROTATION < 270:
        ROTATION += 90
    else:
        ROTATION = 0
    return redirect(url_for('home', rotation=ROTATION))

@app.route('/manual', methods=['GET'])
def manual_photo():
    result, image = cap.read()
    image = cv2.resize(image, (WIDTH, HEIGHT))
    if ROTATION == 0:
        cv2.imwrite(f'{IMAGE_DIRECTORY}/{dt.now().strftime("%Y%m%d%H%M%S")}_ManualPhoto.png', image)
    elif ROTATION == 90:
        cv2.imwrite(f'{IMAGE_DIRECTORY}/{dt.now().strftime("%Y%m%d%H%M%S")}_ManualPhoto.png',
                    cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE))
    elif ROTATION == 180:
        cv2.imwrite(f'{IMAGE_DIRECTORY}/{dt.now().strftime("%Y%m%d%H%M%S")}_ManualPhoto.png',
                    cv2.rotate(image, cv2.ROTATE_180))
    elif ROTATION == 270:
        cv2.imwrite(f'{IMAGE_DIRECTORY}/{dt.now().strftime("%Y%m%d%H%M%S")}_ManualPhoto.png',
                    cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE))
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(host='0.0.0.0')

