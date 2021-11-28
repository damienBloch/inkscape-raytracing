from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Optional

import numpy

from .vector import UnitVector, Vector


@dataclass(frozen=True)
class Ray:
    """A semi-infinite 2D line with an origin point and a direction"""

    origin: Vector
    direction: UnitVector

    abcd: numpy.array = field(default_factory=lambda: numpy.eye(2))

    # If a beam hits an object before having traveled a minimum distance
    # from its origin, the collision is ignored. This prevents infinite
    # collision in case the origin of a beam is on the surface of an object
    min_travel: ClassVar[float] = 1e-7


@dataclass
class Line:
    """Segment with a finite length"""

    ray: Ray
    length: Optional[float] = None


class BeamPath:
    """Piecewise linear beam path"""

    def __init__(self, seed: Ray):
        self.sections = [Line(seed)]

    def is_complete(self):
        return self.sections[-1].length is not None

    def __iter__(self):
        return iter(self.sections)

    @property
    def last_line(self):
        return self.sections[-1]

    @property
    def first_line(self):
        return self.sections[0]

    @staticmethod
    def concatenate(beam_path1, beam_path2):
        path = super().__new__(BeamPath)
        path.sections = beam_path1.sections + beam_path2.sections
        return path
