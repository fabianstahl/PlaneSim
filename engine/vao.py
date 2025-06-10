from OpenGL.GL import *

class VAO:

    def __init__(self, vertices, indices):

        self.vertices       = vertices
        self.indices        = indices


    def initializeGL(self):
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self.ebo = glGenBuffers(1)

        glBindVertexArray(self.vao)

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)

        print(self.indices.nbytes, self.vertices.itemsize)

        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * self.vertices.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * self.vertices.itemsize, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        glBindVertexArray(0)


    def use(self):
        glBindVertexArray(self.vao)

    def render(self):
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)

    def release(self):
        glDeleteVertexArrays(1, [self.vao])
        glDeleteBuffers(1, [self.vbo])
        glDeleteBuffers(1, [self.ebo])