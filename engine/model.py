from engine.vao import VAO
from engine.texture import Texture
import glm
import numpy as np

# Camera Systemr elative to plane
RIGHT       = glm.vec3(1, 0, 0)     # pitch
FORWARD     = glm.vec3(0, 1, 0)     # roll
UP          = glm.vec3(0, 0, 1)    # yaw

class Model:

    def __init__(self, vao, position, scale, texture_path, yaw_deg = 0, pitch_deg = 0, roll_deg = 0):
        self.vao            = vao
        self.position       = position
        self.scale          = scale
        self.model_matrix   = glm.mat4(1.0)
        self.orientation    = glm.quat()

        self.add_yaw(glm.radians(yaw_deg))
        self.add_pitch(glm.radians(pitch_deg))
        self.add_roll(glm.radians(roll_deg))

        self._update_model_matrix()

        self.texture        = Texture(texture_path)


    def _update_model_matrix(self):
        
        identity        = glm.mat4(1.0)

        # Translation
        model_trans     = glm.translate(identity, self.position)

        # Scale
        model_scale     = glm.scale(identity, glm.vec3(self.scale))

        #self.model_matrix = model_trans * model_roll * model_pitch * model_yaw * model_scale * model
        self.model_matrix = model_trans * glm.mat4_cast(self.orientation) * model_scale * identity


    def add_yaw(self, yaw_deg):
        yaw_rad     = glm.radians(yaw_deg)
        q_delta     = glm.angleAxis(yaw_rad, self.orientation * UP)
        self.orientation = q_delta * self.orientation
        self._update_model_matrix()


    def add_pitch(self, pitch_deg):
        pitch_rad   = glm.radians(pitch_deg) 
        q_delta     = glm.angleAxis(pitch_rad, self.orientation * RIGHT)
        self.orientation = q_delta * self.orientation
        self._update_model_matrix()


    def add_roll(self, roll_deg):
        roll_rad    = glm.radians(roll_deg)
        q_delta     = glm.angleAxis(roll_rad, self.orientation * FORWARD)
        self.orientation = q_delta * self.orientation
        self._update_model_matrix()


    def set_orientation(self, orientation):
        self.orientation = orientation
        self._update_model_matrix()


    def update(self):
        print("Nothing to update")
        pass


    def initializeGL(self):
        self.texture.initializeGL()


    def render(self):
        self.texture.use()
        self.vao.use()
        self.vao.render()


    def release(self):
        self.vao.release()
        self.texture.release()

    
    def translate(self, offset):
        self.position += offset

        if self.position.z < 0:
            self.position.z = 0



class Target(Model):

    def __init__(self, rotation_speed, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rotation_speed     = rotation_speed


    def update(self):
        self.add_yaw(self.rotation_speed)
        self._update_model_matrix()



class Rocket(Model):

    def __init__(self, rocket_speed, forward, life_time, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rocket_speed   = rocket_speed
        self.forward        = forward
        self.life_time      = life_time
        self.no_updates     = 0


    def update(self):
        self.position       += self.forward * self.rocket_speed
        self.no_updates     += 1
        self._update_model_matrix()

    
    def is_destroyable(self):
        return self.no_updates >= self.life_time
    


class Strip(Model):

    def __init__(self, life_time, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.life_time      = life_time
        self.no_updates     = 0


    def update(self):
        self.no_updates     += 1
        self._update_model_matrix()

    
    def is_destroyable(self):
        return self.no_updates >= self.life_time



class Airplane(Model):

    def __init__(self, min_vel, max_vel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.velocity       = 0
        self.acceleration   = 0
        self.min_vel        = min_vel
        self.max_vel        = max_vel


    def get_forward(self):
        return glm.normalize(glm.vec3(self.model_matrix[1]))


    def accelerate(self, acceleration):
        self.acceleration = acceleration


    def update(self, delta):
        
        # Integrate acceleration to velocity
        self.velocity += self.acceleration * delta

        # Optional: clamp max velocity
        if self.velocity > self.max_vel:
            self.velocity = self.max_vel
        elif self.velocity < self.min_vel:
            self.velocity = self.min_vel  # Prevent moving backward if you want

        # Integrate velocity to position
        forward        = glm.normalize(glm.vec3(self.model_matrix[1]))
        self.position += forward * self.velocity * delta

        self._update_model_matrix()



class MapTile(Model):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def prepare_tile(x, y, z, vao):
        center      = 2**z // 2
        scale       = 2 / 2**z
        x_pos       = 2 * (-x + center - 0.5) / 2**z
        y_pos       = 2 * (y - center + 0.5) / 2**z
        position    = glm.vec3(y_pos, x_pos, 0)
        texture_path= f"data/tiles_esri/{z}/{x}/{y}.png"

        tile = MapTile(
            vao          = vao,
            position     = position,
            scale        = scale,
            texture_path = texture_path
        )
        return (x, y, z, tile)