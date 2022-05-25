**NOTE: this software needs to interface with a running instance of the BenchBot software stack. Unless you are running against a remote stack / robot, please install this software with the BenchBot software stack as described [here](https://github.com/qcr/benchbot).**

# BenchBot API

![benchbot_api](./docs/benchbot_api_web.gif)

The BenchBot API provides a simple interface for controlling a robot or simulator through actions, and receiving data through observations. As shown above, the entire code required for running an agent in a realistic 3D simulator is only a handful of simple Python commands.

[Open AI Gym](https://gym.openai.com) users will find the breakdown into actions, observations, and steps extremely familiar. BenchBot API allows researchers to develop and test novel algorithms with real robot systems and realistic 3D simulators, without the typical hassles arising when interfacing with complicated multi-component robot systems.

Running a robot through an entire environment, with your own custom agent, is as simple as one line of code with the BenchBot API:

```python
from benchbot_api import BenchBot
from my_agent import MyAgent

BenchBot(agent=MyAgent()).run()
```

The above assumes you have created your own agent by overloading the abstract `Agent` class provided with the API. Overloading the abstract class requires implementing 3 basic methods. Below is a basic example to spin on the spot:

```python
from benchbot_api import Agent
import json

class MyAgent(Agent):

    def is_done(self, action_result):
        # Go forever
        return False

    def pick_action(self, observations, action_list):
        # Rotates on the spot indefinitely, 5 degrees at a time
        # (assumes we are running in passive mode)
        return 'move_angle', {'angle': 5}

    def save_result(self, filename, empty_results, results_format_fns):
        # Save some blank results
        with open(filename, 'w') as f:
            json.dump(empty_results, f)
```

If you prefer to do things manually, a more exhaustive suite of functions are also available as part of the BenchBot API. Instead of using the `BenchBot.run()` method, a large number of methods are available through the API. Below highlights a handful of the capabilities of BenchBot API:

```python
from benchbot_api import BenchBot, RESULT_LOCATION
import json
import matplotlib.pyplot as plt

# Create a BenchBot instance & reset the simulator / robot to starting state
b = BenchBot()
observations, action_result = b.reset()

# Print details of selected task & environment
print(b.task_details)
print(b.environment_details)

# Visualise the current RGB image from the robot
plt.imshow(observations['image_rgb'])

# Move to the next pose if we have a 'move_next' action available
if 'move_next' in b.actions:
    observations, action_result = b.step('move_next')

# Save some empty results
with open(RESULT_LOCATION, 'w') as f:
    json.dump(b.empty_results(), f)
```

For sample solutions that use the BenchBot API, see the examples add-ons available (e.g. [`benchbot-addons/examples_base`](https://github.com/benchbot-addons/examples_base) and [`benchbot-addons/examples_ssu`](https://github.com/benchbot-addons/examples_ssu)).

## Installing BenchBot API

BenchBot API is a Python package, installable with pip. Run the following in the root directory of where this repository was cloned:

```
u@pc:~$ pip install .
```

## Using the API to communicate with a robot

Communication with the robot comes through a series of "channels" which are defined by the robot's definition file (e.g. [carter](https://github.com/benchbot-addons/robots_isaac/blob/master/robots/carter.yaml)). A task definition file (e.g. [semantic_slam:passive:ground_truth](https://github.com/benchbot-addons/tasks_ssu/blob/master/tasks/sslam_pgt.yaml)) then declares which of these connections are provided to the API as either sensor observations or actions to be executed by a robot actuator.

The API talks to the [BenchBot Supervisor](https://github.com/qcr/benchbot_supervisor), which handles loading and managing the different kinds of back-end configuration files. This abstracts all of the underlying communication complexities away from the user, allowing the BenchBot API to remain a simple interface that focuses on getting observations and sending actions.

An action is sent to the robot by calling the `BenchBot.step()` method with a valid action (found by checking the `BenchBot.actions` property):

```python
from benchbot_api import BenchBot

b = BenchBot()
available_actions = b.actions
b.step(b.actions[0], {'action_arg:', arg_value})  # Perform the first available action
```

The second parameter is a dictionary of named arguments for the selected action. For example, moving 5m forward with the `'move_distance'` action is represented by the dictionary `{'distance': 5}`.

Observations lists are received as return values from a `BenchBot.step()` call (`BenchBot.reset()` internally calls `BenchBot.step(None)`, which means don't perform an action):

```python
from benchbot_api import BenchBot

b = BenchBot()
observations, action_result = b.reset()
observations, action_result = b.step('move_distance', {'distance': 5})
```

The returned `observations` variable holds a dictionary with key-value pairs corresponding to the name-data defined by each observation channel.

The `action_result` is an enumerated value denoting the result of the action (use `from benchbot_api import ActionResult` to access the `Enum` class). You should use this result to guide the progression of your algorithm either manually or in the `is_done()` method of your `Agent`. Possible values for the returned `action_result` are:

- `ActionResult.SUCCESS`: the action was carried out successfully
- `ActionResult.FINISHED`: the action was carried out successfully, and the robot is now finished its traversal through the scene (only used in `passive` actuation mode)
- `ActionResult.COLLISION`: the action crashed the robot into an obstacle, and as a result it will not respond to any further actuation commands (at this point you should quit)

### Standard Communication Channels

Tasks and robot definition files declare actions and observations, and these files are include through [BenchBot add-ons](https://github.com/qcr/benchbot_addons). The add-on creator is free to add and declare channels as they please, but it is a better experience for all if channel definitions are as consistent as possible across the BenchBot ecosystem.

So if you're adding a robot that move between a set of poses, declare a channel called `'move_next` with no arguments. Likewise, a robot that receives image observations should use a channel named `'image_rgb'` with the same format as described below. Feel free to implement the channels however you please for your robot, but consistent interfaces should always be preferred.

If you encounter a task using non-standard channel configurations, the API has all the functionality you need as a user to handle them (`actions`, `config`, & `observations` properties). On the other hand, maybe the non-standard channel should be a new standard. New standard communication channels are always welcome; please open a pull request with the details!

#### Standard action channels:

| Name              |       Required Arguments       | Description                                                                                                                                   |
| ----------------- | :----------------------------: | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `'move_next'`     |             `None`             | Moves the robot to the next pose in its list of pre-defined poses (only available in environments that declare a `'trajectory_poses'` field). |
| `'move_distance'` | <pre>{'distance': float}</pre> | Moves the robot `'distance'` metres directly ahead.                                                                                           |
| `'move_angle'`    |  <pre>{'angle': float}</pre>   | Rotate the angle on the spot by `'angle'` degrees.                                                                                            |

#### Standard observation channels:

| Name                 | Data format                                                                                                                                                                                                                                                                                                     | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| -------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `'image_depth'`      | <pre>numpy.ndarray(shape=(H,W),<br> dtype='float32')</pre>                                                                                                                                                                                                                                                      | Depth image from the default image sensor with depths in meters.                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `'image_depth_info'` | <pre>{<br> 'frame_id': string<br> 'height': int<br> 'width': int<br> 'matrix_instrinsics':<br> numpy.ndarray(shape=(3,3),<br> dtype='float64')<br>'matrix_projection':<br> numpy.ndarray(shape=(3,4)<br> dtype='float64')<br>}</pre>                                                                            | Sensor information for the depth image. `'matrix_instrinsics'` is of the format:<br><pre>[fx 0 cx]<br>[0 fy cy]<br>[0 0 1]</pre> for a camera with focal lengths `(fx,fy)`, & principal point `(cx,cy)`. Likewise, `'matrix_projection'` is:<br><pre>[fx 0 cx Tx]<br>[0 fy cy Ty]<br>[0 0 1 0]</pre>where `(Tx,Ty)` is the translation between stereo sensors. See [here](http://docs.ros.org/melodic/api/sensor_msgs/html/msg/CameraInfo.html) for further information on fields. |
| `'image_rgb'`        | <pre>numpy.ndarray(shape=(H,W,3),<br> dtype='uint8')</pre>                                                                                                                                                                                                                                                      | RGB image from the default image sensor with colour values mapped to the 3 channels, in the 0-255 range.                                                                                                                                                                                                                                                                                                                                                                           |
| `'image_rgb_info'`   | <pre>{<br> 'frame_id': string<br> 'height': int<br> 'width': int<br> 'matrix_instrinsics':<br> numpy.ndarray(shape=(3,3),<br> dtype='float64')<br>'matrix_projection':<br> numpy.ndarray(shape=(3,4)<br> dtype='float64')<br>}</pre>                                                                            | Sensor information for the RGB image. `'matrix_instrinsics'` is of the format:<br><pre>[fx 0 cx]<br>[0 fy cy]<br>[0 0 1]</pre> for a camera with focal lengths `(fx,fy)`, & principal point `(cx,cy)`. Likewise, `'matrix_projection'` is:<br><pre>[fx 0 cx Tx]<br>[0 fy cy Ty]<br>[0 0 1 0]</pre>where `(Tx,Ty)` is the translation between stereo sensors. See [here](http://docs.ros.org/melodic/api/sensor_msgs/html/msg/CameraInfo.html) for further information on fields.   |
| `'laser'`            | <pre>{<br> 'range_max': float64,<br> 'range_min': float64,<br> 'scans':<br> numpy.ndarray(shape=(N,2),<br> dtype='float64')<br>}</pre>                                                                                                                                                                          | Set of scan values from a laser sensor, between `'range_min'` & `'range_max'` (in meters). The `'scans'` array consists of `N` scans of format `[scan_angle, scan_value]`. For example, `scans[100,0]` would get the angle of the 100th scan & `scans[100,1]` would get the distance value.                                                                                                                                                                                        |
| `'poses'`            | <pre>{<br> ...<br> 'frame_name': {<br> 'parent_frame': string<br> 'rotation_rpy':<br> numpy.ndarray(shape=(3,),<br> dtype='float64')<br> 'rotation_xyzw':<br> numpy.ndarray(shape=(4,),<br> dtype='float64')<br> 'translation_xyz':<br> numpy.ndarray(shape=(3,),<br> dtype='float64')<br> }<br> ...<br>}</pre> | Dictionary of relative poses for the current system state. The pose of each system component is available at key `'frame_name'`. Each pose has a `'parent_frame'` which the pose is relative to (all poses are typically with respect to global `'map'` frame), & the pose values. `'rotation_rpy'` is `[roll,pitch,yaw]` in `ZYX` order, `'rotation_xyzw'` is the equivalent quaternion `[x,y,z,w]`, & `'translation_xyz'` is the Cartesion `[x,y,z]` coordinates.                               |

## Using the API to communicate with the BenchBot system

A running BenchBot system manages many other elements besides simply getting data to and from a real / simulated robot. BenchBot encapsulates not just the robot, but also the environment it is operating in (whether that be simulator or real) and task that is currently being attempted.

The API handles communication for all parts of the BenchBot system, including controlling the currently running environment and obtaining configuration information. Below are details for some of the more useful features of the API (all features are also documented in the [`benchbot.py`](./benchbot_api/benchbot.py) source code).

### Gathering configuration information

| API method or property | Description                                                                                                                                                |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `config`               | Returns a `dict` exhaustively describing the current BenchBot configuration. Most of the information returned will not be useful for general BenchBot use. |

### Interacting with the environment

| API method or property | Description                                                                                                                                                                                                                                                                     |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `reset()`              | Resets the current environment scene. For the simulator, this means restarting the running simulator instance with the robot back at its initial position. The method returns initial `observations`, & the `action_result` (should always be `BenchBot.ActionResult.SUCCESS`). |
| `next_scene()`         | Starts the next scene in the current environment (only relevant for tasks with multiple scenes). Note there is no going back once you have moved to the next scene. Returns the same as `reset()`.                                                                              |

### Interacting with an agent

| API method or property        | Description                                                                                                                                                                                                  |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `actions`                     | Returns the list of actions currently available to the agent. This will update as actions are performed in the environment (for example if the agent has collided with an obstacle this list will be empty). |
| `observations`                | Returns the lists of observations available to the agent.                                                                                                                                                    |
| `step(action, **action_args)` | Performs the requested action with the provided named action arguments. See [Using the API to communicate with a robot](#using-the-api-to-communicate-with-a-robot) above for further details.               |

### Creating results

| API method or property                          | Description                                                                                                                                                                                                                                                                                                                           |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `empty_results()`                               | Generates a `dict` of with required result metadata & empty results. Metadata (`'task_details'` & `'environment_details'`) is pre-filled. To create results, all a user needs to do is fill in the empty `'results'` field using format's results functions. These functions are available through the `'results_functions()` method. |
| `results_functions()`                           | Returns a `dict` of functions defined by the task's `'results_format'`. Example use for calling a `create()` function is `results_functions()['create']()`.                                                                                                                                                                           |
| `RESULT_LOCATION` (outside of `BenchBot` class) | A static string denoting where results should be saved (`/tmp/results`). Using this locations ensures tools in the [BenchBot software stack](https://github.com/qcr/benchbot) work as expected.                                                                                                                          |
