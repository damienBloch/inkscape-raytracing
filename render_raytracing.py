"""
Extension for rendering beams in 2D optics with Inkscape
"""

from typing import Tuple, List, Union, Iterable

import inkex
import numpy as np
from inkex.paths import Line, Move

import raytracing.geometry as geom
import raytracing.material as mat
from raytracing import World, OpticalObject, Ray
from utils import get_description, pairwise, get_optics_fields


def get_material(obj: inkex.ShapeElement) -> List[Union[mat.OpticMaterial,
                                                        mat.BeamSeed]]:
    """Extracts the optical material of an object from its description"""

    desc = get_description(obj)
    return materials_from_description(desc)


def get_absolute_path(obj: inkex.ShapeElement) -> inkex.CubicSuperPath:
    path = obj.to_path_element().path.to_absolute()
    transformed_path = path.transform(obj.composed_transform())
    return transformed_path.to_superpath()


def get_geometry(obj: inkex.ShapeElement) -> geom.GeometricObject:
    """
    Converts the geometry of inkscape elements to a form suitable for the
    ray tracing module
    """

    # Treats all objects as cubic Bezier curves. This treatment is exact
    # for most primitives except circles and ellipses that are only
    # approximated by Bezier curves.
    # TODO: implement exact representation for ellipses
    path = get_absolute_path(obj)
    composite_bezier = superpath_to_bezier_segments(path)
    return composite_bezier


def get_beams(element: inkex.ShapeElement) -> Iterable[Ray]:
    bezier_path = superpath_to_bezier_segments(get_absolute_path(element))
    for subpath in bezier_path:
        endpoint, tangent = subpath.endpoint_info()
        yield Ray(endpoint, tangent)


def materials_from_description(desc: str) -> List[Union[mat.OpticMaterial,
                                                        mat.BeamSeed]]:
    """Run through the description to extract the material properties"""

    materials = list()
    mat_name = {
            "beam_dump": mat.BeamDump, "mirror": mat.Mirror,
            "beam_splitter": mat.BeamSplitter, "beam": mat.BeamSeed,
            "glass": mat.Glass
    }
    for match in get_optics_fields(desc.lower()):
        material_type = match.group('material')
        prop = match.group('num')
        if material_type in mat_name:
            if material_type == "glass":  # only material with parameter
                materials.append(mat_name[material_type](float(prop)))
            else:
                materials.append(mat_name[material_type]())
    return materials


def superpath_to_bezier_segments(superpath: inkex.CubicSuperPath) \
        -> geom.CompositeCubicBezier:
    """
    Converts a superpath with a representation
    [Subpath0[handle0_0, point0, handle0_1], ...], ...]
    to a representation of consecutive bezier segments of the form
    CompositeCubicBezier([CubicBezierPath[CubicBezier[point0, handle0_1,
    handle1_0, point1], ...], ...]).
    """

    composite_bezier = list()
    for subpath in superpath:
        bezier_path = list()
        for (__, p0, p1), (p2, p3, __) in pairwise(subpath):
            bezier = geom.CubicBezier(np.array([p0, p1, p2, p3]))
            bezier_path.append(bezier)
        composite_bezier.append(geom.CubicBezierPath(bezier_path))
    return geom.CompositeCubicBezier(composite_bezier)


def raise_err_num_materials(obj):
    message = f"The element {obj.get_id()} has more than one optical " \
              f"material and will be ignored:\n{get_description(obj)}\n"
    inkex.utils.errormsg(message)


class Tracer(inkex.EffectExtension):
    """Renders the beams present in the document"""

    def __init__(self):
        super().__init__()
        self._world = World()
        self._beam_seeds = list()

        # Ray tracing is only implemented for the following inkex primitives
        self._filter_primitives = (inkex.PathElement, inkex.Line,
                                   inkex.Polyline, inkex.Polygon,
                                   inkex.Rectangle, inkex.Ellipse,
                                   inkex.Circle)

    def effect(self) -> None:
        """
        Loads the objects and outputs a svg with the beams after propagation
        """

        # In addition to the primitives handled, it is also necessary to
        # break the groups apart
        filter_ = self._filter_primitives + (inkex.Group,)
        for obj in self.svg.selection.filter(filter_).values():
            self.process_object(obj)

        self._document_as_border()

        if len(self._beam_seeds) > 0:
            self._beam_layer = self.add_render_layer()
            for seed in self._beam_seeds:
                if self.is_inside_document(seed["source"]):
                    generated = self._world.propagate_beams(
                            [[(seed["source"], 0)]])
                    for beam in generated:
                        self.plot_beam(beam, seed["node"])

    def add_render_layer(self):
        """
        Looks for an existing layer to render beams into and creates on if
        not already present
        """
        for element in self.document.iter():
            if element.label == 'rendered_beams':
                return element
        svg = self.document.getroot()
        layer = svg.add(inkex.Layer())
        layer.label = 'rendered_beams'
        return layer

    def process_object(self, obj: inkex.BaseElement) -> None:
        if isinstance(obj, inkex.Group):
            self.process_group(obj)
        elif isinstance(obj, self._filter_primitives):
            self.process_optical_object(obj)

    def process_optical_object(self, obj: inkex.ShapeElement) -> None:
        """
        Extracts properties and adds the object to the ray tracing data
        structure
        """

        materials = get_material(obj)
        if len(materials) > 1:
            raise_err_num_materials(obj)
        elif len(materials) == 1:
            material = materials[0]
            if isinstance(material, mat.BeamSeed):
                for ray in get_beams(obj):
                    self._beam_seeds.append({"source": ray, "node": obj})
            else:
                geometry = get_geometry(obj)
                opt_obj = OpticalObject(geometry, material)
                self._world.add_object(opt_obj)

    def process_group(self, group: inkex.Group) -> None:
        """Splits the objects inside a group and treats them individually"""

        for obj in group:
            self.process_object(obj)
        # TODO : broadcast the information in the group description to all
        #  children. At this point it is discarded.

    def _document_as_border(self) -> None:
        """
        Adds a beam blocking contour on the borders of the document to
        prevent the beams from going to infinity
        """

        svg = self.document.getroot()
        w = self.svg.unittouu(svg.get('width'))
        h = self.svg.unittouu(svg.get('height'))
        contour_geometry = geom.CompositeCubicBezier([geom.CubicBezierPath([
                geom.CubicBezier(np.array([[0, 0], [0, 0], [w, 0], [w, 0]])),
                geom.CubicBezier(np.array([[w, 0], [w, 0], [w, h], [w, h]])),
                geom.CubicBezier(np.array([[w, h], [w, h], [0, h], [0, h]])),
                geom.CubicBezier(
                        np.array([[0, h], [0, h], [0, 0], [0, 0]]))])])
        self._document_border = OpticalObject(contour_geometry, mat.BeamDump())
        self._world.add_object(self._document_border)

    def is_inside_document(self, ray: Ray) -> bool:
        return self._document_border.geometry.is_inside(ray)

    def plot_beam(self, beam: List[Tuple[Ray, float]],
                  node: inkex.ShapeElement) -> None:
        path = inkex.Path()
        if len(beam) > 0:
            path += [Move(beam[0][0].origin[0], beam[0][0].origin[1])]
            for ray, t in beam:
                p1 = ray.origin + t * ray.direction
                path += [Line(p1[0], p1[1])]
        element = self._beam_layer.add(inkex.PathElement())
        element.style = node.get("style")
        element.path = path.transform(-node.composed_transform())


if __name__ == '__main__':
    Tracer().run()
