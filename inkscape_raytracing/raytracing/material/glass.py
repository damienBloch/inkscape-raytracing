import numpy as np

from .optic_material import OpticMaterial
from ..geometry import RayObjectIntersection
from ..ray import Ray


class Glass(OpticMaterial):
    """Material that transmits and bends beams hitting it"""

    def __init__(self, optical_index):
        self._optical_index = optical_index

    @property
    def optical_index(self):
        return self._optical_index

    def __repr__(self):
        return f"Glass({self._optical_index})"

    def generated_beams(self, ray: Ray, intersect: RayObjectIntersection) -> list[Ray]:
        o, d = intersect.first_hit_point, ray.direction
        n = intersect.normal
        if intersect.object.is_inside(ray):
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
