"""
Module to describe and interact with a scene composed of various optical
objects
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Optional, List, NamedTuple, Iterable, Tuple

from .geometry import GeometricObject
from .material import OpticMaterial, BeamDump
from .ray import Ray
from .shade import ShadeRec


class OpticalObject(NamedTuple):
    geometry: GeometricObject
    material: OpticMaterial


class Tip(NamedTuple):
    beam: Ray
    rays: List


@dataclass
class World:
    """Stores a scene and computes the interaction with a ray"""

    objects: Optional[list[OpticalObject]] = field(default_factory=list)
    # default recursion depth can be changed, but should not exceed
    # system recursion limit.
    max_recursion_depth: Optional[int] = 500

    def add(self, obj: OpticalObject):
        self.objects.append(obj)

    def __iter__(self) -> Iterable[OpticalObject]:
        return iter(self.objects)

    @property
    def num_objects(self) -> int:
        return len(self.objects)

    def first_hit(self, ray: Ray) -> Tuple[ShadeRec, OpticMaterial]:
        """
        Returns the information about the first collision of the beam
        with an object.

        :return: A shade for the collision geometric information and the
        material of the object hit.
        """
        result = ShadeRec()
        material = BeamDump()
        for obj in self:
            shade = obj.geometry.hit(ray)
            if Ray.min_travel < shade.travel_dist < result.travel_dist:
                result = shade
                material = obj.material
        return result, material

    def propagate_beams(self, seed):
        initial_beam = []
        beams = [initial_beam]
        tips = [Tip(seed, initial_beam)]
        while len(tips):
            tip = tips.pop(0)
            if len(tip.rays) >= self.max_recursion_depth:
                err_msg = (
                    f"Maximal recursion depth exceeded ({self.max_recursion_depth})."
                    "It is  likely that not all beams have been rendered."
                )
                tips = []
                warnings.warn(err_msg)
            else:
                shade, material = self.first_hit(tip.beam)
                new_seeds = material.generated_beams(tip.beam, shade)
                ray = Ray(tip.beam.origin, tip.beam.direction, shade.travel_dist)
                tip.rays.append(ray)
                rays = [tip.rays] if len(new_seeds) == 1 else [tip.rays, *[[*tip.rays] for i in range(len(new_seeds)-1)]]
                for index, seed in enumerate(new_seeds):
                    tips.append(Tip(seed, rays[index]))
                rays.pop(0)
                for r in rays:
                    beams.append(r)

        return beams
