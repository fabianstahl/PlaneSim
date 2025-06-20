import glm
import numpy as np
import geometry as geom

from numpy.typing import NDArray
from typing import Set, Tuple, List



class Frustum:
    def __init__(self, max_z: int, res_multiplier: float):
        self._max_z             = max_z
        self._res_multiplier    = res_multiplier


    def cull(self, vp_matrix: glm.mat4, cam_pos: glm.vec3) -> Set[Tuple[int, int, int]]:
        """
        Find out which (x, y, z) tiles should be drawn. 
        Only returns tiles that are within the camera frustum. 
        Tiles close to the camera position are subdivided, i.e. 
        the zoom level z is increased for these tiles.
        """
        inv_viewproj = glm.inverse(vp_matrix)

        # Find frustum boundries (bl, tl, tr, br)
        frustum_points = np.array([
            geom.ray_z_plane_intersection(inv_viewproj, -1, -1),
            geom.ray_z_plane_intersection(inv_viewproj, -1, 1),
            geom.ray_z_plane_intersection(inv_viewproj, 1,  1),
            geom.ray_z_plane_intersection(inv_viewproj, 1, -1),
        ])

        planes = self._test_plane(0, 0, 0, frustum_points, cam_pos)
        #print(len(planes), " in frustum")
        return set(planes)


    def _test_plane(self, x: int, y: int, z: int, frustum_points: NDArray[np.float32], cam_pos: glm.vec3) -> List[Tuple[int, int, int]]:

        results = []

        # Get Tile corners
        tile_size   = 2.0 / (2 ** z)  # total range from -1 to 1 = 2.0
        min_x       = -1.0 + y * tile_size
        max_x       = min_x + tile_size
        max_y       = 1 - x * tile_size
        min_y       = max_y - tile_size
        tile_points = np.array([(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)])

        # Test if Tile is in camera frustum
        if not geom.test_plane_intersection_2d(tile_points, frustum_points):
            return []

        # Check 1: Don't subdivide if the camera is above the tile cube
        if cam_pos.z > tile_size:
            return [(x, y, z)]

        # Check 2: Max z Level reached
        if z == self._max_z:
            return [(x, y, z)]

        # Check 3: Don't subdivide if distance from camera to the tile bottom center is larger than the tile size
        center          = glm.vec3(min_x + tile_size / 2, min_y + tile_size / 2, 0)
        length          = glm.length(cam_pos - center)
        dist_treshold   = self._res_multiplier * tile_size
        if length > dist_treshold:
            return [(x, y, z)]
        
        # Subdivide otherwise
        for x_ in ((2 * x, 2 * x + 1)):
            for y_ in ((2 * y, 2 * y + 1)):
                sub_planes = self._test_plane(x_, y_, z+1, frustum_points, cam_pos)
                results.extend(sub_planes)
        
        return results

