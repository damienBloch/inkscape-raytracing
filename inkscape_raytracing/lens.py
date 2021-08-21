"""
Module to add a lens object in the document
"""

from math import cos, pi, sin, sqrt, acos, tan

import inkex
from inkex import Transform


class Lens(inkex.GenerateExtension):
    """
    Produces a PathElement corresponding to the shape of the lens calculated
    from user parameters.
    """

    @property
    def style(self):
        return {
            "stroke": "#000000",
            "fill": "#b7c2dd",
            "stroke-linejoin": "round",
            "stroke-width": str(self.svg.unittouu("1px")),
        }

    def add_arguments(self, pars):
        pars.add_argument("--focal_length", type=float, default=100.0)
        pars.add_argument("--focal_length_unit", type=str, default="mm")

        pars.add_argument("--diameter", type=float, default=1.0)
        pars.add_argument("--diameter_unit", type=str, default="in")

        pars.add_argument("--edge_thickness", type=float, default=2.0)
        pars.add_argument("--edge_thickness_unit", type=str, default="mm")

        pars.add_argument("--optical_index", type=float, default=1.5168)

        pars.add_argument("--lens_type", type=str, default="plano_con")

    def to_document_units(self, value: float, unit: str) -> float:
        return self.svg.unittouu(str(value) + unit)

    def generate(self):
        opts = self.options
        d = self.to_document_units(opts.diameter, opts.diameter_unit)
        f = self.to_document_units(opts.focal_length, opts.focal_length_unit)
        e = self.to_document_units(opts.edge_thickness, opts.edge_thickness_unit)
        optical_index = opts.optical_index

        lens_path = []
        if opts.lens_type == "plano_con":
            # Radius of curvature from Lensmaker's equation
            roc = (optical_index - 1) * abs(f)
            if 2 * roc < d:
                inkex.utils.errormsg(
                    "Focal length is too short or diameter is too large."
                )
                return None
            elif (roc ** 2 - (d / 2) ** 2) ** 0.5 - roc < -e and f < 0:
                inkex.utils.errormsg("Edge thickness is too small.")
                return None
            else:
                sweep = 1 if f < 0 else 0
                lens_path = arc_to_path(
                    [-d / 2, 0], [roc, roc, 0.0, 0, sweep, +d / 2, 0]
                )
                lens_path += [
                    [[+d / 2, 0], [+d / 2, 0], [+d / 2, -e]],
                    [[+d / 2, -e], [+d / 2, -e], [-d / 2, -e]],
                    [[+d / 2, -e], [-d / 2, -e], [-d / 2, +e]],
                ]
                # no need to close the path correctly as it's done after
        elif opts.lens_type == "bi_con":
            roc = (
                (optical_index - 1) * abs(f) * (1 + (1 - e / f / optical_index) ** 0.5)
            )
            if 2 * roc < d:
                inkex.utils.errormsg(
                    "Focal length is too short or diameter is too large."
                )
                return None
            elif (roc ** 2 - (d / 2) ** 2) ** 0.5 - roc < -e / 2 and f < 0:
                inkex.utils.errormsg("Edge thickness is too small.")
                return None
            else:
                sweep = 1 if f < 0 else 0
                lens_path = arc_to_path(
                    [-d / 2, 0], [roc, roc, 0.0, 0, sweep, +d / 2, 0]
                )
                lens_path += [
                    [[+d / 2, 0], [+d / 2, 0], [+d / 2, -e]],
                    [[+d / 2, -e], [+d / 2, -e], [+d / 2, -e]],
                ]
                lens_path += arc_to_path(
                    [+d / 2, -e], [roc, roc, 0.0, 0, sweep, -d / 2, -e]
                )
                lens_path += [
                    [[-d / 2, -e], [-d / 2, -e], [-d / 2, 0]],
                    [[-d / 2, -e], [-d / 2, 0], [-d / 2, 0]],
                ]

        lens = inkex.PathElement()
        lens.style = self.style
        closed_path = inkex.Path(inkex.CubicSuperPath([lens_path]))
        closed_path.close()
        lens.path = closed_path.transform(Transform("rotate(90)"))
        lens.desc = (
            f"L{opts.focal_length}{opts.focal_length_unit}\n"
            f"optics:glass:{optical_index:.4f}"
        )
        yield lens


