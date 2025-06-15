import glm



FORWARD     = glm.vec3(0, 0, 1) 
RIGHT       = glm.vec3(1, 0, 0)
UP          = glm.vec3(0, 1, 0)



class PivotCamera:
    def __init__(self,
            pivot_point : glm.vec3  = glm.vec3(0, 0, 0),
            tilt_deg    : float     = 70,
            orbit_deg   : float     = 0,
            distance    : float     = 0.1,
            fov_deg     : float     = 40,  
            aspect      : float     = 16/9, 
            near        : float     = 0.001, 
            far         : float     = 10):
        
        # Attributes for view matrix
        self.pivot_point    = pivot_point
        self.tilt_rad       = glm.radians(tilt_deg)
        self.orbit_rad      = glm.radians(orbit_deg)
        self.distance       = distance

        # Attributes for projection matrix
        self.fov            = glm.radians(fov_deg)
        self.aspect         = aspect
        self.near           = near
        self.far            = far

        self._update_view_matrix()
        self._update_projection_marix()


    def set_aspect(self, aspect: float):
        self.aspect = aspect


    def _update_view_matrix(self) -> glm.mat4:

        # Calculate the orbit rotation matrix
        rotation_orbit      = glm.rotate(glm.mat4(1), self.orbit_rad, FORWARD)
        new_right           = glm.vec3(rotation_orbit * glm.vec4(RIGHT, 0.0))
        new_up              = glm.vec3(rotation_orbit * glm.vec4(UP, 0.0))

        # Perform tilting
        rotation_tilt       = glm.rotate(glm.mat4(1), self.tilt_rad, new_right)
        new_up              = glm.vec3(rotation_tilt * new_up)
        new_forward         = glm.vec3(rotation_tilt * FORWARD)

        # Get new camera position 
        cam_pos             = self.pivot_point + new_forward * self.distance

        # LookAt Matrix: eye, center, up
        self._view_matrix   = glm.lookAt(cam_pos, self.pivot_point, new_up)


    def _update_projection_marix(self) -> glm.mat4:
        self._projection_matrix = glm.perspective(self.fov, self.aspect, self.near, self.far)


    def get_view_matrix(self):
        return self._view_matrix
    

    def get_projection_matrix(self):
        return self._projection_matrix


    def translate(self, translation_vector: glm.vec3):
        """Translate camera position by a vector in world space (e.g., for WASD movement)"""
        self.pivot_point    += translation_vector
        self._update_view_matrix()


    def focus(self, new_pivot_point: glm.vec3):
        """
        Move the camera such that it continues looking from the same relative position,
        but the new pivot point becomes the specified position.
        """

        self.pivot_point    = new_pivot_point
        self._update_view_matrix()


    def zoom(self, distance):
        """
        Zoom camera along the forward axis by a distance
        """
        # TODO: find out why tiles shift when zoomed out too far
        self.distance   = distance

        self._update_view_matrix()


    def tilt(self, angle_offset_deg: float):
        """
        Tilt the camera around its right axis, keeping the intersection with z=0 fixed.
        """

        tilt_deg = glm.degrees(self.tilt_rad) + angle_offset_deg

        if tilt_deg < 0:
            tilt_deg = 0
        elif tilt_deg > 65:
            tilt_deg = 65

        self.tilt_rad = glm.radians(tilt_deg)
        self._update_view_matrix()


    def orbit(self, angle_offset_deg: float):
        """
        Orbit the camera around the pivot point, keeping the intersection with z=0 fixed.
        """

        orbit_deg       = (glm.degrees(self.orbit_rad) + angle_offset_deg) % 360
        self.orbit_rad  = glm.radians(orbit_deg)
        self._update_view_matrix()
