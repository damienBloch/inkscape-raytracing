"""
Extension for rendering beams in 2D optics with Inkscape
"""

import itertools
import re
from typing import TypeVar, Iterator, Tuple, List, Union

import inkex
from inkex.paths import Line, Move
import numpy as np

import raytracing.geometry as geom
import raytracing.material as mat
from raytracing import World, OpticalObject, Ray


T = TypeVar('T')


def plot_beam(beam: List[Tuple[Ray, float]], node: inkex.BaseElement) -> None:
    path = inkex.Path()
    for ray, t in beam:
        p0 = ray.origin
        p1 = ray.origin + t * ray.direction
        path += [Move(p0[0], p0[1]), Line(p1[0], p1[1])]

    element = node.getparent().add(inkex.PathElement())
    element.style = node.get("style")
    element.path = path


def pairwise(iterable: Iterator[T]) -> Iterator[Tuple[T, T]]:
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def get_material(obj: inkex.ShapeElement) -> List[Union[mat.OpticMaterial,
                                                        mat.BeamSeed]]:
    """Extracts the optical material of an object from its description"""

    desc = get_description(obj)
    return materials_from_description(desc)


def get_geometry(obj: inkex.ShapeElement) -> geom.GeometricObject:
    """
    Converts the geometry of inkscape elements to a form suitable for the
    ray tracing module
    """

    # Treats all objects as cubic Bezier curves. This treatment is exact
    # for most primitives except circles and ellipses that are only
    # approximated by Bezier curves.
    # TODO: implement exact representation for ellipses
    superpath = inkex.CubicSuperPath(obj.path.to_absolute())
    composite_bezier = superpath_to_bezier_segments(superpath)
    return composite_bezier


def get_description(element: inkex.BaseElement) -> str:
    for child in element.getchildren():
        if child.tag == inkex.addNS('desc', 'svg'):
            return child.text
    return ''


def get_beam(element: inkex.PathElement) -> Ray:
    # TODO: Find a better way to extract beam characteristics.
    #  The current approach will give weird results for paths that are not
    #  lines.
    end_points = np.array([x for x in element.path.to_absolute().end_points])
    origin = end_points[0]
    direction = end_points[1]-end_points[0]
    return Ray(origin, direction)


def materials_from_description(desc: str) -> List[Union[mat.OpticMaterial,
                                                        mat.BeamSeed]]:
    """Parses the description to extract the material properties"""

    pattern = "optics *: *([a-z,_]*)(?::([0-9]+(?:.[0-9])?))?"
    fields = re.findall(pattern, desc.lower())

    materials = list()
    for material_type, prop in fields:
        if material_type == "beam_dump":
            materials.append(mat.BeamDump())
        elif material_type == "beam":
            materials.append(mat.BeamSeed())
        # TODO: add all other types of materials
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

    composite_bezier = geom.CompositeCubicBezier()
    for subpath in superpath:
        bezier_path = geom.CubicBezierPath()
        for (__, p0, p1), (p2, p3, __) in pairwise(subpath):
            bezier = geom.CubicBezier(np.array([p0, p1, p2, p3]))
            bezier_path.add_bezier(bezier)
        composite_bezier.add_subpath(bezier_path)
    return composite_bezier


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

        for seed in self._beam_seeds:
            generated = self._world.propagate_beams([[(seed["source"], -1)]])
            for beam in generated:
                plot_beam(beam, seed["node"])

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
            geometry = get_geometry(obj)
            if isinstance(material, mat.BeamSeed):
                ray = get_beam(obj.to_path_element())
                self._beam_seeds.append({"source": ray, "node": obj})
            else:
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
            geom.CubicBezier(np.array([[0, h], [0, h], [0, 0], [0, 0]]))])])
        self._document_border = OpticalObject(contour_geometry, mat.BeamDump())
        self._world.add_object(self._document_border)


if __name__ == '__main__':
    Tracer().run()
