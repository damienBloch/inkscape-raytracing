from typing import List

import numpy as np

from ..ray import Ray
from ..shade import ShadeRec
from .optic_material import OpticMaterial


class BeamSplitter(OpticMaterial):
    """
    Material producing two beams after collision. One is reflected and
    the other is transmitted.
    """

    def __repr__(self):
        return "Mirror()"

    def generated_beams(self, ray: Ray, shade: ShadeRec) -> List[Ray]:
        o, d = shade.local_hit_point, ray.direction
        n = shade.normal
        reflected_ray = Ray(o, d - 2 * np.dot(d, n) * n)
        transmitted_ray = Ray(o, d)
        return [reflected_ray, transmitted_ray]
