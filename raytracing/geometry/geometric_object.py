from abc import abstractmethod
from typing import Protocol, List

import numpy

from raytracing.ray import Ray
from raytracing.shade import ShadeRec


class GeometricObject(Protocol):
    """Protocol for a geometric object (line, sphere, lens, ...)"""

    @abstractmethod
    def hit(self, ray: Ray) -> ShadeRec:
        """Tests if a collision between a beam and the object occurred

        Returns a shade that contains the information about the collision in
        case it happened.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def aabbox(self) -> "AABBox":
        """Computes an axis aligned bounding box for the object"""
        raise NotImplementedError

    @abstractmethod
    def is_inside(self, ray: Ray) -> bool:
        """Indicates if a ray is inside or outside of the object"""
        raise NotImplementedError


class AABBox:
    """
    Implements an axis-aligned bounding box

    This is used to accelerate the intersection between a beam and an object.
    If the beam doesn't hit the bounding box, it is not necessary to do
    expensive intersection calculations with the object.
    """

    def __init__(self, lower_left, upper_right):
        self._corners = numpy.array([lower_left, upper_right])

    def __eq__(self, other: "AABBox"):
        return numpy.array_equal(self._corners, other._corners)

    @classmethod
    def englobing_aabbox(cls, aabboxes: List["AABBox"]) -> "AABBox":
        """Return a box that contains all boxes in a list"""

        aabboxes_array = numpy.array([box._corners for box in aabboxes])
        lower_left = numpy.min(aabboxes_array[:, 0, :], axis=0)
        upper_right = numpy.max(aabboxes_array[:, 1, :], axis=0)
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
        with numpy.errstate(invalid="ignore", divide="ignore"):
            a = 1 / ray.direction
            t_min = (numpy.where(a >= 0, p0, p1) - ray.origin) * a
            t_max = (numpy.where(a >= 0, p1, p0) - ray.origin) * a
        t0 = numpy.max(t_min)
        t1 = numpy.min(t_max)
        return (t0 < t1) and (t1 > Ray.min_travel)
