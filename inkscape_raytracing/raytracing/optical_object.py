from dataclasses import dataclass

from .geometry import GeometricObject
from .material import OpticMaterial


@dataclass(frozen=True)
class OpticalObject:
    geometry: GeometricObject
    material: OpticMaterial
