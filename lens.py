"""
Module to add a lens object in the document
"""

import inkex
from inkex import Transform
from inkex.paths import arc_to_path

from utils import set_description


class Lens(inkex.GenerateExtension):
    """
    Produces a PathElement corresponding to the shape of the lens calculated
    from user parameters.
    """

    @property
    def style(self):
        return {
                'stroke': '#000000', 'fill': '#b7c2dd',
                'stroke-linejoin': 'round',
                'stroke-width': str(self.svg.unittouu('1px'))
        }

    def add_arguments(self, pars):
        pars.add_argument("--focal_length", type=float, default=100.)
        pars.add_argument("--focal_length_unit", type=str, default="mm")

        pars.add_argument("--diameter", type=float, default=1.)
        pars.add_argument("--diameter_unit", type=str, default="in")

        pars.add_argument("--edge_thickness", type=float, default=2.)
        pars.add_argument("--edge_thickness_unit", type=str, default="mm")

        pars.add_argument("--optical_index", type=float, default=1.5168)

        pars.add_argument("--lens_type", type=str, default="plano_con")

    def to_document_units(self, value: float, unit: str) -> float:
        return self.svg.unittouu(str(value) + unit)

    def generate(self):
        opts = self.options
        d = self.to_document_units(opts.diameter,
                                   opts.diameter_unit)
        f = self.to_document_units(opts.focal_length,
                                   opts.focal_length_unit)
        e = self.to_document_units(opts.edge_thickness,
                                   opts.edge_thickness_unit)
        optical_index = opts.optical_index

        lens_path = []
        if opts.lens_type == 'plano_con':
            # Radius of curvature from Lensmaker's equation
            roc = (optical_index - 1) * abs(f)
            if 2 * roc < d:
                inkex.utils.errormsg(
                    "Focal length is too short or diameter is too large.")
                return None
            elif (roc ** 2 - (d / 2) ** 2) ** .5 - roc < -e and f < 0:
                inkex.utils.errormsg("Edge thickness is too small.")
                return None
            else:
                sweep = 1 if f < 0 else 0
                # see arc_to_path in inkex/paths.py for description of
                # parameters
                lens_path = arc_to_path([-d / 2, 0],
                                        [roc, roc, 0., 0, sweep, +d / 2, 0])
                lens_path += [
                        [[+d / 2, 0], [+d / 2, 0], [+d / 2, -e]],
                        [[+d / 2, -e], [+d / 2, -e], [-d / 2, -e]],
                        [[+d / 2, -e], [-d / 2, -e], [-d / 2, +e]],
                ]
                # no need to close the path correctly as it's done after
        elif opts.lens_type == 'bi_con':
            roc = (optical_index - 1) * abs(f) \
                  * (1 + (1 - e / f / optical_index) ** .5)
            if 2 * roc < d:
                inkex.utils.errormsg(
                        "Focal length is too short or diameter is too large.")
                return None
            elif (roc ** 2 - (d / 2) ** 2) ** .5 - roc < -e / 2 and f < 0:
                inkex.utils.errormsg("Edge thickness is too small.")
                return None
            else:
                sweep = 1 if f < 0 else 0
                lens_path = arc_to_path([-d / 2, 0],
                                        [roc, roc, 0., 0, sweep, +d / 2, 0])
                lens_path += [
                        [[+d / 2, 0], [+d / 2, 0], [+d / 2, -e]],
                        [[+d / 2, -e], [+d / 2, -e], [+d / 2, -e]],
                ]
                lens_path += arc_to_path([+d / 2, -e],
                                         [roc, roc, 0., 0, sweep, -d / 2, -e])
                lens_path += [
                        [[-d / 2, -e], [-d / 2, -e], [-d / 2, 0]],
                        [[-d / 2, -e], [-d / 2, 0], [-d / 2, 0]],
                ]

        lens = inkex.PathElement()
        lens.style = self.style
        closed_path = inkex.Path(inkex.CubicSuperPath([lens_path]))
        closed_path.close()
        lens.path = closed_path.transform(Transform('rotate(90)'))
        set_description(lens, f"optics:glass:{optical_index}")
        yield lens


if __name__ == '__main__':
    Lens().run()
