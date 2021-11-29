import numpy
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
            mat = (
                self.abcd_mirror(intersect.curvature, -d * n)
                @ numpy.array([[1, intersect.ray_travelled_dist], [0, 1]])
                @ ray.abcd
            )
            reflected_ray = Ray(o, d - 2 * (d * n) * n, mat)
            return [reflected_ray]
        else:  # refraction
            c2 = np.sqrt(u)
            mat = (
                self.abcd_refraction(1 / r, intersect.curvature, -d * n)
                @ numpy.array([[1, intersect.ray_travelled_dist], [0, 1]])
                @ ray.abcd
            )
            transmitted_ray = Ray(o, r * d + (r * c1 - c2) * n, mat)
            return [transmitted_ray]

    def abcd_mirror(self, curvature, ct):
        return numpy.array([[1, 0], [2 * curvature * ct, 1]])

    def abcd_refraction(self, n, curvature, ct):
        p = np.sqrt(n ** 2 - (1 - ct ** 2))
        return numpy.array([[p / n / ct, 0], [(ct - p) * curvature / ct / p, ct / p]])
