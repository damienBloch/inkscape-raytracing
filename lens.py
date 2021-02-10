"""
Module to add a lens object in the document
"""

import inkex
from inkex.paths import arc_to_path


class Lens(inkex.GenerateExtension):
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
        focal_length = self.to_document_units(opts.focal_length,
                                              opts.focal_length_unit)
        e = self.to_document_units(opts.edge_thickness,
                                   opts.edge_thickness_unit)
        optical_index = opts.optical_index

        lens_path = []
        if opts.lens_type == 'plano_con':
            if focal_length >= 0:
                RoC = (optical_index - 1) * focal_length
                if 2 * RoC < d:
                    inkex.utils.debug("Focal power is too strong.")
                    return
                else:
                    lens_path = arc_to_path([-d / 2, 0],
                                             [RoC, RoC, 0., 0, 0, +d / 2, 0])

            else:
                RoC = - (optical_index - 1) * focal_length
                if 2 * RoC < d or (RoC **2 -(d/2)**2)**.5 -RoC < -e:
                    inkex.utils.debug("Focal power is too strong.")
                    return
                lens_path = arc_to_path([-d / 2, 0],
                                         [RoC, RoC, 0., 0, 1, +d / 2, 0])
            lens_path += [
                    [[+d / 2, 0], [+d / 2, 0], [+d / 2, -e]],
                    [[+d / 2, -e], [+d / 2, -e], [-d / 2, -e]],
                    [[+d / 2, -e], [-d / 2, -e], [-d / 2, +e]],
            ]
        elif opts.lens_type == 'bi_con':
            return

        lens = inkex.PathElement()
        lens.style = self.style
        closed_path = inkex.Path(inkex.CubicSuperPath([lens_path]))
        closed_path.close()
        lens.path = closed_path
        yield lens


if __name__ == '__main__':
    Lens().run()
