from __future__ import print_function

from enum import Enum, unique
import importlib
import jsonpickle
import jsonpickle.ext.numpy as jet
import os
import requests
import sys
import time

from .agent import Agent

jet.register_handlers()

DEFAULT_ADDRESS = 'benchbot_supervisor'
DEFAULT_PORT = 10000

RESULT_LOCATION = '/tmp/benchbot_result'

TIMEOUT_SUPERVISOR = 60


class _UnexpectedResponseError(requests.RequestException):
    """Consistent error messaging for when the Supervisor rejects a query"""
    def __init__(self, http_status_code, *args, **kwargs):
        super(_UnexpectedResponseError, self).__init__(
            "Received an unexpected response from BenchBot supervisor "
            "(HTTP status code: %d)" % http_status_code, *args, **kwargs)


@unique
class ActionResult(Enum):
    """Result of an action that an agent has taken

    Values
    ------
    SUCCESS : 
        Action succeeded, and the robot is ready for a new action
    FINISHED : 
        Action succeeded, and the robot is finished in the current scene
    COLLISION : 
        Action failed, and the robot has colliding with an obstacle
    """
    SUCCESS = 0,
    FINISHED = 1,
    COLLISION = 2


class BenchBot(object):
    """BenchBot handles communication between the client and server systems,
    and abstracts away hardware and simulation, such that code written to be
    run by BenchBot will run with either a real or simulated robot
    """
    @unique
    class RouteType(Enum):
        """Enum denoting type of route (used in building routes when talking
        with a Supervisor)
        """
        CONNECTION = 0,
        CONFIG = 1,
        ROBOT = 2,
        RESULTS = 3,
        EXPLICIT = 4

    ROUTE_MAP = {
        RouteType.CONNECTION: 'connections',
        RouteType.CONFIG: 'config',
        RouteType.ROBOT: 'robot',
        RouteType.RESULTS: 'results_functions',
        RouteType.EXPLICIT: ''
    }

    def __init__(self,
                 agent=None,
                 supervisor_address='http://' + DEFAULT_ADDRESS + ':' +
                 str(DEFAULT_PORT) + '/',
                 auto_start=True):
        self.agent = None
        self.supervisor_address = supervisor_address
        self._connection_callbacks = {}

        if auto_start:
            self.start()
        self.set_agent(agent)

    def _build_address(self, route_name, route_type=RouteType.CONNECTION):
        """Builds an address for communication with a running instance of 
        BenchBot Supervisor

        Parameters
        ----------
        route_name :
            The name of the route within the subdirectory (e.g. 'is_finished')

        route_type :
            The type of route which maps to the URL's subdirectory (e.g. 
            RouteType.ROBOT = 'robot')

        Returns
        -------
        string
            A full URL string describing the route (e.g.
            'http://localhost:10000/robot/is_finished')
        """
        base = self.supervisor_address + (
            '' if self.supervisor_address.endswith('/') else '/')
        if route_type not in BenchBot.ROUTE_MAP:
            raise ValueError(
                "Cannot build address from invalid route type: %s" %
                route_type)
        return (base + BenchBot.ROUTE_MAP[route_type] +
                ('/' if BenchBot.ROUTE_MAP[route_type] else '') + route_name)

    def _query(self,
               route_name=None,
               route_type=RouteType.CONNECTION,
               data=None,
               method=requests.get):
        """Sends a request to a running BenchBot Supervisor, and returns the
        response

        Parameters
        ----------
        route_name: 
            The name of the route within the subdirectory (e.g. 'is_finished')

        route_type :
            The type of route which maps to the URL's subdirectory (e.g.
            RouteType.ROBOT = 'robot')

        data :
            A dict of data to attach to the request

        method :
            HTTP method to use for the request (should generally always be GET)

        Returns
        -------
        dict
            The JSON data returned by the request's response
        """
        data = {} if data is None else data
        addr = self._build_address(route_name, route_type)
        try:
            resp = requests.get(addr, json=data)
            if resp.status_code >= 300:
                raise _UnexpectedResponseError(resp.status_code)
            return jsonpickle.decode(resp.content)
        except:
            raise requests.ConnectionError(
                "Communication to BenchBot supervisor "
                "failed using the route:\n\t%s" % addr)

    @staticmethod
    def _attempt_connection_imports(connection_data):
        """Attempts to dynamically import any API-side connection callbacks
        (this method should never need to be called manually)

        Parameters
        ----------
        connection_data :
            A dict containing the data defining the connection

        Returns
        -------
        None

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
            A list of actions the robot can take. If the robot has collided
            with an obstacle or finished its task, this list will be empty.
        """
        return ([] if self._query('is_collided',
                                  BenchBot.RouteType.ROBOT)['is_collided']
                or self._query('is_finished',
                               BenchBot.RouteType.ROBOT)['is_finished'] else
                self._query('task/actions', BenchBot.RouteType.CONFIG))

    @property
    def config(self):
        """Returns detailed information about the current BenchBot configuration

        Returns
        -------
        dict
            A dict of all configuration parameters as retrieved from the
            running BenchBot supervisor
        """
        return self._query('', BenchBot.RouteType.CONFIG)

    @property
    def observations(self):
        """The list of observations the robot is currently providing

        Returns
        -------
        list
            A list of observations.
        """
        return self._query('task/observations', BenchBot.RouteType.CONFIG)

    @property
    def result_filename(self):
        """The location where results should be written. If the path doesn't
        exist, it makes it.

        Returns
        -------
        str
            The filename that the results will be written to.
        """
        if not os.path.exists(os.path.dirname(RESULT_LOCATION)):
            os.makedirs(os.path.dirname(RESULT_LOCATION))
        return os.path.join(RESULT_LOCATION)

    def empty_results(self):
        """Helper method for getting an empty results dict, pre-populated with
        metadata from the currently running configuration. See the
        'results_functions()' method for help filling in the empty results.

        Returns
        -------
        dict
            A dict with the fields 'task_details' (populated),
            'environment_details' (populated), and 'results' (empty)
        """
        return {
            'task_details':
            self._query('task', BenchBot.RouteType.CONFIG),
            'environment_details':
            self._query('environments', BenchBot.RouteType.CONFIG),
            'results':
            self._query('create', BenchBot.RouteType.RESULTS)
        }

    def next_scene(self):
        """Moves the robot to the next scene, declaring failure if there is no
        next scene defined

        Returns
        -------
        bool
            Denotes whether moving to the next scene succeeded or failed
        """
        # Bail if next is not a valid operation
        if (self._query('is_collided',
                        BenchBot.RouteType.ROBOT)['is_collided']):
            raise RuntimeError("Collision state detected for robot; "
                               "cannot proceed to next scene")

        # Move to the next scene
        print("Moving to next scene ... ", end='')
        sys.stdout.flush()
        resp = self._query('next', BenchBot.RouteType.ROBOT)
        print("Done." if resp['next_success'] else "Failed.")

        # Return the result of moving to next (a failure means we are already
        # at the last scene)
        return resp['next_success']

    def reset(self):
        """Resets the robot state, starting again at the first scene with a
        fresh environment. Resetting is skipped  if the environment is still in
        a fresh state.

        Returns
        -------
        tuple
            Observations and action result at the start of the task (should
            always be SUCCESS).
        """
        # Only restart the supervisor if it is in a dirty state
        if self._query('is_dirty', BenchBot.RouteType.ROBOT)['is_dirty']:
            print("Dirty robot state detected. Performing reset ... ", end='')
            sys.stdout.flush()
            self._query('reset',
                        BenchBot.RouteType.ROBOT)  # This should be a send...
            print("Complete.")
        return self.step(None)

    def results_functions(self):
        return {
            r: lambda *args, _fn=r, **kwargs: self._query(
                '/%s' % _fn, BenchBot.RouteType.RESULTS, {
                    'args': args,
                    'kwargs': kwargs
                })
            for r in self._query('/', BenchBot.RouteType.RESULTS)
        }

    def run(self, agent=None):
        """Helper function that runs the robot according to the agent given.
        Generally, you should use this function and implement your object in
        your own custom agent class. 
        """
        print("SETTING AGENT")
        if agent is not None:
            self.set_agent(agent)
        print("SET AGENT")
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

        # Run through the scenes until done
        scene_fn()
        while self.next_scene():
            scene_fn()

        # We've made it to the end, we should save our results!
        self.agent.save_result(self.result_filename, self.empty_results(),
                               self.results_functions())

    def set_agent(self, agent):
        """Updates the current agent, and starts its connection with a BenchBot
        Supervisor if requested"""
        if agent is None:
            self.agent = None
            return

        if agent is not None and not isinstance(agent, Agent):
            raise ValueError("BenchBot received an agent of type '%s' "
                             "which is not an instance of '%s'." %
                             (agent.__class__.__name__, Agent.__name__))
        self.agent = agent

    def start(self):
        """Establishes a connect to the Supervisor, and then uses this to
        establish a connection with a running robot. It then initialises all
        connections, ensuring API-side callbacks are accessible.
        """
        # Establish a connection to the supervisor (throw an error on failure)
        print("Waiting to establish connection to a running supervisor ... ",
              end='')
        sys.stdout.flush()
        start_time = time.time()
        connected = False
        while not connected and time.time() - start_time < TIMEOUT_SUPERVISOR:
            try:
                self._query("/", BenchBot.RouteType.EXPLICIT)
                connected = True
            except:
                pass
            time.sleep(3)
        if not connected:
            raise requests.ConnectionError(
                "Could not find a BenchBot supervisor @ '%s'. "
                "Are you sure it is available?" % self.supervisor_address)
        print("Connected!")

        # Wait until the robot is running
        print("Waiting to establish connection to a running robot ... ",
              end='')
        sys.stdout.flush()
        while (not self._query("is_running",
                               BenchBot.RouteType.ROBOT)['is_running']):
            time.sleep(0.1)
        print("Connected!")

        # Get references to all of the API callbacks in robot config
        self._connection_callbacks = {
            k: BenchBot._attempt_connection_imports(v)
            for k, v in self._query('robot', BenchBot.RouteType.CONFIG)
            ['connections'].items()
        }

        # Ensure we are starting in a clean robot state
        if (self._query('selected_environment',
                        BenchBot.RouteType.ROBOT)['number'] != 0):
            print(
                "Robot detected not to be in the first scene. "
                "Performing restart ... ",
                end='')
            sys.stdout.flush()
            self._query('restart', BenchBot.RouteType.ROBOT)
            print("Done.")
        else:
            self.reset()

    def step(self, action, **action_kwargs):
        """Performs 'action' with 'action_kwargs' as its arguments, and returns
        the observations after 'action' has completed, regardless of the
        result.

        Parameters
        ----------
        action : 
            Name of action to be performed. The 'actions' property is available
            to list available actions if you are unsure what is available.

        **action_kwargs
            Arguments to be used by the action. See the connection's callbacks
            by using the 'config' property if you are unsure of an action's
            supported arguments.

        Returns
        -------
        tuple
            Observations and action result after the action has finished.

        """
        # Perform the requested action if possible
        if action is not None:
            # Detect actions unavailable due to robot state
            if action not in self.actions:
                raise ValueError(
                    "Action '%s' is unavailable due to: %s" %
                    (action, ('COLLISION' if self._query(
                        'is_collided', BenchBot.RouteType.ROBOT)['is_collided']
                              else 'FINISHED' if self._query(
                                  'is_finished', BenchBot.RouteType.ROBOT)
                              ['is_finished'] else 'WRONG_ACTUATION_MODE?')))

            # Made it through checks, actually perform the action
            print("Sending action '%s' with args: %s" %
                  (action, action_kwargs))
            self._query(action, BenchBot.RouteType.CONNECTION, action_kwargs)

        # Derive action_result (TODO should probably not be this flimsy...)
        action_result = ActionResult.SUCCESS
        if self._query('is_collided', BenchBot.RouteType.ROBOT)['is_collided']:
            action_result = ActionResult.COLLISION
        elif self._query('is_finished',
                         BenchBot.RouteType.ROBOT)['is_finished']:
            action_result = ActionResult.FINISHED

        # Retrieve and return an updated set of observations
        raw_os = {
            o: self._query(o, BenchBot.RouteType.CONNECTION)
            for o in self.observations
        }
        raw_os.update({
            'scene_number':
            self._query('selected_environment',
                        BenchBot.RouteType.ROBOT)['number']
        })
        return ({
            k: (self._connection_callbacks[k](v) if
                (k in self._connection_callbacks
                 and self._connection_callbacks[k] is not None) else v)
            for k, v in raw_os.items()
        }, action_result)
