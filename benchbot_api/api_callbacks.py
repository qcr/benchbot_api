import base64
import cv2
import numpy as np


def decode_ros_image(data):
    return cv2.imdecode(
        np.fromstring(base64.b64decode(data['data']), np.uint8),
        cv2.IMREAD_COLOR)
