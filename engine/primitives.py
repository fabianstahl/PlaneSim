import numpy as np

class Plane():
    
    def __init__(self):
        self.vertices = np.array([
            # positions       # texture coords
            [-0.5,  0.5, 0.0,  0.0, 1.0],  # top-left
            [-0.5, -0.5, 0.0,  0.0, 0.0],  # bottom-left
            [ 0.5, -0.5, 0.0,  1.0, 0.0],  # bottom-right
            [ 0.5,  0.5, 0.0,  1.0, 1.0],  # top-right
        ], dtype=np.float32)

        self.indices = np.array([
            0, 1, 2,
            0, 2, 3
        ], dtype=np.uint32)


