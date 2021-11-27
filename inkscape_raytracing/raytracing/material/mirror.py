from typing import List

import numpy

from .optic_material import OpticMaterial
from ..geometry import RayObjectIntersection
from ..ray import Ray


class Mirror(OpticMaterial):
    """Material reflecting beams that hit it"""

    def __repr__(self):
        return "Mirror()"

    def generated_beams(self, ray: Ray, intersect: RayObjectIntersection) -> List[Ray]:
        o, d = intersect.first_hit_point, ray.direction
        n = intersect.normal
        mat = (
            self.abcd(intersect.curvature, -d * n)
            @ numpy.array([[1, intersect.ray_travelled_dist], [0, 1]])
            @ ray.abcd
        )
        reflected_ray = Ray(o, d - 2 * (d * n) * n, mat)
        return [reflected_ray]

    def abcd(self, curvature, ct):
        return numpy.array([[1, 0], [2 * curvature / ct, 1]])
