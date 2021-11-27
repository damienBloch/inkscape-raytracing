from __future__ import annotations

import functools
from dataclasses import dataclass, InitVar
from typing import Protocol, Iterable, Optional, Callable

import numpy

from ..ray import Ray
from ..vector import Vector, UnitVector


@dataclass
class RayObjectIntersection:
    ray: Ray
    object: GeometricObject
    num_intersection: InitVar[Callable[[], int]]
    first_hit_point: InitVar[Callable[[], Vector]]
    normal: InitVar[Callable[[], UnitVector]]

    def __post_init__(self, num_intersection, first_hit_point, normal):
        self._num_intersection = num_intersection
        self._first_hit_point = first_hit_point
        self._normal = normal

    @property
    def first_hit_point(self) -> Vector:
        return self._first_hit_point()

    @property
    def num_intersection(self) -> int:
        return self._num_intersection()

    @property
    def ray_travelled_dist(self) -> float:
        return (self.first_hit_point - self.ray.origin).norm()

    @functools.cached_property
    def normal(self) -> UnitVector:
        # set normal on the incoming side
        if (self.first_hit_point - self.ray.origin) * self._normal() > 0:
            return -self._normal()
        else:
            return self._normal()


class GeometricObject(Protocol):
    """Protocol for a geometric object (line, rectangle, circle, ...)"""

    @property
    def aabbox(self) -> AABBox:
        """Computes an axis aligned bounding box for the object"""
        raise NotImplementedError

    def get_intersection(self, ray: Ray) -> Optional[RayObjectIntersection]:
        raise NotImplementedError


class GeometryError(RuntimeError):
    pass


@dataclass(frozen=True)
class AABBox:
    """
    Implements an axis-aligned bounding box

    This is used to accelerate the intersection between a beam and an object.
    If the beam doesn't hit the bounding box, it is not necessary to do
    expensive intersection calculations with the object.
    """

    lower_left: Vector
    upper_right: Vector

    @classmethod
    def englobing(cls, aabboxes: Iterable[AABBox]) -> AABBox:
        return functools.reduce(cls.englobing_two, aabboxes)

    @classmethod
    def englobing_two(cls, b1: AABBox, b2: AABBox) -> AABBox:
        union_lower_left = Vector(
            min(b1.lower_left.x, b2.lower_left.x),
            min(b1.lower_left.y, b2.lower_left.y),
        )
        union_upper_right = Vector(
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

        p0 = numpy.array([self.lower_left.x, self.lower_left.y])
        p1 = numpy.array([self.upper_right.x, self.upper_right.y])
        direction = numpy.array([ray.direction.x, ray.direction.y])
        origin = numpy.array([ray.origin.x, ray.origin.y])
        # The implementation safely handles the case where an element
        # of ray.direction is zero. Warning for floating point error
        # can be ignored for this step.
        with numpy.errstate(invalid="ignore", divide="ignore"):
            a = 1 / direction
            t_min = (numpy.where(a >= 0, p0, p1) - origin) * a
            t_max = (numpy.where(a >= 0, p1, p0) - origin) * a
        t0 = numpy.max(t_min)
        t1 = numpy.min(t_max)
        return (t0 < t1) and (t1 > Ray.min_travel)
