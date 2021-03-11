import inkex

from utils import get_description, clear_description, set_description


class SetMaterial(inkex.Effect):
    """Writes the chosen optical property in the element description"""

    def __init__(self):
        super().__init__()

        # only change the description for these objects
        self._filter_primitives = (inkex.PathElement, inkex.Line,
                                   inkex.Polyline, inkex.Polygon,
                                   inkex.Rectangle, inkex.Ellipse,
                                   inkex.Circle)

    def add_arguments(self, pars):
        pars.add_argument("--optical_material", type=str, default='none',
                          help="Name of the optical material to convert the "
                               "selection to.")
        pars.add_argument("--optical_index", type=float, default=1.5168)

    def effect(self) -> None:
        filter_ = self._filter_primitives + (inkex.Group,)
        for obj in self.svg.selection.filter(filter_).values():
            self.process_object(obj)

    def process_object(self, obj: inkex.BaseElement) -> None:
        if isinstance(obj, inkex.Group):
            self.process_group(obj)
        elif isinstance(obj, self._filter_primitives):
            self.process_shape(obj)

    def process_group(self, group: inkex.Group) -> None:
        """Splits the objects inside a group and treats them individually"""

        for obj in group:
            self.process_object(obj)

    def process_shape(self, obj: inkex.ShapeElement):
        """
        In the description of the element, replaces the optical properties
        with the new one.
        """
        name_alias = {
                "None": None, "Beam": 'beam', "Mirror": 'mirror',
                "Beam dump": 'beam_dump', "Beam splitter": 'beam_splitter',
                "Glass": 'glass'
        }
        desc = get_description(obj)
        new_desc = clear_description(desc)
        material_name = name_alias[self.options.optical_material]
        if material_name is not None:
            new_desc += f'optics:{material_name}'
            if material_name == 'glass':
                new_desc += f':{self.options.optical_index:.4f}'
        set_description(obj, new_desc)


if __name__ == '__main__':
    SetMaterial().run()
