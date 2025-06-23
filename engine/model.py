from engine.vao import VAO
from engine.texture import Texture
from pyglm import glm
from typing import Any, Dict
from OpenGL.GL import *


# Camera Systemr relative to plane
RIGHT       = glm.vec3(1, 0, 0)     # pitch
FORWARD     = glm.vec3(0, 1, 0)     # roll
UP          = glm.vec3(0, 0, 1)    # yaw

class Model:

    def __init__(self, 
                vao:            VAO,
                position:       glm.vec3, 
                scale:          glm.vec3 | float, 
                texture_path:   str, 
                yaw_deg:        float               = 0, 
                pitch_deg:      float               = 0, 
                roll_deg:       float               = 0):
        self._vao           = vao
        self._position      = position
        self._scale         = glm.vec3(scale)
        self._texture_path  = texture_path

        self._texture:      Texture     = Texture(texture_path)
        self._model_matrix: glm.mat4    = glm.mat4(1.0)
        self._orientation:  glm.quat    = glm.quat()

        self.add_yaw(yaw_deg)
        self.add_pitch(pitch_deg)
        self.add_roll(roll_deg)




    # === Read only Properties ===

    @property
    def model_matrix(self) -> glm.mat4:
        return self._model_matrix


    # === Read / Write Properties ===

    @property
    def position(self) -> glm.vec3:
        return self._position

    @position.setter
    def position(self, position: glm.vec3):
        self._position = position
        self._update_model_matrix()


    @property
    def scale(self) -> glm.vec3:
        return self._scale

    @scale.setter
    def scale(self, scale: glm.vec3 | float):
        self._scale = glm.vec3(scale)
        self._update_model_matrix()
    

    @property
    def orientation(self) -> glm.quat:
        return self._orientation
    
    @orientation.setter
    def orientation(self, orientation: glm.quat):
        self._orientation   = orientation
        self._update_model_matrix()


    # === Private Methods ===

    def _update_model_matrix(self):
        identity            = glm.mat4(1.0)
        model_trans         = glm.translate(identity, self._position)
        model_scale         = glm.scale(identity, self._scale)
        self._model_matrix  = model_trans * glm.mat4_cast(self._orientation) * model_scale * identity


    # === Public Methods ===

    def add_yaw(self, yaw_deg: float):
        yaw_rad             = glm.radians(yaw_deg)
        q_delta             = glm.angleAxis(yaw_rad, self._orientation * UP)
        self._orientation   = q_delta * self._orientation
        self._update_model_matrix()


    def add_pitch(self, pitch_deg: float):
        pitch_rad           = glm.radians(pitch_deg) 
        q_delta             = glm.angleAxis(pitch_rad, self._orientation * RIGHT)
        self._orientation   = q_delta * self._orientation
        self._update_model_matrix()


    def add_roll(self, roll_deg: float):
        roll_rad            = glm.radians(roll_deg)
        q_delta             = glm.angleAxis(roll_rad, self._orientation * FORWARD)
        self._orientation   = q_delta * self._orientation
        self._update_model_matrix()


    def update(self, delta: float):
        pass


    def initializeGL(self, uniform_locations: Dict):
        self._texture.initializeGL()
        self._uniform_locations = uniform_locations

        if not self._vao.initialized:
            self._vao.initializeGL()


    def render(self):
        
        # Every model has at least a model matrix
        glUniformMatrix4fv(self._uniform_locations["model"], 1, GL_FALSE, self._model_matrix.to_bytes())

        self._texture.use()
        self._vao.use()
        self._vao.render()


    def release(self, keep_vao: bool = False):
        if not keep_vao:
            self._vao.release()
        self._texture.release()

    
    def translate(self, offset: glm.vec3 | float):
        self._position += offset

        if self._position.z < 0:
            self._position.z = 0



class Target(Model):

    def __init__(self, rotation_speed: float, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._rotation_speed     = rotation_speed


    def update(self, delta: float):
        self.add_yaw(self._rotation_speed * delta)
        self._update_model_matrix()
        super().update(delta)



class Airplane(Model):

    def __init__(self, min_vel: float, max_vel: float, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        
        self._min_vel       = min_vel
        self._max_vel       = max_vel

        self._velocity:     float   = 0
        self._acceleration: float   = 0


    @property
    def forward(self) -> glm.vec3:
        return glm.normalize(glm.vec3(self._model_matrix[1]))
    

    @property
    def velocity(self) -> float:
        return self._velocity


    def accelerate(self, acceleration: float):
        self._acceleration = acceleration


    def update(self, delta: float):
        
        # Integrate acceleration to velocity
        self._velocity  += self._acceleration * delta

        # Optional: clamp max velocity
        self._velocity  = glm.clamp(self._velocity, self._min_vel, self._max_vel)

        # Integrate velocity to position
        self._position += self.forward * self._velocity * delta

        if self._position.z < 0:
            self._position.z = 0

        self._update_model_matrix()
        super().update(delta)



class ExpirableModel(Model):

    def __init__(self, life_time: int, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._life_time     = life_time
        
        self._no_updates: int = 0


    def update(self, delta: float):
        self._no_updates    += 1
        self._update_model_matrix()
        super().update(delta)


    def is_expired(self) -> bool:
        return self._no_updates >= self._life_time



class Rocket(ExpirableModel):

    def __init__(self, rocket_speed: float, forward: glm.vec3, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._rocket_speed  = rocket_speed
        self._forward       = forward
        

    def update(self, delta: float):
        self._position      += self._forward * self._rocket_speed * delta
        super().update(delta)



class Strip(ExpirableModel):

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)



class MapTile(Model):

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)


    def prepare_tile(x: int, y: int, z: int, vao: VAO):
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