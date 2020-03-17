**NOTE: this software needs to interface with a running instance of the BenchBot Software Stack. Unless you are running against a remote stack / robot, please install this software with the BenchBot Software Stack as described [here](https://github.com/RoboticVisionOrg/benchbot).**

# BenchBot API

![benchbot_api](./docs/benchbot_api_web.gif)

The BenchBot API provides a simple interface for controlling a robot or simulator through actions, and receiving data through observations. As is shown above, the entire code required for running an agent in a realistic 3D simulator is only 20 lines!

[Open AI Gym](https://gym.openai.com) users will find the breakdown into actions, observations, and steps extremely familiar. BenchBot API aims to allow researchers to develop and testing novel algorithms with real robot systems and realistic 3D simulators, without the typical hassles arising when interfacing with complicated multi-component robot systems.

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

    def save_result(self, filename, empty_results):
        # Save some dummy results
        with open(filename, 'w') as f:
            json.dump(empty_results, f)
```

If you prefer to do things manually, a more exhaustive suite of functions are also available as part of the BenchBot API. Instead of using the `BenchBot.run()` method, a large number of methods can be performed directly through the API. Below highlights a handful of the capabilities of BenchBot API:

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

# Move to the next pose if we are in passive mode
if 'passive' == b.task_details['control_mode']:
    observations, action_result = b.step('move_next')

# Save some empty results
with open(RESULT_LOCATION, 'w') as f:
    json.dump(b.empty_results(), f)
```

For full examples of solutions that use the BenchBot API, see the [benchbot_examples](https://github.com/RoboticVisionOrg/benchbot_examples) repository.

## Installing BenchBot API

BenchBot API is a Python package, installable with pip. Run the following in the root directory of where this repository was cloned:

```
u@pc:~$ pip install .
```

## Using the API to communicate with a robot

Communication with the robot comes through a series of "channels" which are defined by the BenchBot [supervisor](https://github.com/RoboticVisionOrg/benchbot_supervisor). The supervisor also defines whether the channel is an observation from a sensor, or an action executed by a robot actuator (like a motor). The BenchBot API abstracts all of the underlying communication configurations away from the user, so they can simply focus on getting observations & sending actions.

Sending an action to the robot simply requires calling the `BenchBot.step()` method with a valid action (found by checking the `BenchBot.actions` property):

```python
from benchbot_api import BenchBot

b = BenchBot()
available_actions = b.actions
b.step(b.actions[0], {'action_arg:', arg_value})  # Perform the first available action
```

The second parameter is a dictionary of named arguments for the selected action. For example, moving 5m forward with the `'move_distance'` action is represented by the dictionary `{'distance': 5}`. A full list of actions & arguments for the default channel set is shown below.

Observations are simply received as return values from a function call (`BenchBot.reset()` calls `BenchBot.step(None)` which means don't perform an action):

```python
from benchbot_api import BenchBot

b = BenchBot()
observations, action_result = b.reset()
observations, action_result = b.step('move_distance', {'distance': 5})
```
The returned `observations` variable holds a dictionary with key-value pairs corresponding to the name-data defined by each observation channel. A full list of observation channels for the default channel set is provided below.

### Default Communication Channel List

#### Action Channels:

| Name | Required Arguments | Description |
|------|:------------------:|-------------|
|`'move_next'` | `None` | Moves the robot to the next pose in its list of pre-defined poses (only available in passive mode). |
|`'move_distance'` | <pre>{'distance': float}</pre> | Moves the robot `'distance'` metres directly ahead (only available in active mode). |
|`'move_angle'` | <pre>{'angle': float}</pre> | Rotate the angle on the spot by `'angle'` degrees (only available in active mode). |

#### Observation Channels:

| Name | Data format | Description |
|------|:------------|-------------|
|`'image_depth'` | <pre>numpy.ndarray(shape=(H,W),<br>              dtype='float32')</pre> | Depth image from the default image sensor with depths in meters. |
|`'image_depth_info'` | <pre>{<br> 'frame_id': string<br> 'height': int<br> 'width': int<br> 'matrix_instrinsics':<br>     numpy.ndarray(shape=(3,3),<br>                   dtype='float64')<br>'matrix_projection':<br>     numpy.ndarray(shape=(3,4)<br>                   dtype='float64')<br>}</pre> | Sensor information for the depth image. See [here](http://docs.ros.org/melodic/api/sensor_msgs/html/msg/CameraInfo.html) for further information on fields (the `K` matrix is `'matrix_instrinsics'`, & `P` is `'matrix_projection'`). |
|`'image_rgb'` | <pre>numpy.ndarray(shape=(H,W,3),<br>              dtype='uint8')</pre> | RGB image from the default image sensor with colour values mapped to the 3 channels, in the 0-255 range. |
|`'image_rgb_info'` | <pre>{<br> 'frame_id': string<br> 'height': int<br> 'width': int<br> 'matrix_instrinsics':<br>     numpy.ndarray(shape=(3,3),<br>                   dtype='float64')<br>'matrix_projection':<br>     numpy.ndarray(shape=(3,4)<br>                   dtype='float64')<br>}</pre> | Sensor information for the RGB image. See [here](http://docs.ros.org/melodic/api/sensor_msgs/html/msg/CameraInfo.html) for further information on fields (the `K` matrix is `'matrix_instrinsics'`, & `P` is `'matrix_projection'`). |
|`'laser'` | <pre>{<br> 'range_max': float64,<br> 'range_min': float64,<br> 'scans':<br>     numpy.ndarray(shape=(N,2),<br>                   dtype='float64')<br>}</pre> | Set of scan values from a laser sensor, between `'range_min'` & `'range_max'` (in meters). The `'scans'` array consists of `N` scans of format `[scan_angle, scan_value]`. For example, `scans[100,0]` would get the angle of the 100th scan & `scans[100,1]` would get the distance value. |
|`'poses'` | <pre>{<br> ...<br> 'frame_name': {<br>     'parent_frame': string<br>     'rotation_rpy':<br>       numpy.ndarray(shape=(3,),<br>                     dtype='float64')<br>     'rotation_xyzw':<br>       numpy.ndarray(shape=(4,),<br>                     dtype='float64')<br>     'translation_xyz':<br>       numpy.ndarray(shape=(3,),<br>                     dtype='float64')<br> }<br> ...<br>}</pre> | Dictionary of relative poses for the current system state. The pose of each system component is available at key `'frame_name'`. Each pose has a `'parent_frame'` which the pose is relative to (all poses are typically with respect to global `'map'` frame), & the pose values. `'rotation_rpy'` is `[roll,pitch,yaw]`, `'rotation_xyzw'` is the equivalent quaternion `[x,y,z,w]`, & `'translation_xyz'` is the Cartesion `[x,y,z]` coordinates.


## Using the API to communicate with the BenchBot system

TODO
