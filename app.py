import sys
import numpy as np
import glm
import configparser as cfg
import utils
import numpy as np
from typing import Tuple

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QSurfaceFormat, QPainter, QColor, QFont
from PyQt6.QtCore import QTimer, Qt, QElapsedTimer
from OpenGL.GL import *

from engine.shader import Shader, Program
from engine.game_logic import GameLogic
import geometry as geom

RENDER_MODES = {0: GL_POINT, 1:GL_LINE, 2:GL_FILL}

class GLWidget(QOpenGLWidget):

    def __init__(self, configs: cfg.SectionProxy):
        super().__init__()

        self.configs        = configs
        self.program        = None

        self.logic          = GameLogic(configs)

        # 0: points, 1: wireframe, 2: textured
        self.render_mode    = 2     

        # App Timers
        self.timer          = QTimer(self)
        self.timer.timeout.connect(self.update_logic)
        self.timer.start(1000 // configs.getint("app_fps"))
        self.elapsed_timer  = QElapsedTimer()
        self.elapsed_timer.start()

        self._fps           = 0
        self.fps_timer      = QTimer(self)
        self.fps_timer.timeout.connect(self._print_fps)
        self.fps_timer.start(1000)


    # === Private GL Helper Methods ===

    def _print_fps(self):
        print("FPS: {}".format(self._fps))
        self._fps = 0


    def _setup_initial_rendering(self):
        bg_color = utils.parse_list(self.configs["clear_color"], float)
        glClearColor(*bg_color)
        glClearDepth(1.0)
        glPointSize(self.configs.getfloat("point_size"))


    def _setup_shaders(self):
        vertex_shader   = Shader("shaders/vertex_shader.glsl", GL_VERTEX_SHADER)
        fragment_shader = Shader("shaders/fragment_shader.glsl", GL_FRAGMENT_SHADER)
        self.program    = Program(vertex_shader, fragment_shader)


    def _setup_render_step(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPolygonMode(GL_FRONT_AND_BACK, RENDER_MODES[self.render_mode])
        glEnable(GL_DEPTH_TEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Set Uniform attributes that are not changed in rendering loop
        glUniformMatrix4fv(self._uniform_locations["view"], 1, GL_FALSE, self.logic.camera.view_matrix.to_bytes())
        glUniformMatrix4fv(self._uniform_locations["projection"], 1, GL_FALSE, self.logic.camera.projection_matrix.to_bytes())
        glUniform1f(self._uniform_locations["alpha"], 1.0)


    def _enable_opaque_rendering(self):
        glDisable(GL_BLEND)
        glDepthMask(GL_TRUE)
        glEnable(GL_CULL_FACE)


    def _enable_transparent_rendering_cull(self):
        glEnable(GL_BLEND)
        glDepthMask(GL_FALSE)  # Don't write to depth, but still use it
        glEnable(GL_CULL_FACE)


    def _enable_transparent_rendering_no_cull(self):
        glEnable(GL_BLEND)
        glDepthMask(GL_FALSE)  # Don't write to depth, but still use it
        glDisable(GL_CULL_FACE)


    # === Private Key Interaction Methods ===

    def _zoom(self, direction: int):
        """
        Zoom in or out based on direction.
        :param direction: -1 for zoom in, +1 for zoom out
        """
        zoom_factor = self.configs.getfloat("cam_zoom_factor")  
        min_dist    = self.configs.getfloat("cam_zoom_min")

        if direction < 0:
            # Zoom in (move closer): reduce distance
            self.logic.camera.distance *= (1 - zoom_factor)
            self.logic.camera.distance = max(self.logic.camera.distance, min_dist)
        elif direction > 0:
            # Zoom out (move further): increase distance
            self.logic.camera.distance *= (1 + zoom_factor)


    # === Public Methods ===

    def update_logic(self):
        delta      = self.elapsed_timer.elapsed() / 1000.0
        self.elapsed_timer.restart()
        self.logic.update(delta)    # Trigger Logic
        self.update()               # Trigger UI
        self._fps += 1


    def initializeGL(self):
        self._setup_initial_rendering()
        self._setup_shaders()

        # Get uniform location
        uniform_names       = ["model", "view", "projection", "alpha"]
        uniform_locations   = {name: self.program.get_uniform_location(name) for name in uniform_names}
        self._uniform_locations = uniform_locations

        # Initialize models and link uniform locations
        self.logic.initializeGL(uniform_locations)


    def paintGL(self):
        self.program.use()
        self._setup_render_step()    

        # === Stage 1: Render opaque objects ===
        self._enable_opaque_rendering()

        # Load required Map Tiles
        self.logic.map_tile_check()

        for obj in [self.logic.air_plane] + self.logic.enemies + self.logic.tiles:
            obj.render()      

        # === Stage 2: Render Semi-Transparent objects ===
        self._enable_transparent_rendering_cull()
        for obj in self.logic.bl_clouds + self.logic.wh_clouds + self.logic.targets:
            obj.render()

        # === Stage 3: Render Semi-Transparent objects without face culling ===
        self._enable_transparent_rendering_no_cull()
        for obj in self.logic.rockets + self.logic.strips:
            obj.render()

        # === Stage 4: Render Overlays ===
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setPen(QColor(255, 120, 128))
        painter.setFont(QFont("Arial", 30))
        text    = "Reach '{}, {}'".format(self.logic.mission.target.name, self.logic.mission.target.country)
        width   = painter.fontMetrics().horizontalAdvance(text)
        x_pos   = configs.getint("window_width") // 2 - width // 2
        y_pos   = configs.getint("window_height") - 20
        painter.drawText(x_pos, y_pos, text)
        painter.end()
        

    def resizeGL(self, w: int, h: int):
        glViewport(0, 0, w, h)
        self.logic.camera.aspect = w/h


    def release(self):
        self.program.release()
        self.logic.release()


    def delegate_key_released(self, key: Qt.Key):
        if key in [Qt.Key.Key_W, Qt.Key.Key_S, Qt.Key.Key_Shift]:
            self.logic.air_plane.accelerate(0)


    def delegate_key_pressed(self, key: Qt.Key):
        key_actions = {
            # Airplane Controlls
            Qt.Key.Key_W:           lambda: self.logic.air_plane.accelerate(self.configs.getfloat("plane_gas_acc")),
            Qt.Key.Key_S:           lambda: self.logic.air_plane.accelerate(self.configs.getfloat("plane_brake_acc")),
            Qt.Key.Key_A:           lambda: self.logic.air_plane.add_yaw(self.configs.getfloat("plane_yaw_offset")),
            Qt.Key.Key_D:           lambda: self.logic.air_plane.add_yaw(-self.configs.getfloat("plane_yaw_offset")),
            Qt.Key.Key_Shift:       lambda: self.logic.air_plane.accelerate(self.configs.getfloat("plane_nitro_acc")),
            Qt.Key.Key_Up:          lambda: self.logic.air_plane.add_pitch(-self.configs.getfloat("plane_pitch_offset")),
            Qt.Key.Key_Down:        lambda: self.logic.air_plane.add_pitch(self.configs.getfloat("plane_pitch_offset")),
            Qt.Key.Key_Left:        lambda: self.logic.air_plane.add_roll(-self.configs.getfloat("plane_roll_offset")),
            Qt.Key.Key_Right:       lambda: self.logic.air_plane.add_roll(self.configs.getfloat("plane_roll_offset")),
            Qt.Key.Key_Space:       lambda: self.logic.add_rocket(),

            # Camera Controlls
            Qt.Key.Key_PageUp:      lambda: self.logic.camera.add_tilt(-self.configs.getfloat("cam_tilt_offset")),
            Qt.Key.Key_PageDown:    lambda: self.logic.camera.add_tilt(self.configs.getfloat("cam_tilt_offset")),
            Qt.Key.Key_Plus:        lambda: self._zoom(-1),
            Qt.Key.Key_Minus:       lambda: self._zoom(1),

            # Render Controlls
            Qt.Key.Key_1:           lambda: setattr(self, "render_mode", 0),
            Qt.Key.Key_2:           lambda: setattr(self, "render_mode", 1),
            Qt.Key.Key_3:           lambda: setattr(self, "render_mode", 2),
        }

        action = key_actions.get(key)
        if action:
            action()

        if key in [Qt.Key.Key_W, Qt.Key.Key_Shift]:
            if not self.logic.in_air:
                self.logic.in_air = True


    def delegate_wheel_event(self, event):
        self._zoom(-1 if event.angleDelta().y() > 0 else 1)


    def screen_ray(self, pos) -> Tuple[glm.vec3, glm.vec3]:
        x, y            = pos.x(), pos.y()
        view            = self.logic.camera.view_matrix
        proj            = self.logic.camera.projection_matrix
        width, height   = self.width(), self.height()

        # Convert to NDC
        x_ndc           = (2.0 * x) / width - 1.0
        y_ndc           = 1.0 - (2.0 * y) / height

        # Near and far points in view space
        near_point      = glm.vec4(x_ndc, y_ndc, -1.0, 1.0)
        far_point       = glm.vec4(x_ndc, y_ndc,  1.0, 1.0)

        inv_projview    = glm.inverse(proj * view)
        p_near          = inv_projview * near_point
        p_far           = inv_projview * far_point
        p_near          /= p_near.w
        p_far           /= p_far.w

        return glm.vec3(p_near), glm.vec3(p_far)


    def delegate_tilt(self, start_pos, end_pos):

        #dx = end_pos.x() - start_pos.x()
        dy = end_pos.y() - start_pos.y()

        sensitivity = 0.1
        
        self.logic.camera.add_tilt(dy * sensitivity)
        #self.logic.camera.add_orbit(dx * sensitivity)





class MainWindow(QMainWindow):
    def __init__(self, configs):
        super().__init__()

        self.configs = configs

        self.setWindowTitle("PlaneSim")
        self.setGeometry(0, 0, configs.getint("window_width"), configs.getint("window_height"))
        self.gl_widget = GLWidget(configs)
        self.setCentralWidget(self.gl_widget)

        # When a pressed key is considered held is OS dependent. Avoid this break by start as soon as a key is pressed.
        self.keys_held          = set()
        self.timer = QTimer()
        self.timer.timeout.connect(self._process_held_keys)
        print(1000 // self.configs.getfloat("app_fps"))
        self.timer.start(1000 // self.configs.getint("app_fps"))

        # Variables for user interaction
        self.last_mouse_pos     = None
        self.left_mouse_down    = False
        self.middle_mouse_down  = False


    def _process_held_keys(self):
        for key in self.keys_held:
            self.gl_widget.delegate_key_pressed(key)


    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.close()
        self.keys_held.add(key)


    def keyReleaseEvent(self, event):
        key = event.key()
        if key in self.keys_held:
            self.keys_held.remove(key)
            self.gl_widget.delegate_key_released(key)


    def wheelEvent(self, event):
        self.gl_widget.delegate_wheel_event(event)


    def mousePressEvent(self, event):
        self.last_mouse_pos     = event.position()
        if event.button() == Qt.MouseButton.LeftButton:
            self.left_mouse_down    = True
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.middle_mouse_down  = True


    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.left_mouse_down    = False
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.middle_mouse_down  = False


    def mouseMoveEvent(self, event):
        if self.left_mouse_down:
            # TODO: Implement arcball?
            pass
        elif self.middle_mouse_down:
            new_pos = event.position()
            self.gl_widget.delegate_tilt(self.last_mouse_pos, new_pos)
            self.last_mouse_pos = new_pos


    def closeEvent(self, event):
        self.gl_widget.release()





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