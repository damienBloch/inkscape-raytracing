"""
Module for handling objects composed of cubic bezier curves
"""


import numpy as np
from raytracing.ray import orthogonal
from raytracing.shade import ShadeRec
from .geometric_object import GeometricObject


def englobing_aabbox(aabboxes):
    """Return a aabbox englobing a list of aabboxes"""
    aabboxes = np.array(aabboxes)
    return np.array([np.min(aabboxes[:, 0, :], axis=0),
                     np.max(aabboxes[:, 1, :], axis=0)])


def cubic_real_roots(a0: float, a1: float, a2: float, a3: float):
    """
    Returns the real roots X of a cubic polynomial defined as

    .. math::
        a_0 + a_1 X + a_2 X^2 + a_3 X^3 = 0
    """

    # TODO: replace numeric root finding algorithm by analytic case disjunction
    complex_roots = np.roots([a0, a1, a2, a3])
    is_real = np.abs(np.imag(complex_roots)) < 1e-8
    return complex_roots[is_real]


class CompositeCubicBezier(GeometricObject):
    """Set of paths represented by cubic Bezier curves

    :param list_: List of subpaths forming the superpath.

    :type list_: List of CubicBezierPath
    """

    def __init__(self, list_=None):
        if list_ is None:
            list_ = []
        super().__init__()
        self._subpath_list = list(list_)

    def __repr__(self):
        concat_paths = ", ".join(seg.__repr__() for seg in self._subpath_list)
        return f"CompositeCubicBezier([{concat_paths}])"

    def add_subpath(self, subpath):
        """
        :type subpath: CubicBezierPath
        """

        self._subpath_list.append(subpath)

    # TODO: Replace property aabbox by cached_property
    @property
    def aabbox(self):
        """Computes an axis aligned bounding box for the object

        :return: [[x_min, y_min], [x_max, y_max]], an array containing
            the bottom left corner and top right corner of the box
        """

        subpaths_bboxes = [sub.aabbox for sub in self._subpath_list]
        return englobing_aabbox(subpaths_bboxes)

    def first_hit_bezier(self, p0, p1, p2, p3, ray):
        """
        Returns a shade with the information for the first intersection
        of a beam with a bezier segment (p0, p1, p2, p3)
        """
        shade = ShadeRec()
        intersect_params = intersection_bezier_beam(p0, p1, p2, p3,
                                                    ray.origin, ray.direction)
        for (s, t) in intersect_params:
            if self._min_travel < t < shade.travel_distance:
                shade.travel_distance = t
                shade.hit_an_object = True
                shade.local_hit_point = ray.origin + t*ray.direction

    def hit(self, ray):
        shade = ShadeRec()
        if not self.hit_aabbox(ray):
            shade.hit_an_object = False
        else:
            shade.hit_an_object = True
        return shade

    def is_inside(self, point):
        pass


class CubicBezierPath(object):
    """Single path composed of a succession of CubicBezier segments"""

    def __init__(self, list_=None):
        if list_ is None:
            list_ = []
        self._bezier_list = list(list_)

    def __repr__(self):
        concat_seg = ", ".join(bez.__repr__() for bez in self._bezier_list)
        return f"CubicBezierPath([{concat_seg}])"

    def add_bezier(self, bezier):
        """
        :type bezier: CubicBezier
        """

        self._bezier_list.append(bezier)

    @property
    def aabbox(self):
        """Computes an axis aligned bounding box for the object

        :return: [[x_min, y_min], [x_max, y_max]], an array containing
            the bottom left corner and top right corner of the box
        """

        bezier_bboxes = [bez.aabbox for bez in self._bezier_list]
        return englobing_aabbox(bezier_bboxes)


class CubicBezier(object):
    """
    Cubic bezier segment defined as

    .. math::
        \\vec{X}(s) = (1-s)^3 \\vec{p_0} + 3 s (1-s)^2 \\vec{p_1}
                      + 3 s^2 (1-s) \\vec{p_2} + s^3 \\vec{p_3}

    for :math:`0 \\le s \\le 1`

    :type points: array_like of size (4,2)
    """

    def __init__(self, points):
        self._p = np.array(points)

    def __repr__(self):
        return f"CubicBezier([{self._p[0]}, {self._p[1]}, {self._p[2]}, " \
               f"{self._p[3]}])"

    @property
    def aabbox(self):
        return np.array([np.min(self._p, axis=0),
                         np.max(self._p, axis=0)])

    def tangent(self, s):
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

    def normal(self, s):
        """Returns the normal at the curve at curvilinear coordinate s"""

        return orthogonal(self.tangent(s))

    def intersection_bezier_beam(self, ray):
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
        a0 = np.dot(a, p0)
        a1 = -3 * np.dot(a, p0 - p1)
        a2 = 3 * np.dot(a, p0 - 2 * p1 + p2)
        a3 = np.dot(a, -p0 + 3 * p1 - 3 * p2 + p3)
        roots = cubic_real_roots(a0, a1, a2, a3)
        intersection_points = [(1-s)**3*p0 + (1-s)**2*s*p1
                               + (1-s)*s**2*p2 + s**3*p3 for s in roots]
        travel = [np.dot(X-ray.origin, ray.direction) for X in
                  intersection_points]
        return zip(roots, travel)
