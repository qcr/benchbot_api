from __future__ import print_function

from enum import Enum, unique
import importlib
import os
import requests
import sys
import time

from .agent import Agent

DEFAULT_ADDRESS = 'benchbot_supervisor'
DEFAULT_PORT = 10000

RESULT_LOCATION = '/tmp/benchbot_result'


class _UnexpectedResponseError(requests.RequestException):
    """ """

    def __init__(self, http_status_code, *args, **kwargs):
        super(_UnexpectedResponseError, self).__init__(
            "Received an unexpected response from BenchBot supervisor "
            "(HTTP status code: %d)" % http_status_code, *args, **kwargs)


@unique
class ActionResult(Enum):
    """Result of an action that an agent has taken
    SUCCESS : Action has finished successfully and the robot is ready for a new action
    FINISHED : Action has finished successfully and the robot has finished all its goals
    COLLISION : Action has not finished successfully and the robot has collided with an obstacle
    """
    SUCCESS = 0,
    FINISHED = 1,
    COLLISION = 2


class BenchBot(object):
    """BenchBot handles communication between the client and server systems, and abstracts away hardware and simulation, such that code written to be run by BenchBot will run with either a real or simulated robot"""

    SUPPORTED_ACTIONS = {
        'move_next': [],
        'move_distance': ['distance'],
        'move_angle': ['angle']
    }

    @unique
    class RouteType(Enum):
        """ """
        CONNECTION = 0,
        CONFIG = 1,
        SIMULATOR = 2,
        STATUS = 3,
        EXPLICIT = 4

    def __init__(self,
                 agent=None,
                 supervisor_address='http://' + DEFAULT_ADDRESS + ':' +
                 str(DEFAULT_PORT) + '/',
                 auto_start=True):
        if agent is not None and not isinstance(agent, Agent):
            raise ValueError("BenchBot received an agent of type '%s' "
                             "which is not an instance of '%s'." %
                             (agent.__class__.__name__, Agent.__name__))
        self.agent = agent

        self.supervisor_address = supervisor_address
        self._connection_callbacks = {}
        if auto_start:
            self.start()

    def _build_address(self, route_name, route_type=RouteType.CONNECTION):
        """

        Parameters
        ----------
        route_name :

        route_type :
            Default value = RouteType.CONNECTION

        Returns
        -------


        """
        base = self.supervisor_address + (
            '' if self.supervisor_address.endswith('/') else '/')
        if route_type == BenchBot.RouteType.CONNECTION:
            return base + 'connections/' + route_name
        elif route_type == BenchBot.RouteType.CONFIG:
            return base + 'config/' + route_name
        elif route_type == BenchBot.RouteType.SIMULATOR:
            return base + 'simulator/' + route_name
        elif route_type == BenchBot.RouteType.STATUS:
            return base + 'status/' + route_name
        elif route_type == BenchBot.RouteType.EXPLICIT:
            return base + route_name
        else:
            raise ValueError(
                "Cannot build address from invalid route type: %s" %
                route_type)

    def _receive(self, route_name=None, route_type=RouteType.CONNECTION):
        """

        Parameters
        ----------
        route_name :
            Default value = None
        route_type :
            Default value = RouteType.CONNECTION

        Returns
        -------


        """
        try:
            resp = requests.get(self._build_address(route_name, route_type))
            if resp.status_code >= 300:
                raise _UnexpectedResponseError(resp.status_code)
            return resp.json()
        except:
            raise requests.ConnectionError(
                "Failed to establish a connection to BenchBot supervisor")

    def _send(self,
              route_name=None,
              data=None,
              route_type=RouteType.CONNECTION):
        """

        Parameters
        ----------
        route_name :
            Default value = None
        data :
            Default value = None
        route_type :
            Default value = RouteType.CONNECTION

        Returns
        -------


        """
        data = {} if data is None else data
        try:
            resp = requests.get(self._build_address(route_name, route_type),
                                json=data)
            if resp.status_code >= 300:
                raise _UnexpectedResponseError(resp.status_code)
        except:
            raise requests.ConnectionError(
                "Failed to establish a connection to BenchBot supervisor with "
                "input data: %s, %s, %s" % (route_name, route_type.name, data))

    @staticmethod
    def _attempt_connection_imports(connection_data):
        """

        Parameters
        ----------
        connection_data :


        Returns
        -------


        """
        if 'callback_api' in connection_data:
            x = connection_data['callback_api'].rsplit('.', 1)
            return getattr(importlib.import_module('benchbot_api.' + x[0]),
                           x[1])
        return None

    @property
    def actions(self):
        """The list of actions the robot is able to take.

        Returns
        -------
        list
            A list of actions the robot can take. If the robot has collided with an obstacle or finished its task, this list will be empty.
        """
        return ([] if self._receive(
            'is_collided', BenchBot.RouteType.SIMULATOR)['is_collided'] or
                self._receive('is_finished',
                              BenchBot.RouteType.STATUS)['is_finished'] else
                self._receive('actions', BenchBot.RouteType.CONFIG))

    @property
    def environment_details(self):
        names = self._receive('environment_names', BenchBot.RouteType.CONFIG)
        return {
            'name': names[0].split('_')[0],
            'numbers': [x.split('_')[-1] for x in names]
        }

    @property
    def observations(self):
        """The list of observations the robot can see.

        Returns
        -------
        list
            A list of observations.
        """
        return self._receive('observations', BenchBot.RouteType.CONFIG)

    @property
    def task_details(self):
        """The details of the task.

        Returns
        -------
        dict
            The 'type', 'control_mode', and 'localisation_mode' of the task.
        """
        return {
            k: v for k, v in zip(['type', 'control_mode', 'localisation_mode'],
                                 self._receive('task_name', BenchBot.RouteType.
                                               CONFIG).split(':'))
        }

    @property
    def result_filename(self):
        """The result filename. If the path doesn't exist, it makes it.

        Returns
        -------
        str
            The filename that the results will be written to.
        """
        if not os.path.exists(os.path.dirname(RESULT_LOCATION)):
            os.makedirs(os.path.dirname(RESULT_LOCATION))
        return os.path.join(RESULT_LOCATION)

    def next_scene(self):
        # Bail if next is not a valid operation
        if (self._receive('is_collided',
                          BenchBot.RouteType.SIMULATOR)['is_collided']):
            raise RuntimeError("Collision stated detected for robot; "
                               "cannot proceed to next scene")
        elif 'semantic_slam' in self.task_details['type']:
            raise RuntimeError("Semantic SLAM only consists of one scene; "
                               "cannot proceed to next scene")

        # Move to the next scene
        print("Moving to next scene ... ", end='')
        resp = self._receive(
            'next', BenchBot.RouteType.SIMULATOR)  # This should be a send...
        print("Done.")

        # Raise an error if it failed (because it was called a second time)
        if not resp['next_success']:
            raise RuntimeError("Simulator is already at final scene; "
                               "cannot proceed to next scene")

    def reset(self):
        """Resets the robot state, and restarts the supervisor if necessary.

        Returns
        -------
        tuple
            Observations and action result at the start of the task.
        """
        # Only restart the supervisor if it is in a dirty state
        if self._receive('is_dirty', BenchBot.RouteType.SIMULATOR)['is_dirty']:
            print("Dirty simulator state detected. Performing reset ... ",
                  end='')
            sys.stdout.flush()
            self._receive(
                'reset',
                BenchBot.RouteType.SIMULATOR)  # This should be a send...
            print("Complete.")
        return self.step(None)

    def run(self):
        """Helper function that runs the robot according to the agent given.
        Use this function as the basis for implementing a custom AI loop.

        """
        if self.agent is None:
            raise RuntimeError(
                "Can't call Benchbot.run() without an agent attached. Either "
                "create your BenchBot instance with an agent argument, "
                "or create your own run logic instead of using Benchbot.run()")

        # Copy & pasting the same code twice just doesn't feel right...
        def scene_fn():
            observations, action_result = self.reset()
            while not self.agent.is_done(action_result):
                action, action_args = self.agent.pick_action(
                    observations, self.actions)
                observations, action_result = self.step(action, **action_args)

        # Run through the first scene until done
        scene_fn()

        # Attempt to run through the second scene if in Scene Change Detection
        # mode
        if 'scd' in self.task_details['type']:
            self.next_scene()
            scene_fn()

        # We've made it to the end, we should save our results!
        self.agent.save_result(self.result_filename)

    def start(self):
        """Connects to the supervisor and initialises the connection callbacks.

        Raises
        ------
        requests.ConnectionError
            If the BenchBot supervisor cannot be found.
        """
        # Establish a connection to the supervisor (throw an error on failure)
        print("Waiting to establish connection to a running supervisor ... ",
              end='')
        sys.stdout.flush()
        try:
            self._receive("/", BenchBot.RouteType.EXPLICIT)
        except requests.ConnectionError as e:
            raise type(e)("Could not find a BenchBot supervisor @ '%s'. "
                          "Are you sure it is available?" %
                          self.supervisor_address)
        print("Connected!")

        # Wait until the simulator is running
        print("Waiting to establish connection to a running simulator ... ",
              end='')
        sys.stdout.flush()
        while (not self._receive("is_running",
                                 BenchBot.RouteType.SIMULATOR)['is_running']):
            time.sleep(0.1)
        print("Connected!")

        # Get references to all of the API callbacks in robot config
        self._connection_callbacks = {
            k:
            BenchBot._attempt_connection_imports(v) for k, v in self._receive(
                'robot', BenchBot.RouteType.CONFIG).items()
        }

        # Ensure we are starting in a clean simulator state
        if (self._receive('map_selection_number',
                          BenchBot.RouteType.SIMULATOR)['map_selection_number']
                != 0):
            print(
                "Simulator detected not to be in the first scene. "
                "Performing restart ... ",
                end='')
            sys.stdout.flush()
            self._receive(
                'restart',
                BenchBot.RouteType.SIMULATOR)  # This should be a send...
        else:
            self.reset()

    def step(self, action, **action_kwargs):
        """Performs 'action' with 'action_kwargs' as its arguments and returns the observations after 'action' has completed, regardless of the result.

        Parameters
        ----------
        action : {'move_next', 'move_distance', 'move_angle'}
            Action to be performed, must be one of 'move_next', 'move_distance', or 'move_angle'.
        **action_kwargs
            Arguments to be used by the action.
            Must be empty if action is 'move_next'.
            Must be 'distance' if action is 'move_distance'. Distance is in metres.
            Must be 'angle' if action is 'move_angle'. Angle is in radians.

        Returns
        -------
        tuple
            Observations and action result after the action has finished.

        """
        # Perform the requested action if possible
        if action is not None:
            # Detect unsupported actions
            if action not in BenchBot.SUPPORTED_ACTIONS:
                raise ValueError(
                    "Action '%s' is not a valid action (valid actions are: %s)."
                    % (action, ', '.join(BenchBot.SUPPORTED_ACTIONS.keys())))
            elif len(action_kwargs) != len(BenchBot.SUPPORTED_ACTIONS[action]):
                raise ValueError(
                    "Action '%s' requires %d args (%s); you provided %d." %
                    (action, len(BenchBot.SUPPORTED_ACTIONS[action]),
                     ', '.join(BenchBot.SUPPORTED_ACTIONS[action]),
                     len(action_kwargs)))
            else:
                missing_keys = (set(BenchBot.SUPPORTED_ACTIONS[action]) -
                                set(action_kwargs.keys()))
                if missing_keys:
                    raise ValueError(
                        "Action '%s' requires argument '%s' which was not "
                        "provided." % (action, missing_keys.pop()))

            # Detect actions unavailable due to robot state
            if action not in self.actions:
                raise ValueError(
                    "Action '%s' is unavailable due to: %s" %
                    (action, ('COLLISION' if self._receive(
                        'is_collided', BenchBot.RouteType.SIMULATOR)
                              ['is_collided'] else 'FINISHED' if self._receive(
                                  'is_finished', BenchBot.RouteType.STATUS)
                              ['is_finished'] else 'WRONG_ACTUATION_MODE?')))

            # Made it through checks, actually perform the action
            print("Sending action '%s' with args: %s" %
                  (action, action_kwargs))
            self._send(action, action_kwargs, BenchBot.RouteType.CONNECTION)

        # Derive action_result (TODO should probably not be this flimsy...)
        action_result = ActionResult.SUCCESS
        if self._receive('is_collided',
                         BenchBot.RouteType.SIMULATOR)['is_collided']:
            action_result = ActionResult.COLLISION
        elif self._receive('is_finished',
                           BenchBot.RouteType.STATUS)['is_finished']:
            action_result = ActionResult.FINISHED

        # Retrieve and return an updated set of observations
        raw_os = {o: self._receive(o) for o in self.observations}
        return ({
            k: self._connection_callbacks[k](v)
            if self._connection_callbacks[k] is not None else v
            for k, v in raw_os.items()
        }, action_result)
