import cv2

def check_resolution(camera):
    working_resolutions = {}
    with open('resources/supported_resolutions.csv', mode='r') as file:
        cap = cv2.VideoCapture(camera)
        for item in file:
            row = item.strip().split()
            width = int(row[0])
            height = int(row[2])
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            working_resolutions[str(width) + " x " + str(height)] = "OK"
    return working_resolutions







