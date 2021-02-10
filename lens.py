"""
Module to add a lens object in the document
"""

import inkex
from inkex.paths import arc_to_path


class Lens(inkex.GenerateExtension):
    @property
    def style(self):
        return {
                'stroke': '#000000', 'fill': 'none',
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

        d = self.to_document_units(opts.diameter, opts.diameter_unit)
        focal_length = self.to_document_units(opts.focal_length,
                                              opts.focal_length_unit)
        e = self.to_document_units(opts.edge_thickness, opts.edge_thickness_unit)
        optical_index = opts.optical_index

        R1 = (optical_index - 1) * focal_length
        if 2 * R1 < d:
            inkex.utils.debug("Focal power is too strong.")
            yield None
        else:
            circle = arc_to_path([-d / 2, 0],
                                 [R1, R1, 0., 0, 0, +d / 2, 0])
            circle += [
                    [[+d / 2, 0], [+d / 2, 0], [+d / 2, -e]],
                    [[+d / 2, -e], [+d / 2, -e], [-d / 2, -e]],
                    [[+d / 2, -e], [-d / 2, -e], [-d / 2, +e]],
            ]
            lens = inkex.PathElement()
            lens.style = self.style
            path = inkex.Path(inkex.CubicSuperPath([circle]))
            path.close()
            lens.path = path
            yield lens


if __name__ == '__main__':
    Lens().run()
