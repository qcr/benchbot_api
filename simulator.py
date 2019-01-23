#!/usr/bin/env python
from __future__ import print_function

from flask import Flask, jsonify, request, abort
import os
import cv2
import base64
import sys
import gevent
import copy
from gevent.pywsgi import WSGIServer
from gevent.event import Event

class SupervisorException(Exception):
    pass

class UnknownRouteError(SupervisorException):
    def __init__(self, route):
        SupervisorException.__init__(self)
        self.route = route

    def __str__(self):
        return 'Unknown route: ' + self.route

class UnknownCallbackError(SupervisorException):
    def __init__(self, route, method):
        SupervisorException.__init__(self)
        self.route = route
        self.method = method

    def __str__(self):
        return 'Unknown callback: ' + self.route + ' <' + self.method + '>'

class BenchbotSimulator:
  def run(self, supervisor_address='172.17.0.1', supervisor_port=8081, client_address='127.0.0.1', client_port=8082):
    app1 = Flask(__name__) # Interface to benchbot
    app2 = Flask(__name__) # Interface to web UI

    @app1.route('/<route>', methods=['GET'])
    # pylint: disable=unused-variable
    def get(route):
        try:
            return jsonify(self.handle_get(route))
        except UnknownRouteError:
            abort(404)
        except UnknownCallbackError:
            abort(500)
        except Exception as e:
          print('Error <get>:', str(e))
          abort(500)

    @app1.route('/<route>', methods=['POST'])
    # pylint: disable=unused-variable
    def post(route):
        try:
            return jsonify(self.handle_post(route, request.get_json(silent=True)))
        except UnknownRouteError:
            abort(404)
        except UnknownCallbackError:
            abort(500)
        except Exception as e:
            print(str(e))

    @app1.route('/locations', methods=['GET'])
    # pylint: disable=unused-variable
    def locations():
        try:
          rospy.wait_for_service('/navigation/get_locations')
          get_locations = rospy.ServiceProxy('/navigation/get_locations', Locations)
          
          locations = []
          for location in get_locations().result.locations:
            if location.location_id not in self.config['locations']:
              continue
            
            locations.append({
              'id': location.location_id,
              'position': {
                'x': location.marker.pose.position.x, 
                'y': location.marker.pose.position.y, 
                'z': location.marker.pose.position.z
              },
              'orientation': {
                'x': location.marker.pose.orientation.x, 
                'y': location.marker.pose.orientation.y, 
                'z': location.marker.pose.orientation.z, 
                'w': location.marker.pose.orientation.w,
              }
            })

          return jsonify(locations)
        except Exception as e:
          print(str(e))
          abort(500)

    @app1.route('/locations/<location_id>', methods=['GET'])
    # pylint: disable=unused-variable
    def location(location_id):
        try:
          if location_id not in self.config['locations']:
            raise Exception('Unknown location - ' + location_id)

          rospy.wait_for_service('/navigation/get_location_pose')
          get_location = rospy.ServiceProxy('/navigation/get_location_pose', LocationPose)

          location = get_location(location_id)
          
          return jsonify({
              'id': location_id,
              'position': {
                'x': location.pose.position.x, 
                'y': location.pose.position.y, 
                'z': location.pose.position.z
              },
              'orientation': {
                'x': location.pose.orientation.x, 
                'y': location.pose.orientation.y, 
                'z': location.pose.orientation.z, 
                'w': location.pose.orientation.w,
              }
            })
        except Exception as e:
          print('Error <location>:', str(e))
          abort(500)


    @app1.route('/complete', methods=['POST'])
    # pylint: disable=unused-variable
    def complete():
        try:
            return jsonify(self.handle_complete(request.get_json(silent=True)))
        except Exception as e:
            print('Error <complete>:', str(e))

    @app1.route('/objectives', methods=['GET'])
    # pylint: disable=unused-variable
    def objectives_available():
        try:
            return jsonify([objective_id for objective_id in self.config['objectives'] if self.can_complete(objective_id)])
        except Exception as e:
            print(e)

    @app2.route('/')
    # pylint: disable=unused-variable
    def main():
        return jsonify({
            'get': [self.config['routes'][route]['name'] if 'name' in self.config['routes'][route] else route for route in self.config['routes'] if 'get' in self.config['routes'][route]], 
            'send': [self.config['routes'][route]['name'] if 'name' in self.config['routes'][route] else route for route in self.config['routes'] if 'post' in self.config['routes'][route]]
        })

    @app2.route('/objectives')
    # pylint: disable=unused-variable
    def objectives():
        return jsonify(self.config['objectives'])

    @app2.route('/init', methods=['POST'])
    # pylint: disable=unused-variable
    def initialise():
        self.handle_initialise()
        return jsonify()

    @app2.route('/result', methods=['GET'])
    # pylint: disable=unused-variable
    def result():
        return jsonify(self.context.progress)

    app1.debug = True
    benchbot_server = WSGIServer((supervisor_address, supervisor_port), app1)
    benchbot_server.start()

    ui_server = WSGIServer((client_address, client_port), app2)
    ui_server.start()

    evt = Event()

    gevent.signal(signal.SIGQUIT, evt.set)
    gevent.signal(signal.SIGTERM, evt.set)
    gevent.signal(signal.SIGINT, evt.set)

    print('Benchbot Supervisor started on', supervisor_address + ':' + str(supervisor_port))
    print('Client Server started on', client_address + ':' + str(client_port))
    evt.wait()
    print("Shutting down server")

    benchbot_server.stop()
    ui_server.stop()