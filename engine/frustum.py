import glm
import numpy as np


def get_ray_plane_intersection(inv_viewproj, ndc_x, ndc_y):
    # Start at near plane (NDC z = -1), homogeneous clip space
    start = glm.vec4(ndc_x, ndc_y, -1.0, 1.0)
    end   = glm.vec4(ndc_x, ndc_y,  1.0, 1.0)

    world_start = inv_viewproj * start
    world_end   = inv_viewproj * end
    world_start /= world_start.w
    world_end   /= world_end.w

    direction = world_end - world_start
    t = -world_start.z / direction.z  # intersection with z=0
    intersection = glm.vec3(world_start) + glm.vec3(direction) * t
    return (intersection.x, intersection.y)


class Frustum:
    def __init__(self):
        self.start_plane = (-1, 1, -1, 1)


    def cull(self, vp_matrix: glm.mat4, z = 0):
        
        inv_viewproj = glm.inverse(vp_matrix)

        # Find frustum boundries
        frustum_points = [
            get_ray_plane_intersection(inv_viewproj, -1, -1),   # bottom-left
            get_ray_plane_intersection(inv_viewproj, -1, 1),    # top-left
            get_ray_plane_intersection(inv_viewproj,  1,  1),   # top-right
            get_ray_plane_intersection(inv_viewproj, 1, -1),    # bottom-right
        ]

        bbox_min = (min([x[0] for x in frustum_points]), min([x[1] for x in frustum_points]))
        bbox_max = (max([x[0] for x in frustum_points]), max([x[1] for x in frustum_points]))

        frustum_bbox = (bbox_min, bbox_max)

        planes = self.test_plane(0, 0, 0, frustum_bbox)
        #print(len(planes), " in frustum")
        return set(planes)


    def test_plane(self, x, y, z, frustum_boundries):

        results = []

        # Get Plane edges
        tile_size = 2.0 / (2 ** z)  # total range from -1 to 1 = 2.0

        min_x = -1.0 + y * tile_size
        max_x = min_x + tile_size
        max_y = 1 - x * tile_size
        min_y = max_y - tile_size
        (fr_min_x, fr_min_y), (fr_max_x, fr_max_y) = frustum_boundries

        # Test if plane is in camera frustum
        if max_x <= fr_min_x or min_x >= fr_max_x or max_y <= fr_min_y or min_y >= fr_max_y:
            return []

        # Test if resolution is small enough
        if (fr_max_x - fr_min_x) / (max_x - min_x) > 3:
            return [(x, y, z)]

        # Subdivide otherwise
        for x_ in ((2 * x, 2 * x + 1)):
            for y_ in ((2 * y, 2 * y + 1)):
                sub_planes = self.test_plane(x_, y_, z+1, frustum_boundries)
                results.extend(sub_planes)
        
        return results

