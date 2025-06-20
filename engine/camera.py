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
        self._pivot_point   = pivot_point
        self._tilt_rad      = glm.radians(tilt_deg)
        self._orbit_rad     = glm.radians(orbit_deg)
        self._distance      = distance

        # Attributes for projection matrix
        self._fov           = glm.radians(fov_deg)
        self._aspect        = aspect
        self._near          = near
        self._far           = far

        self._view_matrix:          glm.mat4    = glm.mat4(1.0)
        self._projection_matrix:    glm.mat4    = glm.mat4(1.0)
        self._cam_pos:              glm.vec3    = glm.vec3(0, 0, 0)    

        self._update_view_matrix()
        self._update_projection_matrix()



    # === Read only Properties ===

    @property
    def view_matrix(self) -> glm.mat4:
        return self._view_matrix
    

    @property
    def projection_matrix(self) -> glm.mat4:
        return self._projection_matrix
    

    @property
    def orbit_rad(self) -> float:
        return self._orbit_rad
    

    @property
    def tilt_rad(self) -> float:
        return self._tilt_rad
    

    @property
    def cam_pos(self) -> glm.vec3:
        return self._cam_pos


    # === Read / Write Properties ===

    @property
    def pivot_point(self) -> glm.vec3:
        return self._pivot_point
    
    @pivot_point.setter
    def pivot_point(self, pivot_point: glm.vec3):
        self._pivot_point = pivot_point
        self._update_view_matrix()


    @property
    def distance(self) -> float:
        return self._distance
    
    @distance.setter
    def distance(self, distance: float):
        self._distance = distance
        self._update_view_matrix()


    @property
    def aspect(self) -> float:
        return self._aspect
    
    @aspect.setter
    def aspect(self, aspect: float):
        self._aspect = aspect
        self._update_projection_matrix()


    # === Private Methods ===

    def _update_view_matrix(self) -> glm.mat4:

        # Calculate the orbit rotation matrix
        rotation_orbit      = glm.rotate(glm.mat4(1), self._orbit_rad, FORWARD)
        new_right           = glm.vec3(rotation_orbit * glm.vec4(RIGHT, 0.0))
        new_up              = glm.vec3(rotation_orbit * glm.vec4(UP, 0.0))

        # Perform tilting
        rotation_tilt       = glm.rotate(glm.mat4(1), self._tilt_rad, new_right)
        new_up              = glm.vec3(rotation_tilt * new_up)
        new_forward         = glm.vec3(rotation_tilt * FORWARD)

        # Get new camera position 
        self._cam_pos       = self._pivot_point + new_forward * self._distance

        # LookAt Matrix: eye, center, up
        self._view_matrix   = glm.lookAt(self._cam_pos, self._pivot_point, new_up)


    def _update_projection_matrix(self) -> glm.mat4:
        self._projection_matrix = glm.perspective(self._fov, self._aspect, self._near, self._far)


    # === Public Methods ===

    def translate(self, translation_vector: glm.vec3):
        """Translate camera position by a vector in world space"""
        self._pivot_point   += translation_vector
        self._update_view_matrix()


    def add_tilt(self, angle_offset_deg: float):
        """Tilt the camera around its right axis, keeping the pivot point fixed."""
        tilt_deg        = glm.degrees(self._tilt_rad) + angle_offset_deg
        tilt_deg        = glm.clamp(tilt_deg, 0, 65)
        self._tilt_rad  = glm.radians(tilt_deg)
        self._update_view_matrix()


    def add_orbit(self, angle_offset_deg: float):
        """Orbit the camera around the pivot point"""
        orbit_deg       = (glm.degrees(self._orbit_rad) + angle_offset_deg) % 360
        self._orbit_rad = glm.radians(orbit_deg)
        self._update_view_matrix()
