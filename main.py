from flask import Flask, render_template, Response, redirect, url_for, request, send_file
from flask_paginate import Pagination
from flask_bootstrap import Bootstrap
from forms import CreateKismetForm
from datetime import datetime as dt
import zipfile
import time
import cv2
import os
import json
from camera import Camera

camera = Camera()
camera.check_resolution()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'isdbnfgsijdgnkljang9248921ubpfjna0u32nf30qip'
app.config['IMAGES'] = camera.image_dir
Bootstrap(app)

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
                    camera.last_api_call = time.time()
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

@app.route('/downloads/delete/<path:filename>', methods=['GET'])
def delete(filename):
    path = f'{camera.image_dir}/{filename}'
    os.remove(path)
    print("Working")
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
    # camera.cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera.width)
    # camera.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera.height)
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
