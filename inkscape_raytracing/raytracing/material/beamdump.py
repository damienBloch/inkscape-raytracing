from __future__ import annotations

from .optic_material import OpticMaterial
from ..geometry import RayObjectIntersection
from ..ray import Ray


class BeamDump(OpticMaterial):
    """Material absorbing all beams that hit it"""

    def __repr__(self):
        return "BeamDump()"

    def generated_beams(self, ray: Ray, intersect: RayObjectIntersection) -> list[Ray]:
        return list()
