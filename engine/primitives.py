import numpy as np
from abc import ABC, abstractmethod
from typing import Sequence, List


class Primitive(ABC):
    @abstractmethod
    def get_vertices(self) -> Sequence[float]:
        pass

    @abstractmethod
    def get_indices(self) -> Sequence[int]:
        pass



class Plane(Primitive):
    
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

    
    def get_vertices(self):
        return self.vertices
    

    def get_indices(self):
        return self.indices



class Cylinder(Primitive):
    def __init__(self, segments: int = 8):
        self.segments   = segments
        self.vertices   = []
        self.indices    = []
        self._generate_geometry()


    def _generate_geometry(self):
        
        angle_step = 2 * np.pi / self.segments

        top_z = 0.5
        bottom_z = -0.5

        # --- Center vertices ---
        top_center_index = 0
        bottom_center_index = 1
        self.vertices.append([0.0, 0.0, top_z, 1.0, 1.0])     # top center
        self.vertices.append([0.0, 0.0, bottom_z, 0.0, 0.0])  # bottom center
        
        # --- Side circle vertices ---
        top_circle_indices = []
        bottom_circle_indices = []

        for i in range(self.segments):
            angle = i * angle_step
            x = 0.5 * np.cos(angle)
            y = 0.5 * np.sin(angle)

            # Top edge vertex
            self.vertices.append([x, y, top_z, 1.0, 1.0])
            top_circle_indices.append(2 + i * 2)

            # Bottom edge vertex
            self.vertices.append([x, y, bottom_z, 0.0, 0.0])
            bottom_circle_indices.append(2 + i * 2 + 1)
        
        # --- Top face indices ---
        for i in range(self.segments):
            next_i = (i + 1) % self.segments
            self.indices.extend([
                top_center_index,
                top_circle_indices[i],
                top_circle_indices[next_i],
            ])
        
        # --- Bottom face indices ---
        for i in range(self.segments):
            next_i = (i + 1) % self.segments
            self.indices.extend([
                bottom_center_index,
                bottom_circle_indices[i],
                bottom_circle_indices[next_i]
            ])
        
        # --- Side indices (as quads split into triangles) ---
        for i in range(self.segments):
            next_i = (i + 1) % self.segments

            top_current = top_circle_indices[i]
            top_next = top_circle_indices[next_i]
            bottom_current = bottom_circle_indices[i]
            bottom_next = bottom_circle_indices[next_i]

            # First triangle
            self.indices.extend([top_current, bottom_current, top_next])
            
            # Second triangle
            self.indices.extend([top_next, bottom_current, bottom_next])
        


    def get_vertices(self):
        return np.array(self.vertices, dtype=np.float32)


    def get_indices(self):
        return np.array(self.indices, dtype=np.uint32)