import abc
from typing import List

import numpy as np

from raytracing.ray import Ray
from raytracing.shade import ShadeRec


class GeometryError(RuntimeError):
    def __init__(self, message):
        self.message = message


class AABBox(object):
    """
    Implements an axis-aligned bounding box. This is used to accelerate the
    intersection between a beam and an object. If the beam doesn't hit the
    bounding box, it is not necessary to do expensive intersection
    calculations.
    """

    def __init__(self, lower_left, upper_right):
        self._corners = np.array([lower_left, upper_right])

    def __eq__(self, other: 'AABBox'):
        return np.array_equal(self._corners, other._corners)

    @classmethod
    def englobing_aabbox(cls, aabboxes: List['AABBox']) -> 'AABBox':
        """Return a box that contains all boxes in a list"""

        aabboxes_array = np.array([box._corners for box in aabboxes])
        lower_left = np.min(aabboxes_array[:, 0, :], axis=0)
        upper_right = np.max(aabboxes_array[:, 1, :], axis=0)
        return AABBox(lower_left, upper_right)

    def hit(self, ray: Ray) -> bool:
        """Tests if a beam intersects the bounding box"""

        # This algorithm uses the properties of IEEE floating-point
        # arithmetic to correctly handle cases where the ray travels
        # parallel to a coordinate axis.
        # See Williams et al. "An efficient and robust ray-box intersection
        # algorithm" for more details.

        p0, p1 = self._corners
        # The implementation safely handles the case where an element
        # of ray.direction is zero so the warning for floating point error
        # can be ignored for this step.
        with np.errstate(invalid='ignore', divide='ignore'):
            a = 1 / ray.direction
            t_min = (np.where(a >= 0, p0, p1) - ray.origin) * a
            t_max = (np.where(a >= 0, p1, p0) - ray.origin) * a
        t0 = np.max(t_min)
        t1 = np.min(t_max)
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
    def aabbox(self) -> AABBox:
        """Computes an axis aligned bounding box for the object"""

        pass

    @abc.abstractmethod
    def is_inside(self, ray: Ray) -> bool:
        """Indicates is a point is inside or outside of the object

        :params point:  The point to be checked, array [x, y] of size 2
        :return: True if the point is inside the object, False otherwise
        :raise GeometryError: if the instantiated object has no well defined
            inside and outside
        """

        pass
