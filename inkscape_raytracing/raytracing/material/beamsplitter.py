from typing import List

import numpy
import numpy as np

from .optic_material import OpticMaterial
from ..geometry import RayObjectIntersection
from ..ray import Ray


class BeamSplitter(OpticMaterial):
    """
    Material producing two beams after collision. One is reflected and
    the other is transmitted.
    """

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
        reflected_ray = Ray(o, d - 2 * np.dot(d, n) * n, mat)
        mat = (
                numpy.array([[1, intersect.ray_travelled_dist], [0, 1]])
                @ ray.abcd
        )
        transmitted_ray = Ray(o, d, mat)
        return [reflected_ray, transmitted_ray]

    def abcd(self, curvature, ct):
        return numpy.array([[1, 0], [2 * curvature / ct, 1]])
