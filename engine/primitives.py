import numpy as np
from abc import ABC, abstractmethod
from typing import Sequence, List
from parser import OBJ_Parser


class Primitive(ABC):
    @abstractmethod
    def get_vertices(self) -> Sequence[float]:
        pass

    @abstractmethod
    def get_vertex_indices(self) -> Sequence[int]:
        pass

    @abstractmethod
    def get_uv_vertices(self) -> Sequence[int]:
        pass

    @abstractmethod
    def get_uv_indices(self) -> Sequence[int]:
        pass


class Plane(Primitive):
    
    def __init__(self):
        self.vertices = np.array([
            # positions       # texture coords
            [-0.5,  0.5, 0.0],  # top-left
            [-0.5, -0.5, 0.0],  # bottom-left
            [ 0.5, -0.5, 0.0],  # bottom-right
            [ 0.5,  0.5, 0.0],  # top-right
        ], dtype=np.float32)

        self.indices = np.array([
            0, 1, 2,
            0, 2, 3
        ], dtype=np.uint32)

        self.uv_positions = np.array([
            # positions       # texture coords
            [0.0, 1.0],  # top-left
            [0.0, 0.0],  # bottom-left
            [1.0, 0.0],  # bottom-right
            [1.0, 1.0],  # top-right
        ], dtype=np.float32)

    
    def get_vertices(self):
        return self.vertices
    
    def get_vertex_indices(self):
        return self.indices
    
    def get_uv_vertices(self):
        return self.uv_positions

    def get_uv_indices(self):
        return self.indices


class Cylinder(Primitive):
    def __init__(self, segments: int = 20):
        self.segments       = segments
        self.vertices       = []
        self.indices        = []
        self.uv_vertices    = []
        self.uv_indices     = []
        self._generate_geometry()


    def _generate_geometry(self):
        
        angle_step = 2 * np.pi / self.segments

        top_z       = 0.5
        bottom_z    = -0.5


        # --- Side circle vertices ---
        u_step                  = 1.0 / self.segments
        for i in range(self.segments):
            u_start = i * u_step
            self.uv_vertices.append([u_start, 0.0])
            self.uv_vertices.append([u_start, 1.0])
        self.uv_vertices.append([1.0, 0.0])
        self.uv_vertices.append([1.0, 1.0])


        top_circle_indices      = []
        bottom_circle_indices   = []
        for i in range(self.segments):
            angle = i * angle_step
            x = 0.5 * np.cos(angle)
            y = 0.5 * np.sin(angle)

            # Top edge vertex
            self.vertices.append([x, y, top_z])
            top_circle_indices.append(i * 2)

            # Bottom edge vertex
            self.vertices.append([x, y, bottom_z])
            bottom_circle_indices.append(i * 2 + 1)
        
            
        # --- Side indices (as quads split into triangles) ---
        for i in range(self.segments):
            next_i = (i + 1) % self.segments

            top_current     = top_circle_indices[i]
            top_next        = top_circle_indices[next_i]
            bottom_current  = bottom_circle_indices[i]
            bottom_next     = bottom_circle_indices[next_i]

            # First triangle
            self.indices.extend([top_current, bottom_current, top_next])
            self.uv_indices.extend([1 + (i*2), (i*2), 3 + (i*2)])
            
            # Second triangle
            self.indices.extend([top_next, bottom_current, bottom_next])
            self.uv_indices.extend([3 + (i*2), (i*2), 2 + (i*2)])



    def get_vertices(self):
        return np.array(self.vertices, dtype=np.float32)

    def get_vertex_indices(self):
        return np.array(self.indices, dtype=np.uint32)
    
    def get_uv_vertices(self):
        return np.array(self.uv_vertices, dtype=np.float32)

    def get_uv_indices(self):
        return np.array(self.uv_indices, dtype=np.uint32)
    




class Sphere(Primitive):

    def __init__(self, lat_divs: int = 4, lon_divs: int = 8):
        self.lat_divs = lat_divs
        self.lon_divs = lon_divs
        self.vertices = []
        self.uvs = []
        self.indices = []

        self._generate()


    def _generate(self):
        for i in range(self.lat_divs + 1):
            theta = np.pi * i / self.lat_divs
            sin_theta = np.sin(theta)
            cos_theta = np.cos(theta)

            for j in range(self.lon_divs + 1):
                phi = 2 * np.pi * j / self.lon_divs
                sin_phi = np.sin(phi)
                cos_phi = np.cos(phi)

                x = sin_theta * cos_phi * 0.5
                y = cos_theta * 0.5
                z = sin_theta * sin_phi * 0.5

                u = j / self.lon_divs
                v = i / self.lat_divs

                self.vertices.extend([x, z, y])
                self.uvs.append([u, v])

        for i in range(self.lat_divs):
            for j in range(self.lon_divs):
                first = i * (self.lon_divs + 1) + j
                second = first + self.lon_divs + 1

                self.indices.extend([first, second, first + 1])
                self.indices.extend([second, second + 1, first + 1])


    def get_vertices(self):
        return np.array(self.vertices, dtype=np.float32)

    def get_vertex_indices(self):
        return np.array(self.indices, dtype=np.uint32)
    
    def get_uv_vertices(self):
        return np.array(self.uvs, dtype=np.float32)

    def get_uv_indices(self):
        return np.array(self.indices, dtype=np.uint32)
    
    


class Cloud(Primitive):

    def __init__(self, min_spheres, max_spheres, min_radius, max_radius, max_offset_xy, max_offset_z):

        no_spheres  = np.random.randint(min_spheres, max_spheres)
        radius      = np.random.random(no_spheres) / (max_radius - min_radius) + min_radius
        offset      = np.random.random((no_spheres, 3)) * np.array([max_offset_xy, max_offset_xy, max_offset_z])


        self.vertices = []
        self.uvs = []
        self.indices = []

        sphere = Sphere()

        for i in range(no_spheres):
            vertices = np.reshape(sphere.get_vertices(), (-1, 3)) * radius[i] + offset[i]
            self.vertices.extend(vertices)

            self.uvs.extend(sphere.get_uv_vertices())

            self.indices.extend(len(vertices) * i + sphere.get_vertex_indices() )


    def get_vertices(self):
        return np.array(self.vertices, dtype=np.float32)

    def get_vertex_indices(self):
        return np.array(self.indices, dtype=np.uint32)
    
    def get_uv_vertices(self):
        return np.array(self.uvs, dtype=np.float32)

    def get_uv_indices(self):
        return np.array(self.indices, dtype=np.uint32)
    


class OBJ(Primitive):

    def __init__(self, obj_path):
        
        parser = OBJ_Parser(obj_path)

        self.vertex_positions, self.vertex_indices  = parser.get_vertex_data()
        self.uv_positions, self.uv_indices          = parser.get_uv_data()

        # Rotate according to the simulator geography coordinate system
        self.vertex_positions       = self.vertex_positions[:, [1, 0, 2]]   # (x, y) -> (y, x)
        self.vertex_positions[:,1] *= -1                                    # (x) -> (-x)

    def get_vertices(self):
        return self.vertex_positions

    def get_vertex_indices(self):
        return self.vertex_indices

    def get_uv_vertices(self):
        return self.uv_positions

    def get_uv_indices(self):
        return self.uv_indices