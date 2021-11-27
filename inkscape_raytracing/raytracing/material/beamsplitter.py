from typing import List

import numpy as np

from ..ray import Ray
from ..shade import ShadeRec
from .optic_material import OpticMaterial
from ..geometry import RayObjectIntersection

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
        reflected_ray = Ray(o, d - 2 * np.dot(d, n) * n)
        transmitted_ray = Ray(o, d)
        return [reflected_ray, transmitted_ray]
