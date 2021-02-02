import abc
import numpy as np

from raytracing.ray import Ray
from raytracing.shade import ShadeRec


class GeometryError(RuntimeError):
    def __init__(self, message):
        self.message = message


def hit_aabbox(ray: Ray, aabbox: np.ndarray) -> bool:
    """Tests if a beam intersects the bounding box of the object"""

    # This algorithm uses the properties of IEEE floating-point
    # arithmetic to correctly handle cases where the ray travels exactly
    # in a negative coordinate-axis direction.
    # See Williams et al. "An efficient and robust ray-box intersection
    # algorithm" for more details.

    p0, p1 = aabbox
    # The implementation safely handles the case where an element
    # of ray.direction is zero so the warning for zero division can be
    # ignored for this step
    with np.errstate(divide='ignore'):
        a = 1/ray.direction
    t_min = (np.where(a >= 0, p0, p1) - ray.origin) * a
    t_max = (np.where(a >= 0, p1, p0) - ray.origin) * a
    t0 = np.max(t_min)
    t1 = np.min(t_max)
    # t0 = t_min[0] if t_min[0] > t_min[1] else t_min[1]
    # t1 = t_max[0] if t_max[0] < t_max[1] else t_max[1]
    return (t0 < t1) and (t1 > Ray.min_travel)


class GeometricObject(abc.ABC):
    """Abstract class for a geometric object (line, sphere, lens, ...)"""

    def __init__(self):
        pass

    @abc.abstractmethod
    def hit(self, ray: Ray) -> ShadeRec:
        """Tests the collision of a beam with the object.

        :params ray: The beam to be checked for intersection with this object
        :return: A shade indicating if a collision occurred and in
            this case it contains the information of the hit point
        """

        pass

    @property
    @abc.abstractmethod
    def aabbox(self) -> np.ndarray:
        """Computes an axis aligned bounding box for the object

        :return: [[x_min, y_min], [x_max, y_max]], an array containing the
            bottom left corner and top right corner of the box
        """

        pass

    @abc.abstractmethod
    def is_inside(self, point: np.ndarray) -> bool:
        """Indicates is a point is inside or outside of the object

        :params point:  The point to be checked, array [x, y] of size 2
        :return: True if the point is inside the object, False otherwise
        :raise GeometryError: if the instantiated object has no well defined
            inside and outside
        """

        pass
