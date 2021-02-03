from typing import List

import numpy as np

from raytracing.ray import Ray
from raytracing.shade import ShadeRec

from .optic_material import OpticMaterial


class Glass(OpticMaterial):
    """Material reflecting beams that hit it"""

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
            n_in, n_out = 1, self._optical_index
        else:
            n_out, n_in = 1, self._optical_index
        r_n = n_in/n_out
        ci = +np.dot(d, n)
        u = 1-(1-ci**2)/r_n**2
        if u < 0:  # total internal reflection
            reflected_ray = Ray(o, d - 2 * np.dot(d, n) * n)
            return [reflected_ray]
        else:  # refraction
            ct = np.sqrt(u)
            transmitted_ray = Ray(o, -d/r_n-(ct-ci/r_n)*n)
            return [transmitted_ray]
