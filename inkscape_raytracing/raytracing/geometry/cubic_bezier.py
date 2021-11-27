"""
Module for handling objects composed of cubic bezier curves
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cached_property, cache
from typing import Optional

import numpy

from .geometric_object import AABBox, GeometricObject, RayObjectIntersection
from ..ray import Ray
from ..vector import Vector, UnitVector


@dataclass(frozen=True)
class CubicBezier(GeometricObject):
    r"""
    Cubic bezier segment defined as

    .. math::
        \vec{X}(s) = (1-s)^3 \vec{p_0} + 3 s (1-s)^2 \vec{p_1}
                      + 3 s^2 (1-s) \vec{p_2} + s^3 \vec{p_3}

    for :math:`0 \le s \le 1`
    """

    p0: Vector
    p1: Vector
    p2: Vector
    p3: Vector

    def __init__(self, p0, p1, p2, p3):
        # Need to overwrite protocol parent __init__ for some python versions
        object.__setattr__(self, "p0", p0)
        object.__setattr__(self, "p1", p1)
        object.__setattr__(self, "p2", p2)
        object.__setattr__(self, "p3", p3)

    def eval(self, s, diff=0) -> Vector:
        if diff == 0:
            return (
                (1 - s) ** 3 * self.p0
                + 3 * s * (1 - s) ** 2 * self.p1
                + 3 * s ** 2 * (1 - s) * self.p2
                + s ** 3 * self.p3
            )
        elif diff == 1:
            return (
                -3 * (self.p0 - 3 * self.p1 + 3 * self.p2 - self.p3) * s ** 2
                + 6 * (self.p0 - 2 * self.p1 + self.p2) * s
                - 3 * (self.p0 - self.p1)
            )
        elif diff == 2:
            return -6 * (self.p0 - 3 * self.p1 + 3 * self.p2 - self.p3) * s + 6 * (
                self.p0 - 2 * self.p1 + self.p2
            )
        elif diff == 3:
            return -6 * (self.p0 - 3 * self.p1 + 3 * self.p2 - self.p3)
        else:
            return 0 * self.p0

    def get_intersection(self, ray: Ray) -> Optional[RayObjectIntersection]:
        result = None
        if self.aabbox.hit(ray):
            intersect_params = self.intersection_beam(ray)
            travel_dist = tuple([t for (__, t) in intersect_params])
            if travel_dist:

                @cache
                def first_hit():
                    return numpy.argmin(travel_dist)

                @cache
                def num_intersection():
                    return len(travel_dist)

                @cache
                def first_hit_point():
                    return ray.origin + travel_dist[first_hit()] * ray.direction

                @cache
                def normal():
                    return self.normal(intersect_params[first_hit()][0])

                @cache
                def curvature():
                    return self.curvature(intersect_params[first_hit()][0])

                result = RayObjectIntersection(
                    ray, self, num_intersection, first_hit_point, normal, curvature
                )
        return result

    @cached_property
    def aabbox(self) -> AABBox:
        # The box is slightly larger than the minimal box.
        # It prevents the box to have a zero dimension if the object is a line
        # aligned with vertical or horizontal.
        lower_left = Vector(
            min(self.p0.x, self.p1.x, self.p2.x, self.p3.x) - 1e-6,
            min(self.p0.y, self.p1.y, self.p2.y, self.p3.y) - 1e-6,
        )
        upper_right = Vector(
            max(self.p0.x, self.p1.x, self.p2.x, self.p3.x) + 1e-6,
            max(self.p0.y, self.p1.y, self.p2.y, self.p3.y) + 1e-6,
        )
        return AABBox(lower_left, upper_right)

    def intersection_beam(self, ray: Ray) -> list[tuple[float, float]]:
        r"""
        Returns all couples :math:`(s, t)` such that there exist
        :math:`\vec{X}` satisfying

        .. math::
            \vec{X} = (1-s)^3 \vec{p_0} + 3 s (1-s)^2 \vec{p_1}
            + 3 s^2 (1-s) \vec{p_2} + s^3 \vec{p_3}
        and
        .. math::
            \vec{X} = \vec{o} + t \vec{d}
        with :math:`0 \lq s \lq 1` and :math:`t >= 0`
        """

        a = ray.direction.orthogonal()
        a0 = a * (self.p0 - ray.origin)
        a1 = -3 * a * (self.p0 - self.p1)
        a2 = 3 * a * (self.p0 - 2 * self.p1 + self.p2)
        a3 = a * (-self.p0 + 3 * self.p1 - 3 * self.p2 + self.p3)
        roots = cubic_real_roots(a0, a1, a2, a3)
        intersection_points = [self.eval(s) for s in roots]
        travel = [(X - ray.origin) * ray.direction for X in intersection_points]

        def valid_domain(s, t):
            return 0 <= s <= 1 and t > Ray.min_travel

        return [(s, t) for (s, t) in zip(roots, travel) if valid_domain(s, t)]

    def normal(self, s: float) -> UnitVector:
        """Returns a vector normal at the curve at curvilinear coordinate s"""

        return self.tangent(s).orthogonal()

    def tangent(self, s: float) -> UnitVector:
        """Returns the tangent at the curve at curvilinear coordinate s"""
        for diff in range(1, 4):
            t = self.eval(s, diff)
            if t.norm() > 1e-8:
                return t.normalize()

    def curvature(self, s: float) -> float:
        d1 = self.eval(s, 1)
        d2 = self.eval(s, 2)
        return (d1.x * d2.y - d2.x * d1.y) / d1.norm() ** 3


def cubic_real_roots(d: float, c: float, b: float, a: float) -> list[float]:
    """
    Returns the real roots X of a cubic polynomial defined as

    .. math::
        a X^3 + b X^2 + c X + d = 0
    """

    # For more information see:
    # https://en.wikipedia.org/wiki/Cubic_equation#General_cubic_formula

    if not is_almost_zero(a):  # true cubic equation
        p = (3 * a * c - b ** 2) / 3 / a ** 2
        q = (2 * b ** 3 - 9 * a * b * c + 27 * a ** 2 * d) / 27 / a ** 3
        if is_almost_zero(p):
            t = [numpy.cbrt(-q)]
        else:
            discr = -(4 * p ** 3 + 27 * q ** 2)
            if is_almost_zero(discr):
                if is_almost_zero(q):
                    t = [0]
                else:
                    t = [3 * q / p, -3 * q / 2 / p]
            elif discr < 0:
                t = [
                    numpy.cbrt(-q / 2 + numpy.sqrt(-discr / 108))
                    + numpy.cbrt(-q / 2 - numpy.sqrt(-discr / 108))
                ]
            else:
                t = [
                    2
                    * numpy.sqrt(-p / 3)
                    * numpy.cos(
                        1 / 3 * numpy.arccos(3 * q / 2 / p * numpy.sqrt(-3 / p))
                        - 2 * numpy.pi * k / 3
                    )
                    for k in range(3)
                ]
        return [x - b / 3 / a for x in t]
    else:
        return quadratic_roots(b, c, d)


def quadratic_roots(a: float, b: float, c: float) -> list[float]:
    if not is_almost_zero(a):
        discr = b ** 2 - 4 * a * c
        if discr > 0:
            return [
                (-b + numpy.sqrt(discr)) / 2 / a,
                (-b - numpy.sqrt(discr)) / 2 / a,
            ]
        elif is_almost_zero(discr):
            return [-b / 2 / a]
        else:
            return []
    else:
        return linear_root(b, c)


def linear_root(a: float, b: float) -> list[float]:
    if is_almost_zero(a):  # No solutions for 0*X+b=0
        return []  # Ignore infinite solutions for a=b=0
    else:
        return [-b / a]


def is_almost_zero(x: float) -> bool:
    return math.isclose(x, 0, abs_tol=1e-8)
