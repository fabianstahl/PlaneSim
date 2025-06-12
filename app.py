import sys
import numpy as np
import glm
import configparser as cfg
import utils
import numpy as np

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QSurfaceFormat, QPainter, QColor, QFont
from PyQt6.QtCore import QTimer, Qt, QElapsedTimer
from OpenGL.GL import *
from concurrent.futures import ThreadPoolExecutor

from engine.shader import Shader, Program
from engine.camera import Camera
from engine.model import MapTile, Airplane, Model, Target, Rocket
from engine.frustum import Frustum
from engine.vao import VAO
from engine.primitives import Plane, Cylinder, Cloud
from geography import MissionManager


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

        cylinder_geom       = Cylinder()
        self.target_vao     = VAO(cylinder_geom)

        self.rockets        = []
        
        self.mission_manager    = MissionManager(configs)
        self.targets            = []
        for airport in self.mission_manager.get_airports():
            target          = Target(
                vao                 = self.target_vao, 
                position            = glm.vec3(*airport.position, configs.getfloat("target_height") / 2),
                scale               = glm.vec3(configs.getfloat("target_radius"), configs.getfloat("target_radius"), configs.getfloat("target_height")),
                texture_path        = configs.get("target_tex_path"),
                rotation_speed      = configs.getfloat("target_rot_speed")
            )
            self.targets.append(target)

        self.mission        = self.mission_manager.new_mission()
        print("New Mission: Reach '{}, {}'".format(self.mission.target.name, self.mission.target.country))

        plane_geom          = Plane()
        self.tile_vao       = VAO(plane_geom)

        self.air_plane          = Airplane(
            vao                 = self.tile_vao, 
            position            = glm.vec3(utils.parse_list(configs["plane_position"], float)),
            scale               = configs.getfloat("plane_scale"),
            texture_path        = configs.get("plane_tex_path"), 
            orbit_deg           = configs.getfloat("plane_rot"), 
            min_vel             = configs.getfloat("plane_min_vel"),
            max_vel             = configs.getfloat("plane_max_vel")
        )

        self.enemies    = []
        rand_pos        = np.random.random((configs.getint("no_enemies"), 2)) * 2 - 1
        rand_rot        = (0, 356, configs.getint("no_enemies"))
        for i in range(configs.getint("no_enemies")):
            enemy       = Airplane(
                vao             = self.tile_vao, 
                position        = glm.vec3(*rand_pos[i], configs.getfloat("enemy_height")),
                scale           = configs.getfloat("enemy_scale"),
                texture_path    = configs.get("enemy_tex_path"),
                orbit_deg       = rand_rot[0], 
                min_vel         = configs.getfloat("plane_min_vel"),
                max_vel         = configs.getfloat("plane_max_vel")
            )
            self.enemies.append(enemy)

        self.clouds     = []
        self.cloud_vaos = []

        rand_pos        = np.random.random((configs.getint("no_white_clouds"), 2)) * 2 - 1
        for i in range(configs.getint("no_white_clouds")):
            clouds_geom     = Cloud(self.configs.getint("cloud_min_spheres"), 
                                    self.configs.getint("cloud_max_spheres"), 
                                    self.configs.getfloat("cloud_min_rad"), 
                                    self.configs.getfloat("cloud_max_rad"), 
                                    self.configs.getfloat("cloud_max_off_xy"), 
                                    self.configs.getfloat("cloud_max_off_z"))
            cloud_vao       = VAO(clouds_geom)
            self.cloud_vaos.append(cloud_vao)

            cloud           = Model(
                vao                 = cloud_vao, 
                position            = glm.vec3(*rand_pos[i], 0.001),
                scale               = glm.vec3(utils.parse_list(configs["cloud_scale"], float)),
                texture_path        = configs.get("cloud_tex_white"), 
                orbit_deg           = 0
            )
            self.clouds.append(cloud)

        rand_pos        = np.random.random((configs.getint("no_black_clouds"), 2)) * 2 - 1
        for i in range(configs.getint("no_black_clouds")):
            clouds_geom     = Cloud(self.configs.getint("cloud_min_spheres"), 
                                    self.configs.getint("cloud_max_spheres"), 
                                    self.configs.getfloat("cloud_min_rad"), 
                                    self.configs.getfloat("cloud_max_rad"), 
                                    self.configs.getfloat("cloud_max_off_xy"), 
                                    self.configs.getfloat("cloud_max_off_z"))
            cloud_vao       = VAO(clouds_geom)
            self.cloud_vaos.append(cloud_vao)

            cloud           = Model(
                vao                 = cloud_vao, 
                position            = glm.vec3(*rand_pos[i], 0.001),
                scale               = glm.vec3(utils.parse_list(configs["cloud_scale"], float)),
                texture_path        = configs.get("cloud_tex_black")
            )
            self.clouds.append(cloud)


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

        for enemy in self.enemies:
            enemy.update(delta)

        for target in self.targets:
            target.update()

        for rocket in self.rockets:
            rocket.update()
            if rocket.is_destroyable():
                self.rockets.remove(rocket)

        new_focus_point = glm.vec3(self.air_plane.position.x, self.air_plane.position.y, 0)
        self.cam.focus(new_focus_point)

        if self.mission.check_distance((self.air_plane.position.x, self.air_plane.position.y)):
            self.mission = self.mission_manager.new_mission()
            print("New Mission: Reach '{}, {}'".format(self.mission.target.name, self.mission.target.country))

        self.update()


    def initializeGL(self):
        bg_color = utils.parse_list(self.configs["clear_color"], float)
        glClearColor(*bg_color)
        glClearDepth(1.0)
        glEnable(GL_CULL_FACE)
        glDepthMask(GL_FALSE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPointSize(self.configs.getfloat("point_size"))

        self.air_plane.initializeGL()
        
        self.tile_vao.initializeGL()

        self.target_vao.initializeGL()

        for target in self.targets:
            target.initializeGL()

        for cloud in self.cloud_vaos:
            cloud.initializeGL()
        
        for cloud in self.clouds:
            cloud.initializeGL()

        for enemy in self.enemies:
            enemy.initializeGL()

        self.setup_shaders()

        # Get uniform location
        self.model_loc  = self.program.get_uniform_location("model")
        self.view_loc   = self.program.get_uniform_location("view")
        self.proj_loc   = self.program.get_uniform_location("projection")



    def setup_shaders(self):
        vertex_shader   = Shader("shaders/vertex_shader.glsl", GL_VERTEX_SHADER)
        fragment_shader = Shader("shaders/fragment_shader.glsl", GL_FRAGMENT_SHADER)
        self.program    = Program(vertex_shader, fragment_shader)


    def shoot_rocket(self):
        
        rocket          = Rocket(
            vao                 = self.tile_vao, 
            position            = glm.vec3(*self.air_plane.position),
            scale               = 0.001,
            texture_path        = self.configs.get("rocket_tex_path"), 
            orbit_deg           = self.air_plane.orbit_deg, 
            rocket_speed        = self.configs.getfloat("rocket_speed"),
            forward             = self.air_plane.forward, 
            life_time           = self.configs.getint("rocket_life_time")
        )
        
        rocket.initializeGL()

        self.rockets.append(rocket)

    def paintGL(self):

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

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
        with ThreadPoolExecutor() as executor:
            futures = []
            for (x, y, z) in tile_ids:
                if (x, y, z) not in self.tile_cache:
                    futures.append(executor.submit(MapTile.prepare_tile, x, y, z, self.tile_vao))

            for future in futures:
                x, y, z, tile = future.result()
                self.tile_cache[(x, y, z)] = tile
                tile.initializeGL()


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

        # Render clouds
        for cloud in self.clouds:
            glUniformMatrix4fv(self.model_loc, 1, GL_FALSE, np.array(cloud.model_matrix, dtype=np.float32).T)
            cloud.render()

        # Render targets
        for target in self.targets:
            glUniformMatrix4fv(self.model_loc, 1, GL_FALSE, np.array(target.model_matrix, dtype=np.float32).T)
            target.render()

        # Render enemies
        for enemy in self.enemies:
            glUniformMatrix4fv(self.model_loc, 1, GL_FALSE, np.array(enemy.model_matrix, dtype=np.float32).T)
            enemy.render()

        # Render rockets
        for rocket in self.rockets:
            glUniformMatrix4fv(self.model_loc, 1, GL_FALSE, np.array(rocket.model_matrix, dtype=np.float32).T)
            rocket.render()

        # Start QPainter after OpenGL
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setPen(QColor(255, 120, 128))
        painter.setFont(QFont("Arial", 30))
        text    = "Reach '{}, {}'".format(self.mission.target.name, self.mission.target.country)
        width   = painter.fontMetrics().horizontalAdvance(text)
        x_pos   = configs.getint("window_width") // 2 - width // 2
        y_pos   = configs.getint("window_height") - 20
        painter.drawText(x_pos, y_pos, text)
        painter.end()


    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        self.cam.set_aspect(w/h)


    def release(self):
        self.air_plane.release()
        for tile in self.tile_cache.values():
            tile.release()
        self.program.release()


    def delegate_key_released(self, event):
        key = event.key()
        if key == Qt.Key.Key_W:
            self.air_plane.accelerate(0)
        elif key == Qt.Key.Key_S:
            self.air_plane.accelerate(0)


    def delegate_key_pressed(self, event):
        key = event.key()
        if key == Qt.Key.Key_W:
            self.air_plane.accelerate(0.0075)
        elif key == Qt.Key.Key_S:
            self.air_plane.accelerate(-0.01)
        elif key == Qt.Key.Key_A:
            self.air_plane.rotate(2)
            angle = self.air_plane.orbit_deg - self.cam.orbit_deg
            self.cam.orbit(angle)
        elif key == Qt.Key.Key_D:
            self.air_plane.rotate(-2)
            angle = self.air_plane.orbit_deg - self.cam.orbit_deg
            self.cam.orbit(angle)
        elif key == Qt.Key.Key_1:
            self.render_mode = 0
        elif key == Qt.Key.Key_2:
            self.render_mode = 1
        elif key == Qt.Key.Key_3:
            self.render_mode = 2
        elif key == Qt.Key.Key_Space:
            self.shoot_rocket()
        elif key == Qt.Key.Key_PageUp:
            self.cam.tilt(-5)
        elif key == Qt.Key.Key_PageDown:
            self.cam.tilt(5)
        elif key == Qt.Key.Key_Plus:
            self.cam.zoom(self.configs.getfloat("cam_zoom_factor") * glm.length(self.cam.position.z) - self.configs.getfloat("cam_zoom_offset"))
        elif key == Qt.Key.Key_Minus:
            self.cam.zoom(-self.configs.getfloat("cam_zoom_factor") * glm.length(self.cam.position.z) - self.configs.getfloat("cam_zoom_offset"))
        elif key == Qt.Key.Key_Right:
            self.cam.orbit(5)
        elif key == Qt.Key.Key_Left:
            self.cam.orbit(-5)
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

        sensitivity = 0.1
        
        self.cam.tilt(dy * sensitivity)
        self.cam.orbit(dx * sensitivity)





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

    def keyReleaseEvent(self, event):
        self.gl_widget.delegate_key_released(event)


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