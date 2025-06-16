import numpy as np


class OBJ_Parser:

    def __init__(self, path, normalize = True):
        self.vertex_positions   = []
        self.vertex_indices     = []
        self.normals            = []
        self.normal_indices     = []
        self.uv_positions       = []
        self.uv_indices         = []
        self._parse(path)

        if normalize:
            self._normalize()


    def _parse(self, path):

        with open(path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if not parts or parts[0].startswith('#'):
                    continue

                if parts[0] == 'v':  # Vertex position
                    self.vertex_positions.append([float(x) for x in parts[1:]])

                elif parts[0] == 'vn':  # Normals
                    self.normals.append([float(x) for x in parts[1:]])

                elif parts[0] == 'vt':  # Texture coordinate
                    self.uv_positions.append([float(x) for x in parts[1:3]])

                elif parts[0] == 'f':
                    face_vertices = [v.split('/') for v in parts[1:]]
                    num_vertices = len(face_vertices)

                    # Triangulate the polygon (fan triangulation)
                    for i in range(1, num_vertices - 1):
                        tri = [face_vertices[0], face_vertices[i], face_vertices[i + 1]]
                        for v in tri:
                            vi = int(v[0]) - 1
                            self.vertex_indices.append(vi)

                            if len(v) > 1 and v[1]:
                                ti = int(v[1]) - 1
                                self.uv_indices.append(ti)

                            if len(v) > 1 and v[2]:
                                ti = int(v[2]) - 1
                                self.normal_indices.append(ti)


        # Convert to numpy arrays
        self.vertex_positions   = np.array(self.vertex_positions, dtype=np.float32)
        self.vertex_indices     = np.array(self.vertex_indices, dtype=np.int32)
        self.normals            = np.array(self.normals, dtype=np.float32)
        self.normal_indices     = np.array(self.normal_indices, dtype=np.int32)
        self.uv_positions       = np.array(self.uv_positions, dtype=np.float32)
        self.uv_indices         = np.array(self.uv_indices, dtype=np.int32)


    def _normalize(self):
        # Normalize to fit in [-0.5, 0.5] cube
        if len(self.vertex_positions) > 0:
            min_bounds = np.min(self.vertex_positions, axis=0)
            max_bounds = np.max(self.vertex_positions, axis=0)

            center = (min_bounds + max_bounds) / 2.0
            scale = np.max(max_bounds - min_bounds)

            self.vertex_positions = (self.vertex_positions - center) / scale


    def get_vertex_data(self):
        return self.vertex_positions, self.vertex_indices
    

    def get_normal_data(self):
        return self.normals, self.normal_indices


    def get_uv_data(self):
        return self.uv_positions, self.uv_indices
    