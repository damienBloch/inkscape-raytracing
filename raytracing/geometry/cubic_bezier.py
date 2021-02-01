"""
Module for handling objects composed of cubic bezier curves
"""


import numpy as np
from typing import List, Tuple, Optional, Iterator
import inkex

from raytracing.ray import orthogonal, Ray
from raytracing.shade import ShadeRec
from .geometric_object import GeometricObject, hit_aabbox


def englobing_aabbox(aabboxes: List[np.ndarray]) -> np.ndarray:
    """Return a aabbox englobing a list of aabboxes"""
    aabboxes = np.array(aabboxes)
    return np.array([np.min(aabboxes[:, 0, :], axis=0),
                     np.max(aabboxes[:, 1, :], axis=0)])


def cubic_real_roots(a0: float, a1: float, a2: float, a3: float) -> \
                    List[float]:
    """
    Returns the real roots X of a cubic polynomial defined as

    .. math::
        a_0 + a_1 X + a_2 X^2 + a_3 X^3 = 0
    """

    # TODO: replace numeric root finding algorithm by analytic case disjunction
    complex_roots = np.roots([a0, a1, a2, a3])
    is_real = np.abs(np.imag(complex_roots)) < 1e-8
    return list(np.real(complex_roots[is_real]))


class CubicBezier(object):
    """
    Cubic bezier segment defined as

    .. math::
        \\vec{X}(s) = (1-s)^3 \\vec{p_0} + 3 s (1-s)^2 \\vec{p_1}
                      + 3 s^2 (1-s) \\vec{p_2} + s^3 \\vec{p_3}

    for :math:`0 \\le s \\le 1`

    :type points: array_like of size (4,2)
    """

    def __init__(self, points: np.ndarray):
        self._p = np.array(points)

    def __repr__(self) -> str:
        return f"CubicBezier([{self._p[0]}, {self._p[1]}, {self._p[2]}, " \
               f"{self._p[3]}])"

    @property
    def aabbox(self) -> np.ndarray:
        return np.array([np.min(self._p, axis=0),
                         np.max(self._p, axis=0)])

    def tangent(self, s: float) -> np.ndarray:
        """Returns the tangent at the curve at curvilinear coordinate s"""

        diff_1 = - 3*(1-s)**2*self._p[0] + 3*(s-1)*(3*s-1)*self._p[1] \
                 - 3*s*(1-s)*self._p[2] + 3*s**2*self._p[3]
        # If the first derivative is not zero, it is parallel to the tangent
        if np.linalg.norm(diff_1) > 1e-6:
            return diff_1/np.linalg.norm(diff_1)
        # but is the first derivative is zero, we need to get the second order
        else:
            diff_2 = -6*(s-1)*self._p[0] + 6*(3*s-2)*self._p[1] \
                     + 6*(1-3*s)*self._p[2] + 6*s*self._p[3]
            return diff_2/np.linalg.norm(diff_2)

    def normal(self, s: float) -> np.ndarray:
        """Returns the normal at the curve at curvilinear coordinate s"""

        return orthogonal(self.tangent(s))

    def intersection_beam(self, ray: Ray) -> Iterator[Tuple[float,
                                                            float]]:
        """
        Returns all couples :math:`(s, t)` such that there exist
        :math:`\\vec{X}` satisfying

        .. math::
            \\vec{X} = (1-s)^3 \\vec{p_0} + 3 s (1-s)^2 \\vec{p_1}
            + 3 s^2 (1-s) \\vec{p_2} + s^3 \\vec{p_3}
        and
        .. math::
            \\vec{X} = \\vec{o} + t \\vec{d}
        """

        p0, p1, p2, p3 = self._p
        a = orthogonal(ray.direction)
        a0 = np.dot(a, p0 - ray.origin)
        a1 = -3 * np.dot(a, p0 - p1)
        a2 = 3 * np.dot(a, p0 - 2 * p1 + p2)
        a3 = np.dot(a, -p0 + 3 * p1 - 3 * p2 + p3)
        roots = cubic_real_roots(a0, a1, a2, a3)
        intersection_points = [(1-s)**3*p0 + 3*(1-s)**2*s*p1
                               + 3*(1-s)*s**2*p2 + s**3*p3 for s in roots]
        travel = [np.dot(X-ray.origin, ray.direction) for X in
                  intersection_points]
        return zip(roots, travel)

    def hit(self, ray: Ray) -> ShadeRec:
        """
        Returns a shade with the information for the first intersection
        of a beam with the bezier segment
        """

        shade = ShadeRec()  # default no hit
        if hit_aabbox(ray, self.aabbox):
            intersect_params = self.intersection_beam(ray)
            for (s, t) in intersect_params:
                # only keep forward beam and finite bezier segment
                if Ray.min_travel < t < shade.travel_dist and 0 <= s <= 1:
                    shade.travel_dist = t
                    shade.hit_an_object = True
                    shade.local_hit_point = ray.origin + t*ray.direction
        return shade


