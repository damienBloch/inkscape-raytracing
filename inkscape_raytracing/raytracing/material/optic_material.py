from abc import abstractmethod
from typing import Protocol, List

from inkscape_raytracing.raytracing.ray import Ray
from inkscape_raytracing.raytracing.shade import ShadeRec


class OpticMaterial(Protocol):
    """Protocol for an optical material"""

    @abstractmethod
    def generated_beams(self, ray: Ray, shade: ShadeRec) -> List[Ray]:
        """Compute the beams generated after intersection of a beam with this
        material

        Returns list of new beam seeds to start from after the intersection
        of a beam and an object.
        """
        raise NotImplementedError
