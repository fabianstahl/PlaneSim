from engine.vao import VAO
from engine.texture import Texture
import glm
import numpy as np


class Model:

    def __init__(self, vao, position, scale, texture_path, orbit_deg):
        self.vao            = vao
        self.position       = position
        self.scale          = scale
        self.texture_path   = texture_path
        self.orbit_deg      = orbit_deg
        self.model_matrix   = self.calculate_model_matrix()


    def calculate_model_matrix(self):
        mat = glm.mat4(1.0)
        mat = glm.translate(mat, self.position)
        mat = glm.rotate(mat, glm.radians(self.orbit_deg), glm.vec3(0, 0, 1))  # rotate around Z
        mat = glm.scale(mat, glm.vec3(self.scale))
        return mat


    def update(self):
        print("Nothing to update")
        pass



    def initializeGL(self):
        self.texture    = Texture(self.texture_path)


    def render(self):
        self.texture.use()
        self.vao.use()
        self.vao.render()


    def release(self):
        self.vao.release()
        self.texture.release()



class Target(Model):

    def __init__(self, vao, position, scale, texture_path, orbit_deg, rotation_speed):

        super().__init__(vao, position, scale, texture_path, orbit_deg)

        self.rotation_speed     = rotation_speed

    def update(self):
        self.orbit_deg      += self.rotation_speed
        self.model_matrix   = self.calculate_model_matrix()



class Airplane(Model):
    def __init__(self, vao, position, scale, texture_path, orbit_deg):

        super().__init__(vao, position, scale, texture_path, orbit_deg)
        
        self.forward        = glm.vec3(0, 1, 0)
        self.velocity       = 0
        self.acceleration   = 0

        self.max_vel        = 0.04
        self.min_vel        = 0.005


    def accelerate(self, acceleration):
        self.acceleration = acceleration


    def rotate(self, orbit_deg):
        # Rotate around Z axis

        self.orbit_deg      += orbit_deg
        self.model_matrix   = self.calculate_model_matrix()

        rotation            = glm.rotate(glm.mat4(1.0), glm.radians(self.orbit_deg), glm.vec3(0, 0, 1))
        self.forward        = glm.vec3(rotation * glm.vec4(0, 1, 0, 1.0))


    def update(self, delta):

        # Integrate acceleration to velocity
        self.velocity += self.acceleration * delta

        # Optional: clamp max velocity
        if self.velocity > self.max_vel:
            self.velocity = self.max_vel
        elif self.velocity < self.min_vel:
            self.velocity = self.min_vel  # Prevent moving backward if you want

        # Integrate velocity to position
        self.position += self.forward * self.velocity * delta

        self.model_matrix = self.calculate_model_matrix()



class MapTile(Model):

    def __init__(self, vao, position, scale, texture_path, orbit_deg):

        super().__init__(vao, position, scale, texture_path, orbit_deg)
