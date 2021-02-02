import abc
from typing import List

from raytracing.ray import Ray
from raytracing.shade import ShadeRec


class OpticMaterial(abc.ABC):
    """Abstract class for an optical material"""

    def __init__(self):
        pass

    @abc.abstractmethod
    def generated_beams(self, ray: Ray, shade: ShadeRec) -> List[Ray]:
        """
        :return: list of new beam seeds to start from after the intersection
        of a beam and an object
        """
        pass