def arc_to_path(point, params):
    """Approximates an arc with cubic bezier segments.

    Arguments:
    point:  Starting point (absolute coords)
    params: Arcs parameters as per
              https://www.w3.org/TR/SVG/paths.html#PathDataEllipticalArcCommands

    Returns a list of triplets of points : [control_point_before, node, control_point_after]
    (first and last returned triplets are [p1, p1, *] and [*, p2, p2])
    """
    A = point[:]
    rx, ry, theta, long_flag, sweep_flag, x2, y2 = params[:]
    theta = theta * pi / 180.0
    B = [x2, y2]
    # Degenerate ellipse
    if rx == 0 or ry == 0 or A == B:
        return [[A[:], A[:], A[:]], [B[:], B[:], B[:]]]

    # turn coordinates so that the ellipse morph into a *unit circle* (not 0-centered)
    mat = mat_prod(
        (rot_mat(theta), [[1.0 / rx, 0.0], [0.0, 1.0 / ry]], rot_mat(-theta))
    )
    apply_mat(mat, A)
    apply_mat(mat, B)

    k = [-(B[1] - A[1]), B[0] - A[0]]
    d = k[0] * k[0] + k[1] * k[1]
    k[0] /= sqrt(d)
    k[1] /= sqrt(d)
    d = sqrt(max(0, 1 - d / 4.0))
    # k is the unit normal to AB vector, pointing to center O
    # d is distance from center to AB segment (distance from O to the midpoint of AB)
    # for the last line, remember this is a unit circle, and kd vector is orthogonal to AB (Pythagorean thm)

    if (
        long_flag == sweep_flag
    ):  # top-right ellipse in SVG example https://www.w3.org/TR/SVG/images/paths/arcs02.svg
        d *= -1

    O = [(B[0] + A[0]) / 2.0 + d * k[0], (B[1] + A[1]) / 2.0 + d * k[1]]
    OA = [A[0] - O[0], A[1] - O[1]]
    OB = [B[0] - O[0], B[1] - O[1]]
    start = acos(OA[0] / norm(OA))
    if OA[1] < 0:
        start *= -1
    end = acos(OB[0] / norm(OB))
    if OB[1] < 0:
        end *= -1
    # start and end are the angles from center of the circle to A and to B respectively

    if sweep_flag and start > end:
        end += 2 * pi
    if (not sweep_flag) and start < end:
        end -= 2 * pi

    nb_sectors = int(abs(start - end) * 2 / pi) + 1
    d_theta = (end - start) / nb_sectors
    v = 4 * tan(d_theta / 4.0) / 3.0
    # I would use v = tan(d_theta/2)*4*(sqrt(2)-1)/3 ?
    p = []
    for i in range(0, nb_sectors + 1, 1):
        angle = start + i * d_theta
        v1 = [
            O[0] + cos(angle) - (-v) * sin(angle),
            O[1] + sin(angle) + (-v) * cos(angle),
        ]
        pt = [O[0] + cos(angle), O[1] + sin(angle)]
        v2 = [O[0] + cos(angle) - v * sin(angle), O[1] + sin(angle) + v * cos(angle)]
        p.append([v1, pt, v2])
    p[0][0] = p[0][1][:]
    p[-1][2] = p[-1][1][:]

    # go back to the original coordinate system
    mat = mat_prod((rot_mat(theta), [[rx, 0], [0, ry]], rot_mat(-theta)))
    for pts in p:
        apply_mat(mat, pts[0])
        apply_mat(mat, pts[1])
        apply_mat(mat, pts[2])
    return p


def mat_prod(m_list):
    """Get the product of the mat"""
    prod = m_list[0]
    for mat in m_list[1:]:
        a00 = prod[0][0] * mat[0][0] + prod[0][1] * mat[1][0]
        a01 = prod[0][0] * mat[0][1] + prod[0][1] * mat[1][1]
        a10 = prod[1][0] * mat[0][0] + prod[1][1] * mat[1][0]
        a11 = prod[1][0] * mat[0][1] + prod[1][1] * mat[1][1]
        prod = [[a00, a01], [a10, a11]]
    return prod


def rot_mat(theta):
    """Rotate the mat"""
    return [[cos(theta), -sin(theta)], [sin(theta), cos(theta)]]


def apply_mat(mat, point):
    """Apply the given mat"""
    x = mat[0][0] * point[0] + mat[0][1] * point[1]
    y = mat[1][0] * point[0] + mat[1][1] * point[1]
    point[0] = x
    point[1] = y


def norm(point):
    """Normalise"""
    return sqrt(point[0] * point[0] + point[1] * point[1])


if __name__ == "__main__":
    Lens().run()
