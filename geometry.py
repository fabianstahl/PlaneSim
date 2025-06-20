import glm
import numpy as np
from numba import njit
from typing import Tuple, List
from numpy.typing import NDArray


def ray_z_plane_intersection(inv_viewproj: glm.mat4, u: float, v: float) -> Tuple[float, float]:
    """Find the intersection of screen coordinates u, v with the z=0 plane"""
    start           = glm.vec4(u, v, -1.0, 1.0)
    end             = glm.vec4(u, v,  1.0, 1.0)

    world_start     = inv_viewproj * start
    world_end       = inv_viewproj * end
    world_start     /= world_start.w
    world_end       /= world_end.w

    direction       = world_end - world_start
    t               = -world_start.z / direction.z
    intersection    = glm.vec3(world_start) + glm.vec3(direction) * t
    return intersection.x, intersection.y


@njit
def polygon_normals(polygon: NDArray[np.float32]) -> NDArray[np.float32]:
    """Returns the normals (perpendicular vectors) of the polygon edges."""
    normals     = np.zeros_like(polygon)
    num_points  = len(polygon)
    for i in range(num_points):
        p1          = polygon[i]
        p2          = polygon[(i + 1) % num_points]
        edge        = p2 - p1
        normal      = np.array([-edge[1], edge[0]])  # Perpendicular to edge
        normal      = normal / np.linalg.norm(normal)
        normals[i]  = normal
    return normals


@njit
def project_polygon(polygon: NDArray[np.float32], axis: int) -> Tuple[float, float]:
    """Projects a polygon onto an axis and returns the min and max projection values."""
    projections = np.dot(polygon, axis)
    return projections.min(), projections.max()


@njit
def overlap(min_a: float, max_a: float, min_b: float, max_b: float) -> bool:
    """Returns True if the projection intervals overlap."""
    return max_a >= min_b and max_b >= min_a


@njit
def test_plane_intersection_2d(points_a: NDArray[np.float32], points_b: NDArray[np.float32]) -> bool:
    """Tests if two convex 2D polygons intersect."""
    axes = polygon_normals(points_a) + polygon_normals(points_b)
    for axis in axes:
        min_a, max_a = project_polygon(points_a, axis)
        min_b, max_b = project_polygon(points_b, axis)
        if not overlap(min_a, max_a, min_b, max_b):
            return False  # Found a separating axis

    return True  # No separating axis found: intersection exists