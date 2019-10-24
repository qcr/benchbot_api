# BenchBot API


The BenchBot API provides a simple interface for controlling and receiving data from a robot or simulator. [Open AI Gym](https://gym.openai.com) users will find the BenchBot API extremely familiar. By taking the hassle out of interfacing with complicated robot systems, you can focus instead on developing and testing your novel algorithms with real robot systems and realistic 3D simulators.

BenchBot is used as part of the ACRV Scene Understanding Challenge. For further details of the challenge see: [https://nikosuenderhauf.github.io/roboticvisionchallenges/scene-understanding] (https://nikosuenderhauf.github.io/roboticvisionchallenges/scene-understanding)

Getting started with a robot using BenchBot is as simple as:

```python
from benchbot import BenchBot

benchbot = BenchBot() # Create a benchbot instance

routes = benchbot.get() # Get a list of available routes
commands = benchbot.get('command') # Get a list of possible actions for the command route

image = benchbot.getImage() # Get an image (standard opencv numpy array)
```
