import base64
import cv2
import numpy as np

ENCODING_TO_CONVERSION = {'bgr8': cv2.COLOR_BGR2RGB}


def convert_to_rgb(data):
    cvt = ENCODING_TO_CONVERSION.get(data['encoding'], None)
    return data['data'] if cvt is None else cv2.cvtColor(data['data'], cvt)


def decode_color_image(data):
    if data['encoding'] == 'bgr8':
        return cv2.cvtColor(
            cv2.imdecode(
                np.fromstring(base64.b64decode(data['data']), np.uint8),
                cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
    elif data['encoding'] == 'rgb8':
        return cv2.imdecode(
            np.fromstring(base64.b64decode(data['data']), np.uint8),
            cv2.IMREAD_COLOR)
    else:
        raise ValueError(
            "decode_ros_image: received image data with unsupported encoding: %s"
            % data['encoding'])


def decode_jsonpickle(data):
    return jsonpickle.decode(data)
