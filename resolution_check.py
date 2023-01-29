import cv2
import constants

working_resolutions = {}

def check_resolution():
    with open('resources/supported_resolutions.csv', mode='r') as file:
        cap = cv2.VideoCapture(constants.CAMERA)
        for item in file:
            row = item.strip().split()
            width = int(row[0])
            height = int(row[2])
            print(f'{width} x {height}')
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            working_resolutions[str(width) + " x " + str(height)] = "OK"
    return working_resolutions







