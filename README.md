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
