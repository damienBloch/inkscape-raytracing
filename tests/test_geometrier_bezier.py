from pytest import approx

from raytracing.geometry.cubic_bezier import *


def test_cubic_real_roots():
    def roots_set(a0, a1, a2, a3):
        return set(cubic_real_roots(a0, a1, a2, a3))

    # true cubic
    assert roots_set(-12, 22, -12, 2) == approx({1, 2, 3})
    assert roots_set(-0, 1, -2, 1) == approx({0, 1})
    assert roots_set(-8, 0, 0, 1) == approx({2})
    assert roots_set(1, 2, 0, 1) == approx({-0.453398})
    assert roots_set(0, 0, 0, 1) == approx({0})
    assert roots_set(-1, 3, -3, 1) == approx({1})
    # quadratic
    assert roots_set(1, -2, 1, 0) == approx({1})
    assert roots_set(-1, 0, 1, 0) == approx({1, -1})
    assert roots_set(1, 0, 1, 0) == set()
    # linear
    assert roots_set(1, 2, 0, 0) == approx({-0.5})
    assert roots_set(1, 0, 0, 0) == set()
    assert roots_set(0, 0, 0, 0) == set()
