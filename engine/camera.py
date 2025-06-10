import glm

class Camera:
    def __init__(self,
            position    : glm.vec3,
            target      : glm.vec3,
            up          : glm.vec3,
            fov_degrees : float,  
            aspect      : float, 
            near        : float, 
            far         : float):
        
        self.position   = position

        # Create camera coordinate system
        self.forward    = glm.normalize(target - self.position)
        self.up         = glm.normalize(up)

        self.fov        = glm.radians(fov_degrees)
        self.aspect     = aspect
        self.near       = near
        self.far        = far
        self.tilt_deg   = 70
        self.orbit_deg  = 0

        self._update_view_matrix()
        self._update_projection_marix()

    def set_aspect(self, aspect: float):
        self.aspect = aspect


    def _find_z_pivot(self):

        # Avoid division by zero if view is parallel to the ground
        if abs(self.forward.z) < 1e-6:
            return

        # Where is the current pivot on the z=0 plane?
        t       = -self.position.z / self.forward.z
        pivot   = self.position + self.forward * t
        return pivot


    def _update_view_matrix(self) -> glm.mat4:

        pivot   = self._find_z_pivot()

        # Find correct right vector based on orbit angle
        rotation_orbit      = glm.rotate(glm.mat4(1), glm.radians(self.orbit_deg), glm.vec3(0, 0, 1))
        new_right           = glm.vec3(rotation_orbit * glm.vec4(glm.vec3(1, 0, 0), 0.0))

        # Perform tilting
        rotation_tilt       = glm.rotate(glm.mat4(1), glm.radians(self.tilt_deg), new_right)
        self.forward        = glm.vec3(rotation_tilt * rotation_orbit * glm.vec4(glm.vec3(0, 0, -1), 0.0))
        self.up             = glm.vec3(rotation_tilt * rotation_orbit * glm.vec4(glm.vec3(0, 1, 0), 0.0))
        self.position       = pivot - self.forward * glm.length(self.position - pivot)

        self._view_matrix   = glm.lookAt(self.position, self.position + self.forward, self.up)


    def _update_projection_marix(self) -> glm.mat4:
        self._projection_matrix = glm.perspective(self.fov, self.aspect, self.near, self.far)


    def get_view_matrix(self):
        return self._view_matrix
    

    def get_projection_matrix(self):
        return self._projection_matrix


    def translate(self, translation_vector: glm.vec3):
        """Translate camera position by a vector in world space (e.g., for WASD movement)"""
        self.position   += translation_vector
        self._update_view_matrix()


    def move(self, new_pos: glm.vec3):
        """Set camera position in world space"""
        self.position   = new_pos
        self._update_view_matrix()


    def focus(self, focus_point: glm.vec3):
        """
        Move the camera such that it continues looking from the same relative position,
        but the new pivot point becomes the specified position.
        """

        pivot           = self._find_z_pivot()
        self.position   += focus_point - pivot
        self._update_view_matrix()


    def zoom(self, distance):
        """Zoom camera along the forward axis by a distance"""
        # TODO: find out why tiles shift when zoomed out too far
        self.position   += self.forward * distance

        self._update_view_matrix()


    def tilt(self, angle_offset: float):
        """
        Tilt the camera around its right axis, keeping the intersection with z=0 fixed.
        """

        self.tilt_deg += angle_offset

        if self.tilt_deg < 0:
            self.tilt_deg = 0
        elif self.tilt_deg > 65:
            self.tilt_deg = 65

        self._update_view_matrix()


    def orbit(self, angle_offset: float):
        """
        Orbit the camera around the pivot point, keeping the intersection with z=0 fixed.
        """

        self.orbit_deg += angle_offset

        self._update_view_matrix()
