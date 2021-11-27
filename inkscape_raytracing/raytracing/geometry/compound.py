import functools
from dataclasses import dataclass
from typing import TypeVar, Generic, Iterable, Optional

from .geometric_object import GeometricObject, AABBox, RayObjectIntersection
from ..ray import Ray

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

    def get_intersection(self, ray: Ray) -> Optional[RayObjectIntersection]:
        result = None
        if self.aabbox.hit(ray):
            intersections = [obj.get_intersection(ray) for obj in self]
            intersections = list(filter(None, intersections))
            if intersections:
                result = min(intersections, key=lambda x: x.ray_travelled_dist)
                result._num_intersection = lambda: len(intersections)
                result.object = self

        return result

    def is_inside(self, ray: Ray) -> bool:
        # A ray is inside an object if it intersect its boundary an odd
        # number of times
        return (self.get_intersection(ray).num_intersection % 2) == 1
