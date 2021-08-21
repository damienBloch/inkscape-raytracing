"""
Module for handling objects composed of cubic bezier curves
"""

from functools import cached_property
from typing import List, Tuple

import numpy

from .geometric_object import AABBox
from ..ray import Ray
from ..shade import ShadeRec


# def endpoint_info(self) -> Tuple[numpy.ndarray, numpy.ndarray]:
#     """Returns the location of the end point of the path and its tangent"""
#     last_segment = self._bezier_list[-1]  # always at least one element
#     return last_segment.eval(1), last_segment.tangent(1)


class CubicBezier:
    r"""
    Cubic bezier segment defined as

    .. math::
        \vec{X}(s) = (1-s)^3 \vec{p_0} + 3 s (1-s)^2 \vec{p_1}
                      + 3 s^2 (1-s) \vec{p_2} + s^3 \vec{p_3}

    for :math:`0 \le s \le 1`

    :type points: array_like of size (4,2)
    """

    def __init__(self, points: numpy.ndarray):
        self._p = numpy.array(points)

    def __repr__(self) -> str:
        return f"CubicBezier([{self._p[0]}, {self._p[1]}, {self._p[2]}, {self._p[3]}])"

    def eval(self, s):
        p0, p1, p2, p3 = self._p
        return (
            (1 - s) ** 3 * p0
            + 3 * s * (1 - s) ** 2 * p1
            + 3 * s ** 2 * (1 - s) * p2
            + s ** 3 * p3
        )

    @cached_property
    def aabbox(self) -> AABBox:
        # The box is slightly larger than the minimal box.
        # It prevents the box to have a zero dimension if the object is a line
        # aligned with vertical or horizontal.
        return AABBox(
            numpy.min(self._p, axis=0) - 1e-6, numpy.max(self._p, axis=0) + 1e-6
        )

    def tangent(self, s: float) -> numpy.ndarray:
        """Returns the tangent at the curve at curvilinear coordinate s"""

        p0, p1, p2, p3 = self._p
        diff_1 = (
            -3 * (p0 - 3 * p1 + 3 * p2 - p3) * s ** 2
            + 6 * (p0 - 2 * p1 + p2) * s
            - 3 * (p0 - p1)
        )
        # If the first derivative is not zero, it is parallel to the tangent
        if numpy.linalg.norm(diff_1) > 1e-8:
            return diff_1 / numpy.linalg.norm(diff_1)
        # but is the first derivative is zero, we need to get the second order
        else:
            diff_2 = -6 * (p0 - 3 * p1 + 3 * p2 - p3) * s + 6 * (p0 - 2 * p1 + p2)
            if numpy.linalg.norm(diff_2) > 1e-8:
                return diff_2 / numpy.linalg.norm(diff_2)
            else:
                diff_3 = -6 * (p0 - 3 * p1 + 3 * p2 - p3)
                return diff_3 / numpy.linalg.norm(diff_3)

    def normal(self, s: float) -> numpy.ndarray:
        """Returns a vector normal at the curve at curvilinear coordinate s"""

        return orthogonal(self.tangent(s))

    def intersection_beam(self, ray: Ray) -> List[Tuple[float, float]]:
        """
        Returns all couples :math:`(s, t)` such that there exist
        :math:`\\vec{X}` satisfying

        .. math::
            \\vec{X} = (1-s)^3 \\vec{p_0} + 3 s (1-s)^2 \\vec{p_1}
            + 3 s^2 (1-s) \\vec{p_2} + s^3 \\vec{p_3}
        and
        .. math::
            \\vec{X} = \\vec{o} + t \\vec{d}
        with :math:`0 \\lq s \\lq 1` and :math:`t >= 0`
        """

        p0, p1, p2, p3 = self._p
        a = orthogonal(ray.direction)
        a0 = numpy.dot(a, p0 - ray.origin)
        a1 = -3 * numpy.dot(a, p0 - p1)
        a2 = 3 * numpy.dot(a, p0 - 2 * p1 + p2)
        a3 = numpy.dot(a, -p0 + 3 * p1 - 3 * p2 + p3)
        roots = cubic_real_roots(a0, a1, a2, a3)
        intersection_points = [
            (1 - s) ** 3 * p0
            + 3 * s * (1 - s) ** 2 * p1
            + 3 * s ** 2 * (1 - s) * p2
            + s ** 3 * p3
            for s in roots
        ]
        travel = [numpy.dot(X - ray.origin, ray.direction) for X in intersection_points]

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


def cubic_real_roots(d: float, c: float, b: float, a: float) -> List[float]:
    """
    Returns the real roots X of a cubic polynomial defined as

    .. math::
        a X^3 + b X^2 + c X + d = 0
    """

    # For more information see:
    # https://en.wikipedia.org/wiki/Cubic_equation#General_cubic_formula

    if not numpy.isclose(a, 0):  # true cubic equation
        p = (3 * a * c - b ** 2) / 3 / a ** 2
        q = (2 * b ** 3 - 9 * a * b * c + 27 * a ** 2 * d) / 27 / a ** 3
        if numpy.isclose(p, 0):
            t = [numpy.cbrt(-q)]
        else:
            discr = -(4 * p ** 3 + 27 * q ** 2)
            if numpy.isclose(discr, 0):
                if numpy.isclose(q, 0):
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
    if not numpy.isclose(a, 0):
        discr = b ** 2 - 4 * a * c
        if discr > 0:
            return [
                (-b + numpy.sqrt(discr)) / 2 / a,
                (-b - numpy.sqrt(discr)) / 2 / a,
            ]
        elif numpy.isclose(discr, 0):
            return [-b / 2 / a]
        else:
            return []
    else:
        return linear_root(b, c)


def linear_root(a: float, b: float) -> list[float]:
    if numpy.isclose(a, 0):  # No solutions for 0*X+b=0
        return []  # Ignore infinite solutions for a=b=0
    else:
        return [-b / a]
