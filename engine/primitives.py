import numpy as np
from parser import OBJ_Parser
from numpy.typing import NDArray


class Primitive():

    def __init__(self):
        self._vertices          = None
        self._vertex_indices    = None
        self._uv_vertices       = None
        self._uv_indices        = None

    @property
    def vertices(self) -> NDArray[np.float32] | None:
        return self._vertices
    
    @property
    def vertex_indices(self) -> NDArray[np.uint32] | None:
        return self._vertex_indices

    @property
    def uv_vertices(self) -> NDArray[np.float32] | None:
        return self._uv_vertices
    
    @property
    def uv_indices(self) -> NDArray[np.uint32] | None:
        return self._uv_indices
    


class Plane(Primitive):
    
    def __init__(self):
        super().__init__()

        self._vertices      = np.array([
            # [tl, bl, br, tr]
            [-0.5,  0.5, 0.0],
            [-0.5, -0.5, 0.0],
            [ 0.5, -0.5, 0.0],
            [ 0.5,  0.5, 0.0],
        ], dtype=np.float32)

        self._uv_indices   = self._vertex_indices = np.array([
            0, 1, 2,
            0, 2, 3
        ], dtype=np.uint32)

        self._uv_vertices  = np.array([
            # [tl, bl, br, tr]
            [0.0, 1.0],
            [0.0, 0.0],
            [1.0, 0.0], 
            [1.0, 1.0],
        ], dtype=np.float32)




class Cylinder(Primitive):
    def __init__(self, segments: int = 20):
        super().__init__()

        self._segments      = segments
        self._generate_geometry()


    def _generate_geometry(self):
        vertices    = []
        indices     = []
        uv_vertices = []
        uv_indices  = []

        angle_step  = 2 * np.pi / self._segments
        top_z       = 0.5
        bottom_z    = -0.5
        u_step      = 1.0 / self._segments

        # Generate vertex positions
        top_circle_indices      = []
        bottom_circle_indices   = []
        for i in range(self._segments):
            angle   = i * angle_step
            x       = 0.5 * np.cos(angle)
            y       = 0.5 * np.sin(angle)

            # Top
            vertices.append([x, y, top_z])
            top_circle_indices.append(i * 2)

            # Bottom
            vertices.append([x, y, bottom_z])
            bottom_circle_indices.append(i * 2 + 1)

        # Generate uv positions
        for i in range(self._segments):
            u_start = i * u_step
            uv_vertices.append([u_start, 0.0])
            uv_vertices.append([u_start, 1.0])
        uv_vertices.append([1.0, 0.0])
        uv_vertices.append([1.0, 1.0])      
            
        # Generate faces
        for i in range(self._segments):
            next_i          = (i + 1) % self._segments
            top_current     = top_circle_indices[i]
            top_next        = top_circle_indices[next_i]
            bottom_current  = bottom_circle_indices[i]
            bottom_next     = bottom_circle_indices[next_i]

            # First triangle
            indices.extend([top_current, bottom_current, top_next])
            uv_indices.extend([1 + (i*2), (i*2), 3 + (i*2)])
            
            # Second triangle
            indices.extend([top_next, bottom_current, bottom_next])
            uv_indices.extend([3 + (i*2), (i*2), 2 + (i*2)])

        self._vertices          = np.array(vertices, dtype=np.float32)
        self._vertex_indices    = np.array(indices, dtype=np.uint32)
        self._uv_vertices       = np.array(uv_vertices, dtype=np.float32)
        self._uv_indices        = np.array(uv_indices, dtype=np.uint32)



class Sphere(Primitive):

    def __init__(self, lat_divs: int = 4, lon_divs: int = 8):
        super().__init__()

        self._lat_divs = lat_divs
        self._lon_divs = lon_divs
        self._generate_geometry()


    def _generate_geometry(self):

        vertices    = []
        indices     = []
        uv_vertices = []

        for i in range(self._lat_divs + 1):
            theta       = np.pi * i / self._lat_divs
            sin_theta   = np.sin(theta)
            cos_theta   = np.cos(theta)

            for j in range(self._lon_divs + 1):
                phi     = 2 * np.pi * j / self._lon_divs
                sin_phi = np.sin(phi)
                cos_phi = np.cos(phi)

                x = sin_theta * cos_phi * 0.5
                y = cos_theta * 0.5
                z = sin_theta * sin_phi * 0.5

                u = j / self._lon_divs
                v = i / self._lat_divs

                vertices.extend([x, z, y])
                uv_vertices.append([u, v])

        for i in range(self._lat_divs):
            for j in range(self._lon_divs):
                first = i * (self._lon_divs + 1) + j
                second = first + self._lon_divs + 1

                indices.extend([first, second, first + 1])
                indices.extend([second, second + 1, first + 1])

        self._vertices          = np.array(vertices, dtype=np.float32)
        self._vertex_indices    = np.array(indices, dtype=np.uint32)
        self._uv_vertices       = np.array(uv_vertices, dtype=np.float32)
        self._uv_indices        = np.array(indices, dtype=np.uint32)

   

class Cloud(Primitive):

    def __init__(self, min_spheres: int, max_spheres: int, min_radius: float, max_radius: float, max_offset_xy: float, max_offset_z: float):
        super().__init__()

        no_spheres  = np.random.randint(min_spheres, max_spheres)
        radius      = np.random.random(no_spheres) / (max_radius - min_radius) + min_radius
        offset      = np.random.random((no_spheres, 3)) * np.array([max_offset_xy, max_offset_xy, max_offset_z])

        vertices    = []
        indices     = []
        uv_vertices = []

        sphere = Sphere()

        for i in range(no_spheres):
            vert = np.reshape(sphere.vertices, (-1, 3)) * radius[i] + offset[i]
            vertices.extend(vert)
            uv_vertices.extend(sphere.uv_vertices)
            indices.extend(len(vert) * i + sphere.vertex_indices)

        self._vertices          = np.array(vertices, dtype=np.float32)
        self._vertex_indices    = np.array(indices, dtype=np.uint32)
        self._uv_vertices       = np.array(uv_vertices, dtype=np.float32)
        self._uv_indices        = np.array(indices, dtype=np.uint32)



class OBJ(Primitive):

    def __init__(self, obj_path):
        super().__init__()
        
        parser  = OBJ_Parser(obj_path)

        vertices, vertex_indices    = parser.get_vertex_data()
        uv_vertices, uv_indices     = parser.get_uv_data()

        # Rotate according to the simulator geography coordinate system
        vertices        = vertices[:, [1, 0, 2]]      # (x, y) -> (y, x)
        vertices[:,1]   *= -1                         # (x) -> (-x)

        self._vertices          = np.array(vertices, dtype=np.float32)
        self._vertex_indices    = np.array(vertex_indices, dtype=np.uint32)
        self._uv_vertices       = np.array(uv_vertices, dtype=np.float32)
        self._uv_indices        = np.array(uv_indices, dtype=np.uint32)