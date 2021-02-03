from typing import List

import numpy as np

from raytracing.ray import Ray
from raytracing.shade import ShadeRec

from .optic_material import OpticMaterial


class Glass(OpticMaterial):
    """Material reflecting beams that hit it"""

    def __init__(self, optical_index, *args, **kwargs):
        super().__init__()
        self._optical_index = optical_index

    def __repr__(self):
        return f"Glass({self._optical_index})"

    def generated_beams(self, ray: Ray, shade: ShadeRec) -> List[Ray]:
        o, d = shade.local_hit_point, ray.direction
        transmitted_ray = Ray(o, d)
        return [transmitted_ray]
