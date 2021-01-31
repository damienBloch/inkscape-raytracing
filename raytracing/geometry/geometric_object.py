import abc
import numpy as np


class GeometryError(RuntimeError):
    def __init__(self, message):
        self.message = message


class GeometricObject(abc.ABC):
    """Abstract class for a geometric object (plane, sphere, lens, ...)"""

    def __init__(self):
        # If a beam hits an object before having traveled a minimum distance
        # from its origin, the collision is ignored. This prevents infinite
        # collision in case the origin of a beam is on the surface of an object
        self._min_travel = 1e-8

    @abc.abstractmethod
    def hit(self, ray):
        """Tests the collision of a beam with the object.

        :params ray: The beam to be checked for intersection with this object
        :type ray: Ray
        :return: A shade indicating if a collision occurred and in
            this case it contains the information of the hit point
        :rtype: ShadeRec
        """

        pass

    def hit_aabbox(self, ray):
        """Tests if a beam intersects the bounding box of the object

        :params ray: The beam to be checked for intersection with the box
        :type ray: Ray
        :return: True if the beam intersects the box, False if not
        :rtype: bool
        """

        # This algorithm uses the properties of IEEE floating-point
        # arithmetic to correctly handle cases where the ray travels exactly
        # in a negative coordinate-axis direction.
        # See Williams et al. "An efficient and robust ray-box intersection
        # algorithm" for more details.

        p0, p1 = np.array(self.aabbox)
        # The implementation safely handles the case where an element
        # of ray.direction is zero so the warning for zero division can be
        # ignored for this step
        with np.errstate(divide='ignore'):
            a = 1/ray.direction
        t_min = (np.where(a >= 0, p0, p1) - ray.origin) * a
        t_max = (np.where(a >= 0, p1, p0) - ray.origin) * a
        t0 = np.max(t_min)
        t1 = np.min(t_max)
        return (t0 < t1) and (t1 > self._min_travel)

    @property
    @abc.abstractmethod
    def aabbox(self):
        """Computes an axis aligned bounding box for the object

        :return: ((x_min, y_min), (x_max, y_max)), a tuple containing the
            bottom left corner and top right corner of the box
        """

        pass

    @abc.abstractmethod
    def is_inside(self, point):
        """Indicates is a point is inside or outside of the object

        :params point:  The point to be checked
        :type point: array_like of size 2
        :return: True if the point is inside the object, False otherwise
        :rtype: Bool
        :raise GeometryError: if the instantiated object has no well defined
            inside and outside
        """

        pass
