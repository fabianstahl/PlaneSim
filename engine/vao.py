from OpenGL.GL import *
import numpy as np
from engine.primitives import Primitive

class VAO:

    def __init__(self, geometry: Primitive):
        """
        Combines positions and UVs into flat vertex array.
        Assumes face_indices and uv_face_indices have same shape.
        """

        vertices        = geometry.get_vertices()
        uv_vertices     = geometry.get_uv_vertices()    
        face_indices    = geometry.get_vertex_indices()
        uv_face_indices = geometry.get_uv_indices()

        assert face_indices.shape == uv_face_indices.shape, "Mismatched face shapes"

        self.vertex_data = []
        for f_idx, uv_idx in zip(face_indices.flatten(), uv_face_indices.flatten()):
            pos = vertices[f_idx]
            uv = uv_vertices[uv_idx]
            self.vertex_data.append(np.concatenate([pos, uv]))

        self.vertex_data    = np.array(self.vertex_data, dtype=np.float32)
        self.vertex_count   = len(self.vertex_data)


    def initializeGL(self):
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertex_data.nbytes, self.vertex_data, GL_STATIC_DRAW)

        stride = self.vertex_data.shape[1] * self.vertex_data.itemsize
        offset = 0

        # position (vec3)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset))
        glEnableVertexAttribArray(0)
        offset += 3 * self.vertex_data.itemsize

        # texcoords (vec2)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset))
        glEnableVertexAttribArray(1)

        glBindVertexArray(0)


    def use(self):
        glBindVertexArray(self.vao)


    def render(self):
        glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)


    def release(self):
        glDeleteVertexArrays(1, [self.vao])
        glDeleteBuffers(1, [self.vbo])