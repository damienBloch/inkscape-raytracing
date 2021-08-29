from __future__ import annotations

from dataclasses import dataclass, field
from functools import singledispatchmethod
from math import sqrt
from numbers import Real


@dataclass(frozen=True)
class Vector:
    x: float = field()
    y: float = field()

    def orthogonal(self) -> Vector:
        """Return a vector obtained by a pi/2 rotation"""
        return UnitVector(-self.y, self.x)

    @singledispatchmethod
    def __mul__(self, other):
        raise NotImplementedError

    @__mul__.register
    def _(self, other: Real):
        return Vector(self.x * other, self.y * other)

    @singledispatchmethod
    def __rmul__(self, other):
        raise NotImplementedError(type(other))

    @__rmul__.register
    def _(self, other: Real):
        return Vector(self.x * other, self.y * other)

    @singledispatchmethod
    def __add__(self, other) -> Vector:
        raise NotImplementedError

    @singledispatchmethod
    def __sub__(self, other) -> Vector:
        raise NotImplementedError

    def __neg__(self) -> Vector:
        return Vector(-self.x, -self.y)

    def norm(self):
        return sqrt(self * self)

    def normalize(self) -> UnitVector:
        return UnitVector(self.x, self.y)


@dataclass(frozen=True)
class UnitVector(Vector):
    def __init__(self, x, y):
        norm = sqrt(x ** 2 + y ** 2)
        super().__init__(x / norm, y / norm)


@Vector.__add__.register
def _(self, other: Vector):
    return Vector(self.x + other.x, self.y + other.y)


@Vector.__sub__.register
def _(self, other: Vector):
    return Vector(self.x - other.x, self.y - other.y)


@Vector.__mul__.register
def _(self, other: Vector) -> float:
    return self.x * other.x + self.y * other.y

@Vector.__rmul__.register
def _(self, other: Vector) -> float:
    return self.x * other.x + self.y * other.y
