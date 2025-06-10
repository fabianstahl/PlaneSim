import math
import numpy as np

def parse_list(string, dtype):
    return [dtype(x) for x in string.split(",")]

mapWidth    = 2
mapHeight   = 2

def convert_lat_lon(latitude, longitude):
    # get x value
    x = (longitude + 180) * (mapWidth / 360)

    # convert from degrees to radians
    latRad = (latitude * math.pi) / 180

    # get y value
    mercN = np.log(math.tan((math.pi / 4) + (latRad / 2)))
    y     = (mapHeight / 2) - (mapWidth * mercN / (2 * math.pi))
    return x-1, float(1-y)