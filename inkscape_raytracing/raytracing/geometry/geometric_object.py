from __future__ import annotations

import functools
from abc import abstractmethod
from dataclasses import dataclass
from typing import Protocol, Iterable

import numpy

from inkscape_raytracing.raytracing.ray import Ray
from inkscape_raytracing.raytracing.shade import ShadeRec


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
    def aabbox(self) -> AABBox:
        """Computes an axis aligned bounding box for the object"""
        raise NotImplementedError

    @abstractmethod
    def is_inside(self, ray: Ray) -> bool:
        """Indicates if a ray is inside or outside of the object"""
        raise NotImplementedError


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class AABBox:
    """
    Implements an axis-aligned bounding box

    This is used to accelerate the intersection between a beam and an object.
    If the beam doesn't hit the bounding box, it is not necessary to do
    expensive intersection calculations with the object.
    """

    lower_left: Point
    upper_right: Point

    @classmethod
    def englobing(cls, aabboxes: Iterable[AABBox]) -> AABBox:
        return functools.reduce(cls.englobing_two, aabboxes)

    @classmethod
    def englobing_two(cls, b1: AABBox, b2: AABBox) -> AABBox:
        union_lower_left = Point(
            min(b1.lower_left.x, b2.lower_left.x),
            min(b1.lower_left.y, b2.lower_left.y),
        )
        union_upper_right = Point(
            max(b1.upper_right.x, b2.upper_right.x),
            max(b1.upper_right.y, b2.upper_right.y),
        )
        return AABBox(union_lower_left, union_upper_right)

    def hit(self, ray: Ray) -> bool:
        """Tests if a beam intersects the bounding box"""

        # This algorithm uses the properties of IEEE floating-point
        # arithmetic to correctly handle cases where the ray travels
        # parallel to a coordinate axis.
        # See Williams et al. "An efficient and robust ray-box intersection
        # algorithm" for more details.

        p0 = numpy.array(self.lower_left)
        p1 = numpy.array(self.upper_right)
        # The implementation safely handles the case where an element
        # of ray.direction is zero. Warning for floating point error
        # can be ignored for this step.
        with numpy.errstate(invalid="ignore", divide="ignore"):
            a = 1 / ray.direction
            t_min = (numpy.where(a >= 0, p0, p1) - ray.origin) * a
            t_max = (numpy.where(a >= 0, p1, p0) - ray.origin) * a
        t0 = numpy.max(t_min)
        t1 = numpy.min(t_max)
        return (t0 < t1) and (t1 > Ray.min_travel)
