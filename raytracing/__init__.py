from typing import NamedTuple

from .world import *
from .ray import *
from .geometry import GeometricObject
from .material import OpticMaterial


class OpticalObject(NamedTuple):
    geometry: GeometricObject
    material: OpticMaterial
