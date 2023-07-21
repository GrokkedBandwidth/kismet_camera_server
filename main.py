from flask import Flask, render_template, Response, redirect, url_for, request, send_file
from flask_paginate import Pagination
from flask_bootstrap import Bootstrap
from forms import CreateKismetForm
from datetime import datetime as dt
import zipfile
import time
import cv2
import os
from camera import Camera

# Adjust constants inside of constants.py
# MOTION_DETECTION = constants.MOTION_DETECTION
# GRAB_APS = constants.GRAB_APS
# TARGET_RSSI = constants.TARGET_RSSI
# USERNAME = constants.USERNAME
# PASSWORD = constants.PASSWORD
# IP = constants.IP
# COUNT = constants.COUNT
# CAMERA = constants.CAMERA
# START = constants.START
# STREAM = constants.STREAM
# SENSITIVITY = constants.SENSITIVITY
# ROTATION = constants.ROTATION
# IMAGE_DIRECTORY = constants.IMAGE_DIRECTORY

# WIDTH = 640
# HEIGHT = 480

params = {
    'fields': [
        "kismet.device.base.signal/kismet.common.signal.last_signal",
        "kismet.device.base.macaddr",
        "kismet.device.base.type",
        "kismet.device.base.last_time"
    ]
}

camera = Camera()
camera.check_resolution()
# motion_list = [None, None]
# cap = cv2.VideoCapture(camera.camera)
# last_api_call = 0

app = Flask(__name__)
app.config['SECRET_KEY'] = 'isdbnfgsijdgnkljang9248921ubpfjna0u32nf30qip'
app.config['IMAGES'] = camera.image_dir
Bootstrap(app)

# def api_call():
#     if GRAB_APS:
#         aps = ''
#     else:
#         aps = 'Wi-Fi AP'
#     results = requests.post(
#         url=f"http://{USERNAME}:{PASSWORD}@{IP}:2501/devices/views/phy-IEEE802.11/devices.json",
#         json=params).json()
#     mac_list = []
#     rssi_above_target = False
#     for item in results:
#         rssi = int(item['kismet.common.signal.last_signal'])
#         last_seen_time = item["kismet.device.base.last_time"]
#         if rssi >= TARGET_RSSI \
#                 and rssi != 0 \
#                 and item['kismet.device.base.type'] != aps \
#                 and time.time() - last_seen_time <= 30:
#             rssi_above_target = True
#             mac = item['kismet.device.base.macaddr'].replace(':', '')
#             device_type = item['kismet.device.base.type']
#             mac_list.append([mac, device_type, rssi])
#     if rssi_above_target:
#         name = f'{dt.now().strftime("%Y%m%d_%H%M%S")}'
#         for num in range(0, COUNT):
#             result, image = cap.read()
#             image = cv2.resize(image, (WIDTH, HEIGHT))
#             if ROTATION == 0:
#                 cv2.imwrite(f'{IMAGE_DIRECTORY}/{name}_{num}.png', image)
#             elif ROTATION == 90:
#                 cv2.imwrite(f'{IMAGE_DIRECTORY}/{name}_{num}.png', cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE))
#             elif ROTATION == 180:
#                 cv2.imwrite(f'{IMAGE_DIRECTORY}/{name}_{num}.png', cv2.rotate(image, cv2.ROTATE_180))
#             elif ROTATION == 270:
#                 cv2.imwrite(f'{IMAGE_DIRECTORY}/{name}_{num}.png', cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE))
#             time.sleep(.25)
#         with open(f'{IMAGE_DIRECTORY}/MAC List_{dt.now().strftime("%Y%m%d")}.csv', mode="a", encoding='utf8') as mac_deck:
#             writer = csv.writer(mac_deck)
#             for item in mac_list:
#                 item.append(name)
#                 writer.writerow(item)

def gen_frames():
    while True:
        check, frame = camera.cap.read()
        if camera.start_capture:
            if camera.motion_detection:
                motion = 0
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (21, 21), 0)
                if camera.static_back is None:
                    camera.static_back = gray
                    continue
                diff_frame = cv2.absdiff(camera.static_back, gray)
                thresh_frame = cv2.threshold(diff_frame, 30, 255, cv2.THRESH_BINARY)[1]
                thresh_frame = cv2.dilate(thresh_frame, None, iterations=2)
                cnts, _ = cv2.findContours(thresh_frame.copy(),
                                           cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for contour in cnts:
                    if cv2.contourArea(contour) < camera.sensitivity:
                        continue
                    motion = 1
                    (x, y, w, h) = cv2.boundingRect(contour)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                    if time.time() > 2.5 + camera.last_api_call:
                        camera.last_api_call = time.time()
                        camera.api_call()
            else:
                if time.time() > 2.5 + camera.last_api_call:
                    last_api_call = time.time()
                    camera.api_call()
        if not check:
            break
        else:
            if camera.rotation == 0:
                ret, buffer = cv2.imencode('.jpg', frame)
            elif camera.rotation == 90:
                ret, buffer = cv2.imencode('.jpg', cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE))
            elif camera.rotation == 180:
                ret, buffer = cv2.imencode('.jpg', cv2.rotate(frame, cv2.ROTATE_180))
            elif camera.rotation == 270:
                ret, buffer = cv2.imencode('.jpg', cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE))
            frame = buffer.tobytes()
            if camera.stream:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                pass

@app.route('/', methods=['POST', 'GET'])
def home():
    resolution = f'{camera.width} x {camera.height}'
    return render_template('index.html',
                           motion=camera.motion_detection,
                           aps=camera.grab_aps,
                           rssi=camera.rssi,
                           start=camera.start_capture,
                           stream=camera.stream,
                           rotation=camera.rotation,
                           resolutions=camera.resolutions,
                           resolution=resolution,
                           camera_object=camera)

