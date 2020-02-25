from enum import Enum, unique
import importlib
import os
import requests

DEFAULT_ADDRESS = 'benchbot_supervisor'
DEFAULT_PORT = 10000

RESULT_LOCATION = '/tmp/benchbot_result'


class _UnexpectedResponseError(requests.RequestException):

    def __init__(self, http_status_code, *args, **kwargs):
        super(_UnexpectedResponseError, self).__init__(
            "Received an unexpected response from BenchBot supervisor "
            "(HTTP status code: %d)" % http_status_code, *args, **kwargs)


@unique
class ActionResult(Enum):
    SUCCESS = 0,
    FINISHED = 1,
    COLLISION = 2


class BenchBot(object):

    @unique
    class RouteType(Enum):
        CONNECTION = 0,
        CONFIG = 1,
        SIMULATOR = 2,
        STATUS = 3,
        EXPLICIT = 4

    def __init__(self,
                 supervisor_address='http://' + DEFAULT_ADDRESS + ':' +
                 str(DEFAULT_PORT) + '/',
                 auto_start=True):
        self.supervisor_address = supervisor_address
        self._connection_callbacks = {}
        if auto_start:
            self.start()

    def _build_address(self, route_name, route_type=RouteType.CONNECTION):
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
        if 'callback_api' in connection_data:
            x = connection_data['callback_api'].rsplit('.', 1)
            return getattr(importlib.import_module('benchbot_api.' + x[0]),
                           x[1])
        return None

    @property
    def actions(self):
        return ([] if self._receive(
            'is_collided', BenchBot.RouteType.SIMULATOR)['is_collided'] or
                self._receive('is_finished', BenchBot.RouteType.STATUS) else
                ('actions', BenchBot.RouteType.CONFIG))

    @property
    def observations(self):
        return self._receive('observations', BenchBot.RouteType.CONFIG)

    @property
    def task_details(self):
        return {
            k: v for k, v in zip(['type', 'control_mode', 'localisation_mode'],
                                 self._receive('task_name', BenchBot.RouteType.
                                               CONFIG).split(':'))
        }

    @property
    def result_filename(self):
        if not os.path.exists(os.path.pardir(RESULT_LOCATION)):
            os.makedirs(os.path.pardir(RESULT_LOCATION))
        return os.path.join(RESULT_LOCATION)

    def reset(self):
        # Only restart the supervisor if it is in a dirty state
        if self._receive('is_dirty', BenchBot.RouteType.SIMULATOR)['is_dirty']:
            self._receive('restart', BenchBot.RouteType.SIMULATOR
                         )  # This should probably be a send...

        return self.step(None)

    def start(self):
        # Establish connection (throw an error if we can't find the supervisor)
        try:
            self._receive("/", BenchBot.RouteType.EXPLICIT)
        except requests.ConnectionError as e:
            raise type(e)("Could not find a BenchBot supervisor @ '%s'. "
                          "Are you sure it is available?" %
                          self.supervisor_address)

        # Get references to all of the API callbacks in robot config
        self._connection_callbacks = {
            k:
            BenchBot._attempt_connection_imports(v) for k, v in self._receive(
                'robot', BenchBot.RouteType.CONFIG).items()
        }

    def step(self, action, **action_kwargs):
        # Perform the requested action
        if action is not None:
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
