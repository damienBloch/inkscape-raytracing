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

    @staticmethod
    def orthogonal(vec: UnitVector) -> UnitVector:
        return UnitVector(-vec.y, vec.x)
