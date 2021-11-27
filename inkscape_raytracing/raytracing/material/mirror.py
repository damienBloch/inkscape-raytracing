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
        reflected_ray = Ray(o, d - 2 * numpy.dot(d, n) * n)
        return [reflected_ray]
