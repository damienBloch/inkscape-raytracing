from dataclasses import dataclass
from typing import ClassVar

import numpy


@dataclass
class Ray:
    """This class implements a 2D line with an origin point and a direction."""

    origin: numpy.ndarray  # must be of size 2
    direction: numpy.ndarray  # must be of size 2
    travel: float = 0

    # If a beam hits an object before having traveled a minimum distance
    # from its origin, the collision is ignored. This prevents infinite
    # collision in case the origin of a beam is on the surface of an object
    min_travel: ClassVar[float] = 1e-7

    def __post_init__(self):
        self.direction /= numpy.linalg.norm(self.direction)


def orthogonal(vec):
    """Returns an orthogonal vector while conserving the norm"""

    return numpy.array([-vec[1], vec[0]])
