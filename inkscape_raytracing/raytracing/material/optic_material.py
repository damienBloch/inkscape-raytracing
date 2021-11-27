from abc import abstractmethod
from typing import Protocol

from ..geometry import RayObjectIntersection
from ..ray import Ray


class OpticMaterial(Protocol):
    """Protocol for an optical material"""

    @abstractmethod
    def generated_beams(self, ray: Ray, intersect: RayObjectIntersection) -> list[Ray]:
        """Compute the beams generated after intersection of a beam with this
        material

        Returns list of new beam seeds to start from after the intersection
        of a beam and an object.
        """
        raise NotImplementedError
