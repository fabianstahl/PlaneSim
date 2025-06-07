from engine.vao import VAO
from engine.texture import Texture
import glm
import numpy as np


class Model:

    def __init__(self, vertices, indices, position, scale, texture_path):
        self.vertices       = vertices
        self.indices        = indices
        self.position       = position
        self.scale          = scale
        self.texture_path   = texture_path
        self.yaw_rad        = 0
        self.model_matrix   = self.calculate_model_matrix()


    def calculate_model_matrix(self):
        mat = glm.mat4(1.0)
        mat = glm.translate(mat, self.position)
        mat = glm.rotate(mat, glm.radians(self.yaw_rad), glm.vec3(0, 0, 1))  # rotate around Z
        mat = glm.scale(mat, glm.vec3(self.scale))
        return mat


    def initializeGL(self):
        self.vao        = VAO(self.vertices, self.indices)
        self.texture    = Texture(self.texture_path)


    def render(self):
        self.texture.use()
        self.vao.use()
        self.vao.render()


    def release(self):
        self.vao.release()
        self.texture.release()


class Plane(Model):
    def __init__(self, position, scale, texture_path):

        plane_vertices = np.array([
            # positions       # texture coords
            [-0.5,  0.5, 0.0,  0.0, 1.0],  # top-left
            [-0.5, -0.5, 0.0,  0.0, 0.0],  # bottom-left
            [ 0.5, -0.5, 0.0,  1.0, 0.0],  # bottom-right
            [ 0.5,  0.5, 0.0,  1.0, 1.0],  # top-right
        ], dtype=np.float32)

        plane_indices = np.array([
            0, 1, 2,
            0, 2, 3
        ], dtype=np.uint32)

        super().__init__(plane_vertices, plane_indices, position, scale, texture_path)
        
        self.forward        = glm.vec3(0, 1, 0)
        self.velocity       = 0
        self.acceleration   = 0

        self.max_vel        = 0.01
        self.max_acc        = 1


    def accelerate(self, acceleration):
        self.acceleration = acceleration


    def rotate(self, angle_rad):
        # Rotate around Z axis

        self.yaw_rad        += angle_rad
        self.model_matrix   = self.calculate_model_matrix()

        rotation            = glm.rotate(glm.mat4(1.0), glm.radians(self.yaw_rad), glm.vec3(0, 0, 1))
        self.forward        = glm.vec3(rotation * glm.vec4(0, 1, 0, 1.0))


    def update(self, delta):

        # Integrate acceleration to velocity
        self.velocity += self.acceleration * delta

        # Optional: clamp max velocity
        if self.velocity > self.max_vel:
            self.velocity = self.max_vel
        elif self.velocity < 0:
            self.velocity = 0  # Prevent moving backward if you want

        # Integrate velocity to position
        self.position += self.forward * self.velocity * delta

        self.model_matrix = self.calculate_model_matrix()



class MapTile(Model):

    def __init__(self, position, scale, texture_path):

        plane_vertices = np.array([
            # positions       # texture coords
            [-0.5,  0.5, 0.0,  0.0, 1.0],  # top-left
            [-0.5, -0.5, 0.0,  0.0, 0.0],  # bottom-left
            [ 0.5, -0.5, 0.0,  1.0, 0.0],  # bottom-right
            [ 0.5,  0.5, 0.0,  1.0, 1.0],  # top-right
        ], dtype=np.float32)

        plane_indices = np.array([
            0, 1, 2,
            0, 2, 3
        ], dtype=np.uint32)

        super().__init__(plane_vertices, plane_indices, position, scale, texture_path)
