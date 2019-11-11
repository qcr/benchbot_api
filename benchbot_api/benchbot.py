from enum import Enum, unique
import importlib
import requests

DEFAULT_ADDRESS = 'benchbot_supervisor'
DEFAULT_PORT = 10000


class _UnexpectedResponseError(requests.RequestException):

    def __init__(self, http_status_code, *args, **kwargs):
        super(_UnexpectedResponseError, self).__init__(
            "Received an unexpected response from BenchBot supervisor "
            "(HTTP status code: %d)" % http_status_code, *args, **kwargs)


class BenchBot(object):

    @unique
    class RouteType(Enum):
        ROUTE = 0,
        CONFIG = 1,
        EXPLICIT = 2

    def __init__(self,
                 supervisor_address='http://' + DEFAULT_ADDRESS + ':' +
                 str(DEFAULT_PORT) + '/',
                 auto_start=True):
        self.supervisor_address = supervisor_address
        self._connection_callbacks = {}
        if auto_start:
            self.start()

    def _build_address(self, route_name, route_type=RouteType.ROUTE):
        base = self.supervisor_address + (
            '' if self.supervisor_address.endswith('/') else '/')
        if route_type == BenchBot.RouteType.ROUTE:
            return base + 'connections/' + route_name
        elif route_type == BenchBot.RouteType.CONFIG:
            return base + 'config/' + route_name
        elif route_type == BenchBot.RouteType.EXPLICIT:
            return base + route_name
        else:
            raise ValueError(
                "Cannot build address from invalid route type: %s" %
                route_type)

    def _receive(self, route_name=None, route_type=RouteType.ROUTE):
        try:
            resp = requests.get(self._build_address(route_name, route_type))
            if resp.status_code >= 300:
                raise _UnexpectedResponseError(resp.status_code)
            return resp.json()
        except:
            raise requests.ConnectionError(
                "Failed to establish a connection to BenchBot supervisor")

    def _send(self, route_name=None, data=None, route_type=RouteType.ROUTE):
        data = {} if data is None else data
        try:
            resp = requests.get(self._build_address(route_name, route_type),
                                json=data)
            if resp.status_code >= 300:
                raise _UnexpectedResponseError(resp.status_code)
        except:
            raise requests.ConnectionError(
                "Failed to establish a connection to BenchBot supervisor")

    @staticmethod
    def _attempt_connection_imports(connection_data):
        if 'callback_api' in connection_data:
            x = connection_data['callback_api'].rsplit('.', 1)
            return getattr(importlib.import_module('benchbot_api.' + x[0]),
                           x[1])
        return None

    @property
    def actions(self):
        return self._receive('actions', BenchBot.RouteType.CONFIG)

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

    def finish(self, result):
        # TODO
        pass

    def is_done(self):
        # TODO
        return False

    def reset(self):
        # TODO
        return self.step(None)[0]

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

    def step(self, action):
        # Perform the requested action
        # TODO

        # Retrieve and return an updated set of observations
        # TODO is there anything meaningful to give back as reward or info???
        raw_os = {o: self._receive(o) for o in self.observations}
        return ({
            k: self._connection_callbacks[k](v)
            for k, v in raw_os.items()
            if self._connection_callbacks[k] is not None
        }, 0, '')
