from dataclasses import dataclass
from typing import ClassVar

from .vector import UnitVector, Vector


@dataclass(frozen=True)
class Ray:
    """This class implements a 2D line with an origin point and a direction."""

    origin: Vector
    direction: UnitVector
    travel: float = 0

    # If a beam hits an object before having traveled a minimum distance
    # from its origin, the collision is ignored. This prevents infinite
    # collision in case the origin of a beam is on the surface of an object
    min_travel: ClassVar[float] = 1e-7
