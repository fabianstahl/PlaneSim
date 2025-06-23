import configparser as cfg
import glm
import utils
import numpy as np
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor

from engine.frustum import Frustum
from engine.camera import PivotCamera
from engine.model import MapTile, Airplane, Model, Target, Rocket, Strip
from engine.vao import VAO
from engine.primitives import Plane, Cylinder, Cloud, OBJ
from geography import MissionManager, Mission

from OpenGL.GL import *

class GameLogic():

    def __init__(self, configs : cfg.SectionProxy):
        
        self._configs       = configs
        self._in_air        = False

        # Setup Camera and Frustum Controller
        self._cam           = self._setup_camera()
        self._frustum       = self._setup_frustum()

        # Setup Mission Manager
        self._mission_mgr   = MissionManager(configs)
        self._mission       = self._mission_mgr.new_mission()
        print("New Mission: Reach '{}, {}'".format(self._mission.target.name, self._mission.target.country))

        # Setup shared VAOs
        self._air_plane_vao = VAO(OBJ(self._configs.get("plane_obj_path")))
        self._plane_vao     = VAO(Plane())
        self._cylinder_vao  = VAO(Cylinder())

        # Setup Game Objects
        self._air_plane     = self._setup_air_plane()
        self._enemies       = self._setup_enemies()
        self._targets       = self._setup_targets()
        self._wh_clouds     = self._setup_white_clouds()
        self._bl_clouds     = self._setup_black_clouds()
        
        self._strips        = []
        self._rockets       = []

        self._tile_cache    = dict()
    
        # Focus Camera on Airplane
        self._cam.pivot_point = self._air_plane.position


    @property
    def camera(self) -> PivotCamera:
        return self._cam

    @property
    def tiles(self) -> List[MapTile]:
        return list(self._tile_cache.values())

    @property
    def air_plane(self) -> Airplane:
        return self._air_plane
    
    @property
    def enemies(self) -> List[Airplane]:
        return self._enemies
    
    @property
    def bl_clouds(self) -> List[Cloud]:
        return self._bl_clouds
    
    @property
    def wh_clouds(self) -> List[Cloud]:
        return self._wh_clouds
    
    @property
    def targets(self) -> List[Target]:
        return self._targets
    
    @property
    def rockets(self) -> List[Rocket]:
        return self._rockets
    
    @property
    def strips(self) -> List[Strip]:
        return self._strips

    @property
    def mission(self) -> Mission:
        return self._mission
    
    @property
    def in_air(self) -> bool:
        return self._in_air
    
    @in_air.setter
    def in_air(self, value: bool):
        self._in_air = value


    def _setup_camera(self) -> PivotCamera: 
        return PivotCamera(
            pivot_point = glm.vec3(utils.parse_list(self._configs["cam_pivot_point"], float)),
            tilt_deg    = self._configs.getfloat("cam_tilt_deg"),
            orbit_deg   = self._configs.getfloat("cam_orbit_deg"),
            distance    = self._configs.getfloat("cam_distance"),
            fov_deg     = self._configs.getfloat("cam_fov"), 
            aspect      = self._configs.getint("window_width") / self._configs.getint("window_height"), 
            near        = self._configs.getfloat("cam_near"), 
            far         = self._configs.getfloat("cam_far")
        )
    

    def _setup_frustum(self) -> Frustum: 
        return Frustum(
            self._configs.getint("tile_max_z"),
            self._configs.getfloat("res_multiplier")
        )
    

    def _setup_air_plane(self) -> Airplane:
        plane_position          = self._mission_mgr.airport_manager.position_by_name(self._configs.get("start_airport"))
        return Airplane(
            vao                 = self._air_plane_vao, 
            position            = glm.vec3(*plane_position, self._configs.getfloat("plane_init_height")),
            scale               = self._configs.getfloat("plane_scale"),
            texture_path        = self._configs.get("plane_tex_path"), 
            yaw_deg             = self._configs.getfloat("plane_rot"), 
            min_vel             = self._configs.getfloat("plane_min_vel"),
            max_vel             = self._configs.getfloat("plane_max_vel")
        )
    

    def _setup_enemies(self) -> List[Airplane]:
        enemies     = []
        rand_pos    = np.random.random((self._configs.getint("no_enemies"), 2)) * 2 - 1
        rand_rot    = np.random.randint(0, 356, self._configs.getint("no_enemies"))
        for i in range(self._configs.getint("no_enemies")):
            enemy       = Airplane(
                vao             = self._air_plane_vao, 
                position        = glm.vec3(*rand_pos[i], self._configs.getfloat("enemy_height")),
                scale           = self._configs.getfloat("enemy_scale"),
                texture_path    = self._configs.get("plane_tex_path"),
                yaw_deg         = rand_rot[i], 
                min_vel         = self._configs.getfloat("plane_min_vel"),
                max_vel         = self._configs.getfloat("plane_max_vel")
            )
            enemies.append(enemy)
        return enemies
    

    def _setup_targets(self) -> List[Target]:
        targets = []
        for airport in self._mission_mgr.get_airports():
            target          = Target(
                vao                 = self._cylinder_vao, 
                position            = glm.vec3(*airport.position, self._configs.getfloat("target_height") / 2),
                scale               = glm.vec3(self._configs.getfloat("target_radius"), self._configs.getfloat("target_radius"), self._configs.getfloat("target_height")),
                texture_path        = self._configs.get("target_tex_path"),
                rotation_speed      = self._configs.getfloat("target_rot_speed")
            )
            targets.append(target)
        return targets
    

    def _setup_white_clouds(self) -> List[Model]:
        clouds      = []
        rand_pos_xy = np.random.random((self._configs.getint("no_white_clouds"), 2)) * 2 - 1
        rand_pos_z  = np.random.random(self._configs.getint("no_white_clouds")) * self._configs.getfloat("cloud_max_height")
        for i in range(self._configs.getint("no_white_clouds")):
            clouds_geom = Cloud(
                self._configs.getint("cloud_min_spheres"), 
                self._configs.getint("cloud_max_spheres"), 
                self._configs.getfloat("cloud_min_rad"), 
                self._configs.getfloat("cloud_max_rad"), 
                self._configs.getfloat("cloud_max_off_xy"), 
                self._configs.getfloat("cloud_max_off_z")
            )
            cloud       = Model(
                vao             = VAO(clouds_geom), 
                position        = glm.vec3(*rand_pos_xy[i], rand_pos_z[i]),
                scale           = glm.vec3(utils.parse_list(self._configs["cloud_scale"], float)),
                texture_path    = self._configs.get("cloud_tex_white"), 
                yaw_deg         = 0
            )
            clouds.append(cloud)
        return clouds
    

    def _setup_black_clouds(self) -> List[Model]:
        clouds      = []
        rand_pos_xy = np.random.random((self._configs.getint("no_black_clouds"), 2)) * 2 - 1
        rand_pos_z  = np.random.random(self._configs.getint("no_black_clouds")) * self._configs.getfloat("cloud_max_height")
        for i in range(self._configs.getint("no_black_clouds")):
            clouds_geom = Cloud(
                self._configs.getint("cloud_min_spheres"), 
                self._configs.getint("cloud_max_spheres"), 
                self._configs.getfloat("cloud_min_rad"), 
                self._configs.getfloat("cloud_max_rad"), 
                self._configs.getfloat("cloud_max_off_xy"), 
                self._configs.getfloat("cloud_max_off_z")
            )
            cloud       = Model(
                vao             = VAO(clouds_geom), 
                position        = glm.vec3(*rand_pos_xy[i], rand_pos_z[i]),
                scale           = glm.vec3(utils.parse_list(self._configs["cloud_scale"], float)),
                texture_path    = self._configs.get("cloud_tex_black"), 
                yaw_deg         = 0
            )
            clouds.append(cloud)
        return clouds
    

    def _setup_rocket(self) -> Rocket:
        rocket = Rocket(
            vao                 = self._plane_vao, 
            position            = glm.vec3(*self.air_plane.position),
            scale               = self._configs.getfloat("plane_scale"),
            texture_path        = self._configs.get("rocket_tex_path"), 
            forward             = self.air_plane.forward, 
            rocket_speed        = self._configs.getfloat("rocket_velocity") + self._air_plane.velocity,
            life_time           = self._configs.getint("rocket_life_time")
        )
        rocket.orientation = self.air_plane.orientation
        return rocket


    def _setup_strip(self) -> Strip:
        strip = Strip(
            vao                 = self._plane_vao, 
            position            = glm.vec3(*self.air_plane.position),
            scale               = self._configs.getfloat("plane_scale"),
            texture_path        = self._configs.get("strip_tex_path"), 
            life_time           = self._configs.getint("strip_life_time")
        )
        strip.orientation = self.air_plane.orientation
        return strip


    def _update_cam(self):
        self._cam.pivot_point = self.air_plane.position
        v1          = glm.vec2(0, 1)
        plane_forw  = self._air_plane.forward
        v2          = glm.vec2(plane_forw.x, plane_forw.y)
        angle_rad   = utils.signed_angle_2d(v1, v2)
        angle_off   = glm.degrees(angle_rad - self._cam.orbit_rad)        
        self._cam.add_orbit(angle_off)


    def map_tile_check(self):

        # Add missing tiles
        tile_ids = self._frustum.cull(self._cam.projection_matrix * self._cam.view_matrix, self._cam.cam_pos)
        with ThreadPoolExecutor() as executor:
            futures = []
            for (x, y, z) in tile_ids:
                if (x, y, z) not in self._tile_cache:
                    futures.append(executor.submit(MapTile.prepare_tile, x, y, z, self._plane_vao))

            for future in futures:
                x, y, z, tile = future.result()
                self._tile_cache[(x, y, z)] = tile
                tile.initializeGL(self._uniform_locations)

        # Remove tiles no longer visible
        for key in list(self._tile_cache.keys()):
            if not key in tile_ids:
                self._tile_cache[key].release(keep_vao = True)
                self._tile_cache.pop(key)


    def initializeGL(self, uniform_locations: Dict):
        
        self._uniform_locations = uniform_locations

        # Initialize shared VAOs
        for vao in [self._air_plane_vao, self._plane_vao, self._cylinder_vao]:
            vao.initializeGL()

        # Initialize objects
        for obj in [self._air_plane] + self._enemies + self._targets + self._wh_clouds + self._bl_clouds:
            obj.initializeGL(uniform_locations)


    def update(self, delta):
        
        # Airplane (once started)
        if self._in_air:
            self._air_plane.update(delta)
            self.add_strip()

        # Regular Game Objects
        for obj in self._enemies + self._targets:
            obj.update(delta)

        # Expirable Game Objects
        for rocket in self.rockets:
            rocket.update(delta)
            if rocket.is_expired():
                rocket.release(keep_vao = True)
                self.rockets.remove(rocket)

        for strip in self.strips:
            strip.update(delta)
            if strip.is_expired():
                strip.release(keep_vao = True)
                self.strips.remove(strip)

        self._update_cam()

        if self._mission.check_distance((self.air_plane.position.x, self.air_plane.position.y)):
            self._mission = self._mission_mgr.new_mission()
            print("New Mission: Reach '{}, {}'".format(self.mission.target.name, self.mission.target.country))


    def add_rocket(self):
        rocket = self._setup_rocket()
        rocket.initializeGL(self._uniform_locations)
        self._rockets.append(rocket)


    def add_strip(self):
        strip = self._setup_strip()
        strip.initializeGL(self._uniform_locations)
        self._strips.append(strip)

    
    def release(self):
        for obj in [self.air_plane] +\
                list(self._tile_cache.values()) +\
                self._enemies +\
                self._bl_clouds +\
                self._wh_clouds +\
                self._targets +\
                self._rockets +\
                self._strips:
            obj.release()

        for vao in [self._air_plane_vao, self._plane_vao, self._cylinder_vao]:
            vao.release()