@app.route('/options', methods=['GET', 'POST'])
def options():
    form = CreateKismetForm()
    form.username.render_kw = {'placeholder': f'Current Username: {camera.username}'}
    form.password.render_kw = {'placeholder': f'Current Password: {camera.password}'}
    if form.validate_on_submit():
        camera.username = form.username.data
        camera.password = form.password.data
        return redirect(url_for('options'))
    return render_template('options.html',
                           count=camera.count,
                           form=form,
                           camera=camera.camera,
                           rssi=camera.rssi,
                           motion=camera.motion_detection,
                           aps=camera.grab_aps,
                           sensitivity=camera.sensitivity)

@app.route('/downloads')
def downloads():
    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page
    filelist = []
    for file in os.listdir(camera.image_dir):
        filelist.append(file)
    filelist.sort()
    filelist.reverse()
    items = filelist[offset:offset+per_page]
    pagination = Pagination(page=page, per_page=per_page, offset=offset, total=len(filelist),
                            record_name='filelist')
    return render_template('download.html',
                           filelist=items,
                           pagination=pagination)

@app.route('/downloads/<path:filename>', methods=['GET', 'POST'])
def download_file(filename):
    path = f'{camera.image_dir}/{filename}'
    return send_file(path_or_file=path, as_attachment=True)

@app.route('/downloads/preview/<path:filename>', methods=['GET', 'POST'])
def preview(filename):
    path = f'{camera.image_dir}/{filename}'
    return send_file(path_or_file=path, mimetype='image/jpeg')

@app.route('/downloads/delete/<path:filename>', methods=['GET', 'POST'])
def delete(filename):
    path = f'{camera.image_dir}/{filename}'
    os.remove(path)
    return redirect(url_for('downloads'))

@app.route('/downloads/download_all', methods=['GET', 'POST'])
def download_all():
    filename = f'Extract_{dt.now().strftime("%Y%m%d_%H%M%S")}.zip'
    with zipfile.ZipFile(filename, mode='w') as archive:
        for file in os.listdir(camera.image_dir):
            archive.write(f'{camera.image_dir}/{file}')
    return send_file(path_or_file=filename, as_attachment=True)

@app.route('/downloads/delete_all', methods=['GET', 'POST'])
def delete_all():
    for file in os.listdir(camera.image_dir):
        os.remove(f'{camera.image_dir}/{file}')
    return redirect(url_for('downloads'))

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/set_motion_detect')
def set_motion_detect():
    camera.motion_detection = not camera.motion_detection
    return redirect(url_for('options', motion=camera.motion_detection))

@app.route('/set_grab_aps')
def set_grab_aps():
    camera.grab_aps = not camera.grab_aps
    return redirect(url_for('options', aps=camera.grab_aps))

@app.route('/set_rssi', methods=['POST'])
def set_rssi():
    rssi = request.form['text']
    camera.rssi = int(rssi)
    return redirect(url_for('options', rssi=camera.rssi))

@app.route('/set_sensitivity', methods=['POST'])
def set_sensitivity():
    camera.sensitivity = int(request.form['sensitivity'])
    return redirect(url_for('options', sensitivity=camera.sensitivity))

@app.route('/set_resolution/<resolution>', methods=['GET'])
def set_resolution(resolution):
    camera.width = int(resolution.split()[0].split('.')[0])
    camera.height = int(resolution.split()[2].split('.')[0])
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    return redirect(url_for('home'))

@app.route('/start_capture')
def start_capture():
    camera.start_capture = not camera.start_capture
    return redirect(url_for('home', start=camera.start_capture))

@app.route('/start_stream')
def start_stream():
    camera.stream = not camera.stream
    return redirect(url_for('home', start=camera.stream))

@app.route('/set_count', methods=['POST'])
def set_count():
    camera.count = int(request.form['count'])
    return redirect(url_for('options', count=camera.count))

@app.route('/set_camera', methods=['POST', 'GET'])
def set_camera():
    cv2.destroyAllWindows()
    camera.camera = int(request.form['camera'])
    print(camera.camera)
    camera.check_resolution()
    camera.cap = cv2.VideoCapture(camera.camera)
    camera.width = 640
    camera.height = 480
    return redirect(url_for('options', camera=camera.camera))

@app.route('/rotate', methods=['POST', 'GET'])
def rotate():
    if camera.rotation < 270:
        camera.rotation += 90
    else:
        camera.rotation = 0
    return redirect(url_for('home', rotation=camera.rotation))

@app.route('/manual', methods=['GET'])
def manual_photo():
    result, image = camera.cap.read()
    image = cv2.resize(image, (camera.width, camera.height))
    if camera.rotation == 0:
        cv2.imwrite(f'{camera.image_dir}/{dt.now().strftime("%Y%m%d_%H%M%S")}_ManualPhoto.png', image)
    elif camera.rotation == 90:
        cv2.imwrite(f'{camera.image_dir}/{dt.now().strftime("%Y%m%d_%H%M%S")}_ManualPhoto.png',
                    cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE))
    elif camera.rotation == 180:
        cv2.imwrite(f'{camera.image_dir}/{dt.now().strftime("%Y%m%d_%H%M%S")}_ManualPhoto.png',
                    cv2.rotate(image, cv2.ROTATE_180))
    elif camera.rotation == 270:
        cv2.imwrite(f'{camera.image_dir}/{dt.now().strftime("%Y%m%d_%H%M%S")}_ManualPhoto.png',
                    cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE))
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(host='0.0.0.0')
