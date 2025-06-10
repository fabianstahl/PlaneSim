from engine.vao import VAO
from engine.texture import Texture
import glm
import numpy as np


class Model:

    def __init__(self, vao, position, scale, texture_path, orbit_deg = 0):
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

    def __init__(self, rotation_speed, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rotation_speed     = rotation_speed


    def update(self):
        self.orbit_deg      += self.rotation_speed
        self.model_matrix   = self.calculate_model_matrix()



class Rocket(Model):

    def __init__(self, rocket_speed, forward, life_time, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rocket_speed   = rocket_speed
        self.forward        = forward
        self.life_time      = life_time
        self.no_updates     = 0


    def update(self):
        self.position      += self.forward * self.rocket_speed
        self.no_updates     += 1
        self.model_matrix   = self.calculate_model_matrix()

    
    def is_destroyable(self):
        return self.no_updates >= self.life_time




class Airplane(Model):
    def __init__(self, min_vel, max_vel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.forward        = glm.vec3(0, 1, 0)
        self.velocity       = 0
        self.acceleration   = 0
        self.min_vel        = min_vel
        self.max_vel        = max_vel


    def accelerate(self, acceleration):
        self.acceleration = acceleration


    def rotate(self, orbit_deg):
        # Rotate around Z axis
        self.orbit_deg      += orbit_deg
        rotation            = glm.rotate(glm.mat4(1.0), glm.radians(self.orbit_deg), glm.vec3(0, 0, 1))
        self.forward        = glm.vec3(rotation * glm.vec4(0, 1, 0, 1.0))
        self.model_matrix   = self.calculate_model_matrix()


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
