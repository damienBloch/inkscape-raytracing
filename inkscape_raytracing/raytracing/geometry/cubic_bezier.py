"""
Module for handling objects composed of cubic bezier curves
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cached_property
from math import isclose

import numpy

from .geometric_object import AABBox, GeometricObject, GeometryError
from ..ray import Ray
from ..shade import ShadeRec
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

    def eval(self, s) -> Vector:
        return (
            (1 - s) ** 3 * self.p0
            + 3 * s * (1 - s) ** 2 * self.p1
            + 3 * s ** 2 * (1 - s) * self.p2
            + s ** 3 * self.p3
        )

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

    def tangent(self, s: float) -> UnitVector:
        """Returns the tangent at the curve at curvilinear coordinate s"""

        diff_1 = (
            -3 * (self.p0 - 3 * self.p1 + 3 * self.p2 - self.p3) * s ** 2
            + 6 * (self.p0 - 2 * self.p1 + self.p2) * s
            - 3 * (self.p0 - self.p1)
        )
        # If the first derivative is not zero, it is parallel to the tangent
        if diff_1.norm() > 1e-8:
            return diff_1.normalize()
        # but is the first derivative is zero, we need to get the second order
        else:
            diff_2 = -6 * (self.p0 - 3 * self.p1 + 3 * self.p2 - self.p3) * s + 6 * (
                self.p0 - 2 * self.p1 + self.p2
            )
            if diff_2.norm() > 1e-8:
                return diff_2.normalize()
            else:  # and even to the 3rd derivative if necessary
                diff_3 = -6 * (self.p0 - 3 * self.p1 + 3 * self.p2 - self.p3)
                return diff_3.normalize()

    def normal(self, s: float) -> UnitVector:
        """Returns a vector normal at the curve at curvilinear coordinate s"""

        return self.tangent(s).orthogonal()

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

    def num_hits(self, ray: Ray) -> int:
        if self.aabbox.hit(ray):
            return len(self.intersection_beam(ray))
        else:
            return 0

    def hit(self, ray: Ray) -> ShadeRec:
        """
        Returns a shade with the information for the first intersection
        of a beam with the bezier segment
        """

        shade = ShadeRec()  # default no hit
        if self.aabbox.hit(ray):
            intersect_params = self.intersection_beam(ray)
            travel_dist = [t for (__, t) in intersect_params]
            if len(travel_dist) > 0:  # otherwise error with np.argmin
                shade.normal = True
                first_hit = numpy.argmin(travel_dist)
                shade.travel_dist = travel_dist[first_hit]
                shade.local_hit_point = ray.origin + shade.travel_dist * ray.direction
                shade.normal = self.normal(intersect_params[first_hit][0])
                shade.set_normal_same_side(ray.origin)
        return shade

    def is_inside(self, ray: Ray) -> bool:
        raise GeometryError(f"Can't define an inside for {self}.")


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
