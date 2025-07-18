from OpenGL.GL import *
import numpy as np
from engine.primitives import Primitive

class VAO:

    def __init__(self, geometry: Primitive):
        """
        Combines positions and UVs into flat vertex array.
        Assumes face_indices and uv_face_indices have same shape.
        """

        vertices        = geometry.vertices
        uv_vertices     = geometry.uv_vertices   
        face_indices    = geometry.vertex_indices
        uv_face_indices = geometry.uv_indices

        assert face_indices.shape == uv_face_indices.shape, "Mismatched face shapes"

        vertex_data = []
        for f_idx, uv_idx in zip(face_indices.flatten(), uv_face_indices.flatten()):
            pos = vertices[f_idx]
            uv  = uv_vertices[uv_idx]
            vertex_data.append(np.concatenate([pos, uv]))

        self._vertex_data   = np.array(vertex_data, dtype=np.float32)
        self._vertex_count  = len(self._vertex_data)
        self._initialized   = False


    @property
    def initialized(self) -> bool:
        return self._initialized


    def initializeGL(self):
        self._vao = glGenVertexArrays(1)
        self._vbo = glGenBuffers(1)

        glBindVertexArray(self._vao)
        glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
        glBufferData(GL_ARRAY_BUFFER, self._vertex_data.nbytes, self._vertex_data, GL_STATIC_DRAW)

        stride = self._vertex_data.shape[1] * self._vertex_data.itemsize
        offset = 0

        # position (vec3)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset))
        glEnableVertexAttribArray(0)
        offset += 3 * self._vertex_data.itemsize

        # texcoords (vec2)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset))
        glEnableVertexAttribArray(1)

        glBindVertexArray(0)

        self._initialized = True


    def use(self):
        glBindVertexArray(self._vao)


    def render(self):
        glDrawArrays(GL_TRIANGLES, 0, self._vertex_count)


    def release(self):
        glDeleteVertexArrays(1, [self._vao])
        glDeleteBuffers(1, [self._vbo])