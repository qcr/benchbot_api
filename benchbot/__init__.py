#!/usr/bin/env python

from __future__ import print_function
import requests
import cv2
import base64
import numpy as np
import pickle
from grid_map import GridMap

class SupervisorConnectionError(Exception):
  def __init__(self, message=None):
    Exception.__init__(self, message if message else 'Unable to communicate with supervisor')

class MalformedDataError(Exception):
  def __init__(self, message=None):
    Exception.__init__(self, message if message else 'Malformed data communicated to supervisor')

class BenchBot(object):
    def __init__(self, uri='http://172.17.0.1:8081/'):
      """Benchbot constructor.
      
      Args:
        uri (string, optional): The uri of the supervisor with which benchbot will communicate.
      """
      self.uri = uri
      self.data_store = {}

    def __enter__(self):
      """entry method invoked using `with` that initialises datastore. 
          
      Returns:
        BenchBot: a benchbot instance
      """
      self.data_store = {}
      return self

    def __exit__(self, exc_type, exc_val, exc_tb):
      """exit method invoked when leaving scope of `with`. Transmits datastore to supervisor.
      """
      encoded = str(base64.b64encode(pickle.dumps(self.data_store)))
      
      try:
        self.send('data-store', {'pickle': encoded})
      except Exception as e:
        print(str(e))
        print('Failed transmitting datastore to supervisor')

    def get(self, route=''):
      """Base level method for retrieving information from the robot. 
      
      All communication between benchbot and the robot relies on a running supervisor.

      Args:
        route (string): The route from which benchbot should retrieve data.
          
      Returns:
        dict: A dictionary containing the data retrieved from `route`

      Raises:
        SupervisorConnectionError: If benchbot is unable to communicate with a supervisor
      """
      try:
        resp = requests.get(self.uri + route)

        if resp.status_code == 404:
          raise SupervisorConnectionError()

        return resp.json()

      except:
        raise SupervisorConnectionError('There was an issue with communicating with the supervisor')

    def send(self, route='', data={}):
      """Base level method for sending information to the robot. 
      
      All communication between benchbot and the robot relies on a running supervisor.

      Args:
        route (string): The route from which benchbot should retrieve data.
          
      Returns:
        dict: A dictionary containing a result flag (0 for success), as well as a message on failure.

      Raises:
        SupervisorConnectionError: If benchbot is unable to communicate with a supervisor
        BadDataError: If the transmitted data is in a bad format, or is missing required data.
      """
      try:
        resp = requests.post(self.uri + route, json=data)
        
        if resp.status_code == 500:
          raise MalformedDataError()
        
        if resp.status_code == 404:
          raise SupervisorConnectionError()

        if resp.status_code != 200:
          raise SupervisorConnectionError('There was an issue with communicating with the supervisor')

        return resp.json()

      except requests.ConnectionError:
        raise SupervisorConnectionError()
        
        
    def store(self, key, value):
      """Stores information that can be downloaded after a run. 
      
      Args:
        key (string): A unique identifier used to retrieve `value`.
        value (obj): The value being stored. Must be able to be pickled.
      """
      self.data_store[key] = value

    def getImage(self, route='image'):
      """Convenience wrapper around BenchBot.get that converts the 
      returned value to a numpy array for use with OpenCV etc.
      
      Args:
        route (string, optional): The route from which to retrieve the image. Defaults to `image`.
          
      Returns:
        numpy.array: The retrieved image

      Raises:
        SupervisorConnectionError: If benchbot is unable to communicate with a supervisor
      """
      resp = self.get(route)
      buf = np.fromstring(base64.b64decode(resp['image']), np.uint8)
      return cv2.imdecode(buf, cv2.IMREAD_COLOR)

    def getGridMap(self, route='map'):
      """Convenience wrapper around BenchBot.get that converts the 
      returned value to a 2D occupancy grid that can be used for navigation.
      
      Args:
        route (string, optional): The route from which to retrieve the map. Defaults to `image`.
          
      Returns:
        GridMap: The retrieved occupancy grid map.

      Raises:
        SupervisorConnectionError: If benchbot is unable to communicate with a supervisor
      """
      resp = self.get(route)
      return GridMap(**resp)

    
    def complete(self, task_id, data=None):
      """Convenience wrapper around BenchBot.send that is used to indicate the completion of a task.
      
      Args:
        task_id (string): The task id identifying the task which has been completed.
        data (dict, optional): Additional data needed for completing the task
      Returns:
        dict: A dictionary containing a result flag (0 for success), as well as a message on failure.

      Raises:
        SupervisorConnectionError: If benchbot is unable to communicate with a supervisor
      """
      data = data if data else {}

      if 'id' in data:
        raise Exception('data should not contain key: id')

      data['id'] = task_id
      return self.send('complete', data)

    def isDone(self):
      """Convenience wrapper around BenchBot.get that checks whether all tasks have been completed.
                
      Returns:
        bool: True if completed, False otherwise.

      Raises:
        SupervisorConnectionError: If benchbot is unable to communicate with a supervisor
      """
      resp = self.get('is_done')
      return resp['result']

if __name__ == '__main__':
  with BenchBot() as benchbot:
    benchbot.store('number', 4)

    img = benchbot.getImage()
    benchbot.store('image', img)

    benchbot.complete('goal_2-a', {'marker': 'april_23', 'detected': {'bottle': 2, 'car': 1}})