class CubicBezierPath(object):
    """Single path composed of a succession of CubicBezier segments"""

    def __init__(self, list_: Optional[List[CubicBezier]] = None):
        if list_ is None:
            list_ = []
        self._bezier_list: List[CubicBezier] = list(list_)

    def __repr__(self) -> str:
        concat_seg = ", ".join(bez.__repr__() for bez in self._bezier_list)
        return f"CubicBezierPath([{concat_seg}])"

    def add_bezier(self, bezier: CubicBezier):
        self._bezier_list.append(bezier)

    @property
    def aabbox(self) -> np.ndarray:
        """Computes an axis aligned bounding box for the object

        :return: [[x_min, y_min], [x_max, y_max]], an array containing
            the bottom left corner and top right corner of the box
        """

        bezier_aabboxes = [bez.aabbox for bez in self._bezier_list]
        return englobing_aabbox(bezier_aabboxes)

    def hit(self, ray: Ray) -> ShadeRec:
        """
        Returns a shade with the information for the first intersection
        of a beam one of the Bezier segment composing the path
        """

        result = ShadeRec()
        if hit_aabbox(ray, self.aabbox):
            for bezier in self._bezier_list:
                shade = bezier.hit(ray)
                if Ray.min_travel < shade.travel_dist < result.travel_dist:
                    result = shade
        return result


class CompositeCubicBezier(GeometricObject):
    """Set of paths represented by cubic Bezier curves

    :param list_: List of subpaths forming the superpath.
    """

    def __init__(self, list_: Optional[List[CubicBezierPath]] = None):
        if list_ is None:
            list_ = []
        super().__init__()
        self._subpath_list = list(list_)

    def __repr__(self) -> str:
        concat_paths = ", ".join(seg.__repr__() for seg in self._subpath_list)
        return f"CompositeCubicBezier([{concat_paths}])"

    def add_subpath(self, subpath: CubicBezierPath):
        self._subpath_list.append(subpath)

    # TODO: Replace property aabbox by cached_property
    @property
    def aabbox(self) -> np.ndarray:
        """Computes an axis aligned bounding box for the object

        :return: [[x_min, y_min], [x_max, y_max]], an array containing
            the bottom left corner and top right corner of the box
        """

        subpaths_aabboxes = [sub.aabbox for sub in self._subpath_list]
        return englobing_aabbox(subpaths_aabboxes)

    def hit(self, ray: Ray) -> ShadeRec:
        """
        Returns a shade with the information for the first intersection
        of a beam with one of the subpaths composing the superpath
        """

        result = ShadeRec()
        inkex.utils.debug(self)
        inkex.utils.debug(self.aabbox)
        inkex.utils.debug(hit_aabbox(ray, self.aabbox))
        if hit_aabbox(ray, self.aabbox):
            for path in self._subpath_list:
                shade = path.hit(ray)
                if Ray.min_travel < shade.travel_dist < result.travel_dist:
                    result = shade
        return result

    def is_inside(self, point):
        pass
