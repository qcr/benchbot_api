import base64
import cv2
import jsonpickle
import jsonpickle.ext.numpy as jet
import numpy as np

jet.register_handlers()


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
