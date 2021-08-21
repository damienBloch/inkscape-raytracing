from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class UnitVector:
    x: float
    y: float

    def __post_init__(self):
        norm = sqrt(self.x ** 2 + self.y ** 2)
        self.x /= norm
        self.y /= norm

    def orthogonal(self) -> UnitVector:
        """Return a vector obtained by a pi/2 rotation"""
        return UnitVector(-self.y, self.x)
