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
from .ray import Ray, BeamPath
from .shade import ShadeRec


class OpticalObject(NamedTuple):
    geometry: GeometricObject
    material: OpticMaterial


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
        return self._propagate_beams([BeamPath(seed)], 0)

    def _propagate_beams(self, beam_paths: List[BeamPath], depth) -> List[BeamPath]:
        """Recursively computes the propagation of beams in the world

        :raise: warning if recursion depth hits a limit.
        """

        if depth >= self.max_recursion_depth:
            err_msg = (
                f"Maximal recursion depth exceeded ({self.max_recursion_depth})."
                "It is  likely that not all beam_paths have been rendered."
            )
            warnings.warn(err_msg)
            return beam_paths
        else:
            new_paths = list()
            for beam_path in beam_paths:
                if beam_path.is_complete():
                    new_paths.append(beam_path)
                else:
                    ray = beam_path.last_line.ray
                    shade, material = self.first_hit(ray)
                    beam_path.last_line.length = shade.travel_dist
                    new_seeds = material.generated_beams(ray, shade)
                    if not new_seeds:
                        new_paths.append(beam_path)
                    else:
                        for seed in new_seeds:
                            generated_paths = self._propagate_beams(
                                [BeamPath(seed)], depth + 1
                            )
                            for new_path in generated_paths:
                                new_paths.append(
                                    BeamPath.concatenate(beam_path, new_path)
                                )
            return new_paths
