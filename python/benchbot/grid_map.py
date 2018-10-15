
class GridMap(object):
    def __init__(self, info, data, header=None):
        self.info = info
        self.data = data

    def width(self):
        return self.info['width']

    def height(self):
        return self.info['height']

    def resolution(self):
        return self.info['resolution']

    def getFromMetric(self, x, y):
        x, y = self.toGrid(x, y)
        return self.getFromGrid(x, y)

    def getFromGrid(self, x, y):
        if 0 > x >= self.width(): return float('inf')
        if 0 > y >= self.height(): return float('inf')
        
        index = self.width() * y + x
        if len(self.data) <= index: return float('inf')
        
        return self.data[index]

    def toGrid(self, x, y):
        x = int(x / self.resolution())
        y = int(y / self.resolution())
        return (x, y)

    def toMetric(self, x, y):
        x = x * self.resolution()
        y = y * self.resolution()
        return (x, y)