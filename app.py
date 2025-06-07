import sys
import numpy as np
import glm
import configparser as cfg
import utils

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtCore import QTimer, Qt, QElapsedTimer
from OpenGL.GL import *

from engine.shader import Shader, Program
from engine.camera import Camera
from engine.model import MapTile, Airplane
from engine.frustum import Frustum
from engine.vao import VAO
from engine.primitives import Plane



class GLWidget(QOpenGLWidget):

    def __init__(self, configs):
        super().__init__()

        self.configs        = configs

        self.shader_program = None

        self.cam            = Camera(
                    position    = glm.vec3(utils.parse_list(configs["cam_position"], float)),
                    target      = glm.vec3(utils.parse_list(configs["cam_target"], float)),
                    up          = glm.vec3(utils.parse_list(configs["cam_up"], float)),
                    fov_degrees = configs.getfloat("cam_fov"), 
                    aspect      = configs.getint("window_width") / configs.getint("window_height"), 
                    near        = configs.getfloat("cam_near"), 
                    far         = configs.getfloat("cam_far")
        )
        
        self.frustum        = Frustum()
        self.tile_cache     = {}

        plane_geom          = Plane()
        self.tile_vao       = VAO(plane_geom.vertices, plane_geom.indices)

        self.air_plane          = Airplane(
            vao                 = self.tile_vao, 
            position            = glm.vec3(utils.parse_list(configs["plane_position"], float)),
            scale               = configs.getfloat("plane_scale"),
            texture_path        = configs.get("plane_tex_path")
        )

        # 0: points, 1: wireframe, 2: textured
        self.render_mode    = 2     

        # App Timer
        self.timer          = QTimer(self)
        self.timer.timeout.connect(self.update_game)
        self.timer.start(1000 // configs.getint("app_fps"))
        self.elapsed_timer  = QElapsedTimer()
        self.elapsed_timer.start()


    def update_game(self):

        ms = self.elapsed_timer.elapsed()
        self.elapsed_timer.restart()

        delta = ms / 1000.0  # Convert to seconds
        self.air_plane.update(delta)

        new_focus_point = glm.vec3(self.air_plane.position.x, self.air_plane.position.y, 0)
        self.cam.focus(new_focus_point)

        self.update()


    def initializeGL(self):
        bg_color = utils.parse_list(self.configs["clear_color"], float)
        glClearColor(*bg_color)
        glClearDepth(1.0)
        glEnable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPointSize(configs.getfloat("point_size"))

        self.air_plane.initializeGL()
        
        self.tile_vao.initializeGL()

        self.setup_shaders()

        # Get uniform location
        self.model_loc  = self.program.get_uniform_location("model")
        self.view_loc   = self.program.get_uniform_location("view")
        self.proj_loc   = self.program.get_uniform_location("projection")



    def setup_shaders(self):
        vertex_shader   = Shader("shaders/vertex_shader.glsl", GL_VERTEX_SHADER)
        fragment_shader = Shader("shaders/fragment_shader.glsl", GL_FRAGMENT_SHADER)
        self.program    = Program(vertex_shader, fragment_shader)


    def paintGL(self):

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.program.use()

        if self.render_mode == 0:
            glPolygonMode(GL_FRONT_AND_BACK, GL_POINT)
        elif self.render_mode == 1:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        # Upload matrices
        glUniformMatrix4fv(self.view_loc, 1, GL_FALSE, np.array(self.cam.get_view_matrix(), dtype=np.float32).T)
        glUniformMatrix4fv(self.proj_loc, 1, GL_FALSE, np.array(self.cam.get_projection_matrix(), dtype=np.float32).T)

        # Perform Frustum culling
        tile_ids = self.frustum.cull(self.cam.get_projection_matrix() * self.cam.get_view_matrix())
        
        # Add missing tiles
        for (x, y, z) in tile_ids:
            if not (x, y, z) in self.tile_cache:
                center              = 2**z // 2
                scale               = 2 / 2**z
                x_pos               = 2 * (-x + center - 0.5) / 2**z
                y_pos               = 2 * (y - center + 0.5) / 2**z
                position            = glm.vec3(y_pos, x_pos, 0)
                texture_path        = "data/tiles_esri/{}/{}/{}.png".format(z, x, y)
                tile                = MapTile(self.tile_vao, position, scale, texture_path)
                tile.initializeGL()
                self.tile_cache[(x, y, z)] = tile

        # Remove tiles no longer visible
        for key in list(self.tile_cache.keys()):
            if not key in tile_ids:
                self.tile_cache[key].release
                self.tile_cache.pop(key)


        # Render tiles
        for tile in self.tile_cache.values():
            glUniformMatrix4fv(self.model_loc, 1, GL_FALSE, np.array(tile.model_matrix, dtype=np.float32).T)
            tile.render()

        # Render plane
        glUniformMatrix4fv(self.model_loc, 1, GL_FALSE, np.array(self.air_plane.model_matrix, dtype=np.float32).T)
        self.air_plane.render()


    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        self.cam.set_aspect(w/h)


    def release(self):
        self.air_plane.release()
        for tile in self.tile_cache.values():
            tile.release()
        self.program.release()


    def delegate_key_pressed(self, event):
        key = event.key()
        if key == Qt.Key.Key_W:
            self.air_plane.accelerate(0.004)
        elif key == Qt.Key.Key_S:
            self.air_plane.accelerate(-0.004)
        elif key == Qt.Key.Key_A:
            self.air_plane.rotate(1)
        elif key == Qt.Key.Key_D:
            self.air_plane.rotate(-1)
        elif key == Qt.Key.Key_1:
            self.render_mode = 0
        elif key == Qt.Key.Key_2:
            self.render_mode = 1
        elif key == Qt.Key.Key_3:
            self.render_mode = 2
        """
        if key == Qt.Key.Key_W:
            self.cam.translate(glm.vec3(0, 0.1, 0))
        elif key == Qt.Key.Key_S:
            self.cam.translate(glm.vec3(0, -0.1, 0))
        elif key == Qt.Key.Key_A:
            self.cam.translate(glm.vec3(-0.1, 0, 0))
        elif key == Qt.Key.Key_D:
            self.cam.translate(glm.vec3(0.1, 0, 0))
        """



    def delegate_wheel_event(self, event):

        delta       = event.angleDelta().y() / 120  # One step = 120
        zoom_speed  = 0.1 * glm.length(self.cam.position.z) - 0.0001

        # Move camera along its forward direction
        self.cam.zoom(delta * zoom_speed)



    def delegate_mouse_pressed_event(self, event):
        pass

    def delegate_mouse_released_event(self, event):
        pass


    def screen_ray(self, pos):
        x, y = pos.x(), pos.y()
        view = self.cam.get_view_matrix()
        proj = self.cam.get_projection_matrix()
        width, height = self.width(), self.height()

        # Convert to NDC
        x_ndc = (2.0 * x) / width - 1.0
        y_ndc = 1.0 - (2.0 * y) / height

        # Near and far points in view space
        near_point = glm.vec4(x_ndc, y_ndc, -1.0, 1.0)
        far_point  = glm.vec4(x_ndc, y_ndc,  1.0, 1.0)

        inv_projview = glm.inverse(proj * view)
        p_near = inv_projview * near_point
        p_far  = inv_projview * far_point
        p_near /= p_near.w
        p_far  /= p_far.w

        return glm.vec3(p_near), glm.vec3(p_far)


    def delegate_translation(self, start_pos, end_pos):

        ray_start_old, ray_end_old = self.screen_ray(start_pos)
        ray_start_new, ray_end_new = self.screen_ray(end_pos)

        # Intersect both rays with z=0 plane
        def intersect_z0(start, end):
            dir = end - start
            t = -start.z / dir.z
            return start + t * dir

        p_old = intersect_z0(ray_start_old, ray_end_old)
        p_new = intersect_z0(ray_start_new, ray_end_new)

        delta = p_old - p_new

        self.cam.move(delta)



    def delegate_tilt(self, orbit_center, start_pos, end_pos):

        dx = end_pos.x() - start_pos.x()
        dy = end_pos.y() - start_pos.y()

        sensitivity = 0.005  # adjust this to taste
        
        self.cam.tilt(dy * sensitivity)
        #self.cam.orbit(dx * sensitivity)





class MainWindow(QMainWindow):
    def __init__(self, configs):
        super().__init__()

        self.configs = configs

        self.setWindowTitle("PlaneSim")
        self.setGeometry(0, 0, configs.getint("window_width"), configs.getint("window_height"))
        self.gl_widget = GLWidget(configs)
        self.setCentralWidget(self.gl_widget)

        # Variables for user interaction
        self.last_mouse_pos     = None
        self.left_mouse_down    = False
        self.middle_mouse_down  = False
        self.orbit_center       = None


    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.gl_widget.release()
            self.close()
        self.gl_widget.delegate_key_pressed(event)


    def wheelEvent(self, event):
        self.gl_widget.delegate_wheel_event(event)


    def intersect_plane(self, ray_origin, ray_dir, plane_z=0.0):
        t = (plane_z - ray_origin.z) / ray_dir.z
        return ray_origin + t * ray_dir


    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.left_mouse_down    = True
            self.last_mouse_pos     = event.position()
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.middle_mouse_down  = True
            self.last_mouse_pos     = event.position()
            ray_origin, ray_dir     = self.gl_widget.screen_ray(event.position())
            self.orbit_center       = self.intersect_plane(ray_origin, ray_dir, plane_z=0.0)


    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.left_mouse_down    = False
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.middle_mouse_down  = False


    def mouseMoveEvent(self, event):
        if self.left_mouse_down:
            new_pos = event.position()
            self.gl_widget.delegate_translation(self.last_mouse_pos, new_pos)
            self.last_mouse_pos = new_pos
        elif self.middle_mouse_down:
            new_pos = event.position()
            self.gl_widget.delegate_tilt(self.orbit_center, self.last_mouse_pos, new_pos)
            self.last_mouse_pos = new_pos





if __name__ == "__main__":
    app = QApplication(sys.argv)

    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    fmt.setDepthBufferSize(24)
    QSurfaceFormat.setDefaultFormat(fmt)

    parser = cfg.ConfigParser()
    parser.read("configs.ini")
    configs = parser["DEFAULT"]

    window = MainWindow(configs)
    window.show()

    sys.exit(app.exec())