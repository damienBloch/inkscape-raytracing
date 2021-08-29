from __future__ import annotations

import functools
from dataclasses import dataclass
from typing import Protocol, Iterable, TypeVar, Generic

import numpy

from ..ray import Ray
from ..shade import ShadeRec
from ..vector import Vector


class GeometricObject(Protocol):
    """Protocol for a geometric object (line, rectangle, circle, ...)"""

    def hit(self, ray: Ray) -> ShadeRec:
        """Tests if a collision between a beam and the object occurred

        Returns a shade that contains the information about the collision in
        case it happened.
        """
        raise NotImplementedError

    def num_hits(self, ray: Ray) -> int:
        """Returns the number of times a beam intersect the object boundary"""
        raise NotImplementedError

    @property
    def aabbox(self) -> AABBox:
        """Computes an axis aligned bounding box for the object"""
        raise NotImplementedError

    def is_inside(self, ray: Ray) -> bool:
        """Indicates if a ray is inside or outside the object

        It is not possible to define an inside for every object, for example if it is
        not closed. In this case it should raise a GeometryError.
        """
        raise NotImplementedError


class GeometryError(RuntimeError):
    pass


T = TypeVar("T", bound=GeometricObject)


@dataclass(frozen=True)
class CompoundGeometricObject(GeometricObject, Generic[T]):
    sub_objects: tuple[T, ...]

    def __init__(self, sub_objects: Iterable[T]):
        object.__setattr__(self, "sub_objects", tuple(sub_objects))

    def __iter__(self) -> Iterable[T]:
        return iter(self.sub_objects)

    def __getitem__(self, item) -> T:
        return self.sub_objects[item]

    @functools.cached_property
    def aabbox(self):
        sub_boxes = (sub.aabbox for sub in self.sub_objects)
        return AABBox.englobing(sub_boxes)

    def hit(self, ray: Ray) -> ShadeRec:
        """
        Returns a shade with the information for the first intersection
        of a beam with one of the object composing the composite object
        """

        result = ShadeRec()
        if self.aabbox.hit(ray):
            result = find_first_hit(ray, self.sub_objects)
            result.hit_geometry = self
        return result

    def is_inside(self, ray: Ray) -> bool:
        # A ray is inside an object if it intersect its boundary an odd
        # number of times
        return (self.num_hits(ray) % 2) == 1

    def num_hits(self, ray: Ray) -> int:
        if self.aabbox.hit(ray):
            return sum([obj.num_hits(ray) for obj in self.sub_objects])
        else:
            return 0


def find_first_hit(ray: Ray, objects: Iterable[GeometricObject]) -> ShadeRec:
    result = ShadeRec()
    for obj in objects:
        shade = obj.hit(ray)
        if Ray.min_travel < shade.travel_dist < result.travel_dist:
            result = shade
    return result


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
