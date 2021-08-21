from typing import List

from inkscape_raytracing.raytracing.ray import Ray
from inkscape_raytracing.raytracing.shade import ShadeRec
from .optic_material import OpticMaterial


class BeamDump(OpticMaterial):
    """Material absorbing all beams that hit it"""

    def __init__(self):
        super().__init__()

    def __repr__(self):
        return "BeamDump()"

    def generated_beams(self, ray: Ray, shade: ShadeRec) -> List[Ray]:
        return list()
