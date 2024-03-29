import cv2
import requests
import time
from datetime import datetime as dt
import csv

class Camera:
    def __init__(self):
        self.motion_detection = False
        self.grab_aps = False
        self.rssi = -72
        self.username = "kismet"
        self.password = "kismet"
        self.IP = "localhost"
        self.count = 3
        self.camera = 0
        self.start_capture = False
        self.stream = True
        self.sensitivity = 5000
        self.rotation = 0
        self.image_dir = "images"
        self.resolutions = ""
        self.width = 640
        self.height = 480
        self.static_back = None
        self.last_api_call = 0
        self.cap = cv2.VideoCapture(self.camera)
        self.check = ""
        self.frame = []
        self.params = {
            'fields': [
                "kismet.device.base.signal/kismet.common.signal.last_signal",
                "kismet.device.base.macaddr",
                "kismet.device.base.type",
                "kismet.device.base.last_time"
            ]
        }
        self.source_params = {
            'fields': [
                'kismet.datasource.channels',
                'kismet.datasource.uuid',
                "kismet.datasource.interface",
                "kismet.datasource.hopping",
                "kismet.datasource.channel",
                "kismet.datasource.hop_channels"
            ]
        }
        self.one_six_eleven_params = {
            'channels': ['1', '6', '11'],
            'hoprate': 5
        }
        self.two_full_params = {
            'channels': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14'],
            'hoprate': 5
        }
        self.five_full_params = {
            'channels': ['36', '40', '44', '48', '52', '56', '60', '64', '100', '104', '108', '112', '116', '120',
                         '124',
                         '128', '132', '136', '140', '144', '149', '153', '157', '161', '165'],
            'hoprate': 5
        }
        self.ignore_list = []
        self.seen_list = []
        self.interfaces = []
        self.url = f"http://{self.username}:{self.password}@{self.IP}:2501/"

    def get_interfaces(self):
        results = requests.post(
            url=f"{self.url}datasource/all_sources.json",
            json=self.source_params).json()

        self.interfaces = results

    def survey_channels(self, uuid, span):
        if span == "all":
            for item in self.interfaces:
                if item['kismet.datasource.uuid'] == uuid:
                    params = {
                        'channels': item['kismet.datasource.channels'],
                        'hoprate': 5
                    }
                    requests.post(
                        url=f"{self.url}datasource/by-uuid/{uuid}/set_channel.cmd",
                        json=params)
        else:
            requests.post(
                url=f"{self.url}datasource/by-uuid/{uuid}/set_channel.cmd",
                json=span)

    def lock_channel(self, uuid, channel):
        requests.post(
            url=f"{self.url}datasource/by-uuid/{uuid}/set_channel.cmd",
            json={'channel': channel})

    def retrieve_ignore_list(self):
        temp_ignore_list = []
        with open('resources/ignore_list.csv', mode='r') as file:
            for item in file:
                temp_ignore_list.append(item.replace('\n', ''))
        self.ignore_list = temp_ignore_list

    def check_resolution(self):
        working_resolutions = {}
        with open('resources/supported_resolutions.csv', mode='r') as file:
            cap = cv2.VideoCapture(self.camera)
            for item in file:
                row = item.strip().split()
                width = int(row[0])
                height = int(row[2])
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                working_resolutions[str(width) + " x " + str(height)] = "OK"
        self.resolutions = working_resolutions

    def update_frames(self):
        self.check, self.frame = self.cap.read()

    def api_call(self):
        if self.grab_aps:
            aps = ''
        else:
            aps = 'Wi-Fi AP'
        results = requests.post(
            url=f"{self.url}devices/views/phy-IEEE802.11/devices.json",
            json=self.params).json()
        mac_list = []
        rssi_above_target = False
        for item in results:
            rssi = int(item['kismet.common.signal.last_signal'])
            last_seen_time = item["kismet.device.base.last_time"]
            if rssi >= self.rssi \
                    and rssi != 0 \
                    and item['kismet.device.base.type'] != aps \
                    and time.time() - last_seen_time <= 30 \
                    and item["kismet.device.base.macaddr"] not in self.ignore_list:
                rssi_above_target = True
                mac = item['kismet.device.base.macaddr']
                device_type = item['kismet.device.base.type']
                mac_list.append([mac, device_type, rssi])
        if rssi_above_target:
            name = f'{dt.now().strftime("%Y%m%d_%H%M%S")}'
            for num in range(0, self.count):
                result, image = self.cap.read()
                image = cv2.resize(image, (self.width, self.height))
                if self.rotation == 0:
                    cv2.imwrite(f'{self.image_dir}/{name}_{num}.png', image)
                elif self.rotation == 90:
                    cv2.imwrite(f'{self.image_dir}/{name}_{num}.png', cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE))
                elif self.rotation == 180:
                    cv2.imwrite(f'{self.image_dir}/{name}_{num}.png', cv2.rotate(image, cv2.ROTATE_180))
                elif self.rotation == 270:
                    cv2.imwrite(f'{self.image_dir}/{name}_{num}.png',
                                cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE))
                time.sleep(.25)
            with open(f'{self.image_dir}/MAC List_{dt.now().strftime("%Y%m%d")}.csv', mode="a",
                      encoding='utf8') as mac_deck:
                writer = csv.writer(mac_deck)
                for item in mac_list:
                    item.append(name)
                    writer.writerow(item)
                    if item[0] not in self.seen_list:
                        self.seen_list.append(item[0])
