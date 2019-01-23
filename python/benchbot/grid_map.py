
class GridMap(object):
  def __init__(self, info, data, header=None):
    """GridMap constructor
    
    Args:
      info (dict): A dictionary describing the structure of the grid map (e.g. width/height)
      data (list): A 1D array containing the cost values for the occupancy grid
      header (dict, optional): Not currently used.
    """
    self.info = info
    self.data = data

  def width(self):
    """Retrieves the width of the grid map. 
    
    Returns:
      int: The width of the map.
    """
    return self.info['width']

  def height(self):
    """Retrieves the height of the grid map. 
    
    Returns:
      int: The height of the map.
    """
    return self.info['height']

  def resolution(self):
    """Retrieves the resolution of the grid map, i.e. the size of a pixel to real-world square meters. 
    
    Returns:
      int: The resolution of the map.
    """
    return self.info['resolution']

  def getFromMetric(self, x, y):
    """Retrieves the cost value from the grid map associated with a point in metric space. 
    
    Args:
      x (float): The x coordinate of the point in metric space expressed in meters.
      y (float): The y coordinate of the point in metric space expressed in meters.

    Returns:
      float: The cost value at position (x,y) in metric space. infinite if outside of the grid.
    """
    x, y = self.toGrid(x, y)
    return self.getFromGrid(x, y)

  def getFromGrid(self, x, y):
    """Retrieves the cost value from the grid map associated with a point in grid space. 
    
    Args:
      x (int): The x coordinate of the point in grid space.
      y (int): The y coordinate of the point in grid space.

    Returns:
      float: The cost value at position (x,y) in grid space. infinite if outside of the grid.
    """
    if 0 > x >= self.width(): return float('inf')
    if 0 > y >= self.height(): return float('inf')
    
    index = self.width() * y + x
    if len(self.data) <= index: return float('inf')
    
    return self.data[index]

  def toGrid(self, x, y):
    """Convenience function for converting metric coordinates to grid coordinates. 
    
    Args:
      x (int): The x coordinate of the point in metric space.
      y (int): The y coordinate of the point in metric space.

    Returns:
      tuple: A 2-tuple (x,y) derived from the input arguments and resolution of the map.
    """
    x = int(x / self.resolution())
    y = int(y / self.resolution())
    return (x, y)

  def toMetric(self, x, y):
    """Convenience function for converting grid coordinates to metric coordinates. 
    
    Args:
      x (int): The x coordinate of the point in grid space.
      y (int): The y coordinate of the point in grid space.

    Returns:
      tuple: A 2-tuple (x,y) derived from the input arguments and resolution of the map.
    """
    x = x * self.resolution()
    y = y * self.resolution()
    return (x, y)