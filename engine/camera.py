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
        self.target     = target
        self.up         = up

        self.fov        = glm.radians(fov_degrees)
        self.aspect     = aspect
        self.near       = near
        self.far        = far



    def set_aspect(self, aspect: float):
        self.aspect = aspect



    def get_view_matrix(self) -> glm.mat4:
        return glm.lookAt(self.position, self.target, self.up)



    def get_projection_matrix(self) -> glm.mat4:
        return glm.perspective(self.fov, self.aspect, self.near, self.far)



    def translate(self, translation_vector: glm.vec3):
        """Translate camera position by a vector in world space (e.g., for WASD movement)"""
        self.position   += translation_vector
        self.target     += translation_vector



    def move(self, new_pos: glm.vec3):
        """Set camera position in world space"""
        direction       = glm.normalize(self.target  - self.position)
        distance        = glm.length(self.target - self.position)
        self.position   = new_pos
        self.target     = new_pos + direction * distance  # keep direction and distance



    def focus(self, focus_point: glm.vec3):
        """
        Move the camera such that it continues looking from the same relative position,
        but the new pivot point becomes the specified position.
        """

        forward = glm.normalize(self.target - self.position)

        # Avoid division by zero if view is parallel to the ground
        if abs(forward.z) < 1e-6:
            return

        # Where is the current pivot on the z=0 plane?
        t = -self.position.z / forward.z
        current_pivot = self.position + forward * t

        # Compute offset to shift camera so pivot moves to new location
        offset = focus_point - current_pivot

        # Move camera and target by the same amount
        self.position += offset
        self.target += offset



    def zoom(self, distance):
        """Zoom camera along the forward axis by a distance"""
        offset          = glm.normalize(self.target - self.position) * distance
        self.position   += offset
        self.target     += offset



    def tilt(self, angle_radians: float):
        """
        Tilt the camera around its right axis, keeping the intersection with z=0 fixed.
        angle_radians: Positive = tilt up, Negative = tilt down
        """
        # Step 1: Get view direction and right axis
        direction = glm.normalize(self.target - self.position)
        right     = glm.normalize(glm.cross(direction, self.up))

        # Step 2: Compute intersection with z=0 plane (assuming direction.z ≠ 0)
        if abs(direction.z) < 1e-6:
            return  # Avoid division by zero

        t       = -self.position.z / direction.z
        pivot   = self.position + direction * t  # point on z=0 plane

        # Step 3: Rotate direction around right vector
        rot             = glm.rotate(glm.mat4(1), angle_radians, right)
        new_direction   = glm.vec3(rot * glm.vec4(direction, 0.0))

        # TODO: see why this is sometimes buggy, make generic
        if new_direction.y < 0: 
            new_direction.y = 0
            new_direction = glm.normalize(new_direction)
        elif new_direction.y > 0.8: 
            new_direction.y = 0.8
            new_direction = glm.normalize(new_direction)

        # Step 4: Place the camera such that it looks at pivot
        distance        = glm.length(self.position - pivot)
        self.position   = pivot - new_direction * distance
        self.target     = pivot



    def orbit(self, angle_radians: float):
        
        # TODO: This needs fixing, buggy!

        # Direction camera is facing
        direction = glm.normalize(self.target - self.position)

        # Intersect with z=0 plane
        if direction.z == 0:
            return  # Parallel to z=0, no intersection

        t = -self.position.z / direction.z
        focus_point = self.position + direction * t

        # Vector from focus to current camera position
        relative = self.position - focus_point

        # Create rotation matrix around Z-axis
        rotation_matrix = glm.rotate(glm.mat4(1.0), angle_radians, glm.vec3(0, 0, 1))

        # Rotate relative position and up vector
        rotated_relative = glm.vec3(rotation_matrix * glm.vec4(relative, 1.0))
        self.position = focus_point + rotated_relative
        self.target = focus_point

        # 💡 Update the up vector as well!
        self.up = glm.vec3(rotation_matrix * glm.vec4(self.up, 0.0))
