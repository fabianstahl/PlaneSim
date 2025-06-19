import glm
import numpy as np
import sys

from numba import njit

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



@njit
def get_normals(polygon):
    """Returns the normals (perpendicular vectors) of the polygon edges."""
    normals = []
    num_points = len(polygon)
    for i in range(num_points):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % num_points]
        edge = p2 - p1
        normal = np.array([-edge[1], edge[0]])  # Perpendicular to edge
        normal = normal / np.linalg.norm(normal)
        normals.append(normal)
    return normals


@njit
def project_polygon(polygon, axis):
    """Projects a polygon onto an axis and returns the min and max projection values."""
    projections = np.dot(polygon, axis)
    return projections.min(), projections.max()


@njit
def overlap(min_a, max_a, min_b, max_b):
    """Returns True if the projection intervals overlap."""
    return max_a >= min_b and max_b >= min_a


@njit
def test_plane_intersection_2d(points_a, points_b):
    """Tests if two convex 2D polygons intersect."""
    axes = get_normals(points_a) + get_normals(points_b)

    for axis in axes:
        min_a, max_a = project_polygon(points_a, axis)
        min_b, max_b = project_polygon(points_b, axis)
        if not overlap(min_a, max_a, min_b, max_b):
            return False  # Found a separating axis

    return True  # No separating axis found: intersection exists



class Frustum:
    def __init__(self, max_z):

        self.max_z          = max_z
        self.start_plane    = (-1, 1, -1, 1)


    def cull(self, vp_matrix: glm.mat4, cam_pos: glm.vec3, z = 0):

        inv_viewproj = glm.inverse(vp_matrix)

        # Find frustum boundries
        frustum_points = np.array([
            get_ray_plane_intersection(inv_viewproj, -1, -1),   # bottom-left
            get_ray_plane_intersection(inv_viewproj, -1, 1),    # top-left
            get_ray_plane_intersection(inv_viewproj, 1,  1),   # top-right
            get_ray_plane_intersection(inv_viewproj, 1, -1),    # bottom-right
        ])

        planes = self.test_plane(0, 0, 0, frustum_points, cam_pos)
        #print(len(planes), " in frustum")
        return set(planes)


    def test_plane(self, x, y, z, frustum_points, cam_pos):

        results = []

        # Get Tile corners
        tile_size   = 2.0 / (2 ** z)  # total range from -1 to 1 = 2.0
        min_x       = -1.0 + y * tile_size
        max_x       = min_x + tile_size
        max_y       = 1 - x * tile_size
        min_y       = max_y - tile_size
        tile_points = np.array([(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)])

        # Test if Tile is in camera frustum
        if not test_plane_intersection_2d(tile_points, frustum_points):
            return []

        # Check 1: If the camera is lover than the tile size / 2 -> subdivide
        elevation_treshold  = tile_size / 2
        if cam_pos.z > elevation_treshold:
            return [(x, y, z)]

        # Check 2: If the distance of the camera to the center is 
        center              = glm.vec3(min_x + tile_size / 2, min_y + tile_size / 2, 0)
        length              = glm.length(cam_pos - center)
        threshold           = glm.sqrt(glm.sqrt(tile_size/2**2 + tile_size/2**2)**2 + tile_size/2**2)
        if length > threshold:
            return [(x, y, z)]
        
        # Check 3: Max z Level reached
        if z == self.max_z:
            return [(x, y, z)]

        # Subdivide otherwise
        for x_ in ((2 * x, 2 * x + 1)):
            for y_ in ((2 * y, 2 * y + 1)):
                sub_planes = self.test_plane(x_, y_, z+1, frustum_points, cam_pos)
                results.extend(sub_planes)
        
        return results

