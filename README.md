# BenchBot API


The BenchBot API provides a simple interface for controlling and receiving data from a robot or simulator. [Open AI Gym](https://gym.openai.com) users will find the BenchBot API extremely familiar. By taking the hassle out of interfacing with complicated robot systems, you can focus instead on developing and testing your novel algorithms with real robot systems and realistic 3D simulators.

BenchBot is used as part of the ACRV Scene Understanding Challenge. For further details of the challenge see: [https://nikosuenderhauf.github.io/roboticvisionchallenges/scene-understanding] (https://nikosuenderhauf.github.io/roboticvisionchallenges/scene-understanding)

Getting started with a robot using BenchBot is as simple as:

```python
from benchbot_api.benchbot import BenchBot

benchbot = BenchBot() # Create a benchbot instance

action_list = benchbot.actions  # Get a list of available actions
observation_list = benchbot.get('command') # Get a list of observations

# Perform an action, & get observations, reward, info from performing the
# action
observations, reward, info = benchbot.step(action_list[0])
```

For full examples of solutions that use the BenchBot API, see the [benchbot_examples](https://bitbucket.org/acrv/benchbot_examples/src/master/) repository.

## Installation

Use pip to install BenchBot API & dependencies (from inside this repository's root directory):

```bash
pip install .
```

To get the latest published version without cloning this repository, simply:

```bash
pip install benchbot_api
```

## Observations and their format
There are three observations that BenchBot can give. These are:

```python
color_image
depth_image
laserscan
```

`color_image` is a three channel (RGB) image of the environment as seen from the RGB camera on board the robot. `color_image` is a numpy array of HxWx3 with datatype `np.ubyte`.

`depth_image` is a single channel (depth) image of the environment encoding depth data as seen from the depth camera on board the robot. `depth_image` is a numpy array of HxW with datatype `np.double`. Each pixel is the approximate distance from the camera plane of the environment.

`laserscan` is a scan of the environment as taken from the laser scanner on board the robot. `laserscan` has the following properties:

```python
scans
range_min
range_max
```

`scans` is an array of floating point values that encode the depth in metres of the environment of the plane that the laser scanner scans.

`range_min` is the minimum value in the `scans` array.

`range_max` is the maximum value in the `scans` array.


## Actions and their arguments
There are three actions that BenchBot can take. These are:

```python
move_next
move_distance
move_angle
```

`move_next` does not accept any arguments.

`move_distance` accepts one argument, `distance`, which is the distance to travel forward in metres.

`move_angle` accepts one argument, `angle`, which is the angle to rotate in radians.
