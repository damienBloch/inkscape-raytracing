"""
Extension for rendering beams in 2D optics with Inkscape
"""

from typing import List, Union, Iterable, Optional

import inkex
import numpy as np
from inkex.paths import Line, Move

import raytracing.geometry as geom
import raytracing.material as mat
from raytracing import World, OpticalObject, Ray
from utils import get_description, pairwise, get_optics_fields


class Tracer(inkex.EffectExtension):
    """Extension to renders the beams present in the document"""

    def __init__(self):
        super().__init__()
        self._world = World()
        self._beam_seeds = list()

        # Ray tracing is only implemented for the following inkex primitives
        self._filter_primitives = (inkex.Group, inkex.Use,
                                   inkex.PathElement, inkex.Line,
                                   inkex.Polyline, inkex.Polygon,
                                   inkex.Rectangle, inkex.Ellipse,
                                   inkex.Circle,)

    def effect(self) -> None:
        """
        Loads the objects and outputs a svg with the beams after propagation
        """

        for obj in self.svg.selection.filter(self._filter_primitives).values():
            self.process_object(obj)

        self._document_as_border()

        if len(self._beam_seeds) > 0:
            self._beam_layer = self.add_render_layer()
            for seed in self._beam_seeds:
                if self.is_inside_document(seed['source']):
                    generated = self._world.propagate_beams(seed['source'])
                    for beam in generated:
                        self.plot_beam(beam, seed['node'])

    def process_object(self, obj: inkex.BaseElement) -> None:
        if isinstance(obj, self._filter_primitives):
            if isinstance(obj, inkex.Group):
                self.process_group(obj)
            elif isinstance(obj, inkex.Use):
                self.process_clone(obj)
            else:
                self.process_optical_object(obj)

    def process_group(self, group: inkex.Group):
        for child in group:
            self.process_object(child)

    def process_clone(self, clone: inkex.Use):
        copy = self.clone_unlinked_copy(clone)
        self.process_object(copy)

    def clone_unlinked_copy(self, clone: inkex.Use) \
            -> Optional[inkex.ShapeElement]:
        """Creates a copy of the original with all transformations applied"""
        ref = clone.get('xlink:href')
        if ref is None:
            return None
        else:
            href = self.svg.getElementById(ref.strip('#'))
            copy = href.copy()
            copy.transform = clone.composed_transform() * copy.transform
            copy.style = clone.style + copy.style
            return copy

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
                    self._beam_seeds.append(dict(source=ray, node=obj))
            else:
                geometry = get_geometry(obj)
                opt_obj = OpticalObject(geometry, material)
                self._world.add_object(opt_obj)

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

    def add_render_layer(self):
        """
        Looks for an existing layer to render beams into and creates one if
        not already present.
        """
        for element in self.document.iter():
            if element.get('inkscape:label') == 'rendered_beams':
                return element
        svg = self.document.getroot()
        layer = svg.add(inkex.Layer())
        layer.label = 'rendered_beams'
        return layer

    def is_inside_document(self, ray: Ray) -> bool:
        return self._document_border.geometry.is_inside(ray)

    def plot_beam(self, beam: List[Ray], node: inkex.ShapeElement) -> None:
        path = inkex.Path()
        if len(beam) > 0:
            path += [Move(beam[0].origin[0], beam[0].origin[1])]
            for ray in beam:
                p1 = ray.origin + ray.travel * ray.direction
                path += [Line(p1[0], p1[1])]
        element = self._beam_layer.add(inkex.PathElement())
        # Need to convert to path to get the correct style for inkex.Use
        element.style = node.to_path_element().style
        element.path = path


def get_material(obj: inkex.ShapeElement) -> List[Union[mat.OpticMaterial,
                                                        mat.BeamSeed]]:
    """Extracts the optical material of an object from its description"""

    desc = get_description(obj)
    return materials_from_description(desc)


def materials_from_description(desc: str) -> List[Union[mat.OpticMaterial,
                                                        mat.BeamSeed]]:
    """Run through the description to extract the material properties"""

    materials = list()
    class_alias = dict(beam_dump=mat.BeamDump, mirror=mat.Mirror,
                       beam_splitter=mat.BeamSplitter, beam=mat.BeamSeed,
                       glass=mat.Glass)
    for match in get_optics_fields(desc.lower()):
        material_type = match.group('material')
        prop_str = match.group('num')
        if material_type in class_alias:
            if material_type == 'glass' and prop_str is not None:
                optical_index = float(prop_str)
                materials.append(class_alias[material_type](optical_index))
            else:
                materials.append(class_alias[material_type]())
    return materials


def raise_err_num_materials(obj):
    message = f"The element {obj.get_id()} has more than one optical " \
              f"material and will be ignored:\n{get_description(obj)}\n"
    inkex.utils.errormsg(message)


def get_beams(element: inkex.ShapeElement) -> Iterable[Ray]:
    """
    Returns a beam with origin at the endpoint of the path and tangent to
    the path
    """
    bezier_path = superpath_to_bezier_segments(get_absolute_path(element))
    for subpath in bezier_path:
        endpoint, tangent = subpath.endpoint_info()
        yield Ray(endpoint, tangent)


def get_absolute_path(obj: inkex.ShapeElement) -> inkex.CubicSuperPath:
    path = obj.to_path_element().path.to_absolute()
    transformed_path = path.transform(obj.composed_transform())
    return transformed_path.to_superpath()


def superpath_to_bezier_segments(
        superpath: inkex.CubicSuperPath
) -> geom.CompositeCubicBezier:
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


if __name__ == '__main__':
    Tracer().run()
