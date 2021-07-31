from typing import List

import numpy

from .optic_material import OpticMaterial
from raytracing.ray import Ray
from raytracing.shade import ShadeRec


class Mirror(OpticMaterial):
    """Material reflecting beams that hit it"""

    def __repr__(self):
        return "Mirror()"

    def generated_beams(self, ray: Ray, shade: ShadeRec) -> List[Ray]:
        o, d = shade.local_hit_point, ray.direction
        n = shade.normal
        reflected_ray = Ray(o, d - 2 * numpy.dot(d, n) * n)
        return [reflected_ray]
