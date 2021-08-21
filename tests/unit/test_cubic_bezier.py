from math import sqrt

from inkscape_raytracing.raytracing import Vector, UnitVector
from inkscape_raytracing.raytracing.geometry import CubicBezier


def test_eval():
    bez = CubicBezier(Vector(0, 0), Vector(0, 0), Vector(1, 1), Vector(1, 1))
    assert bez.eval(0) == Vector(0, 0)
    assert bez.eval(1) == Vector(1, 1)
    assert bez.eval(0.5) == Vector(0.5, 0.5)


def test_tangent():
    bez = CubicBezier(Vector(0, 0), Vector(0, 0), Vector(1, 1), Vector(1, 1))
    assert bez.tangent(0.5) == UnitVector(1 / sqrt(2), 1 / sqrt(2))


def test_normal():
    bez = CubicBezier(Vector(0, 0), Vector(0, 0), Vector(1, 1), Vector(1, 1))
    assert bez.normal(0.5) == UnitVector(-1 / sqrt(2), 1 / sqrt(2))
