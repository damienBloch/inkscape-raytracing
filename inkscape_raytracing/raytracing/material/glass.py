from typing import List

import numpy as np

from inkscape_raytracing.raytracing.ray import Ray
from inkscape_raytracing.raytracing.shade import ShadeRec
from .optic_material import OpticMaterial


class Glass(OpticMaterial):
    """Material that transmits and bends beams hitting it"""

    def __init__(self, optical_index):
        super().__init__()
        self._optical_index = optical_index

    @property
    def optical_index(self):
        return self._optical_index

    def __repr__(self):
        return f"Glass({self._optical_index})"

    def generated_beams(self, ray: Ray, shade: ShadeRec) -> List[Ray]:
        o, d = shade.local_hit_point, ray.direction
        n = shade.normal
        if shade.hit_geometry.is_inside(ray):
            n_1, n_2 = self.optical_index, 1
        else:
            n_1, n_2 = 1, self.optical_index
        r = n_1 / n_2
        c1 = -np.dot(d, n)
        u = 1 - r ** 2 * (1 - c1 ** 2)
        if u < 0:  # total internal reflection
            reflected_ray = Ray(o, d - 2 * np.dot(d, n) * n)
            return [reflected_ray]
        else:  # refraction
            c2 = np.sqrt(u)
            transmitted_ray = Ray(o, r * d + (r * c1 - c2) * n)
            return [transmitted_ray]
