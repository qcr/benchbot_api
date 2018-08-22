# BenchBot

BenchBot provides a simple python-based wrapper for use with the QUT cloud-based BenchBot service

```python
from benchbot import BenchBot

benchbot = BenchBot() # Create a benchbot instance

routes = benchbot.get() # Get a list of available routes
commands = benchbot.get('command') # Get a list of possible actions for the command route

image = benchbot.getImage() # Get an image (standard opencv numpy array)
```