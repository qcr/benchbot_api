import requests
import cv2
import base64
import numpy as np

class BenchBot:
    def __init__(self, uri='http://172.17.0.1:8081/'):
        self.uri = uri
    
    def get(self, route=''):
        return requests.get(self.uri + route).json()

    def send(self, route='', data={}):
        return requests.post(self.uri + route, None, data).json()
        
    def getImage(self, route='image'):
        resp = self.get('image')
        buf = np.fromstring(resp['image'].decode('base64'), np.uint8)
        return cv2.imdecode(buf, cv2.IMREAD_COLOR)

    def isDone(self):
        resp = self.get('is_done')
        return resp['result']
