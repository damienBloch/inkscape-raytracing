from __future__ import annotations

from .optic_material import OpticMaterial
from ..ray import Ray
from ..shade import ShadeRec


class BeamDump(OpticMaterial):
    """Material absorbing all beams that hit it"""

    def __init__(self):
        super().__init__()

    def __repr__(self):
        return "BeamDump()"

    def generated_beams(self, ray: Ray, shade: ShadeRec) -> list[Ray]:
        return list()
