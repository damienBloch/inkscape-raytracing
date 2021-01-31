"""
Extension for rendering beams in 2D optics with Inkscape
"""

import re
import itertools
import inkex
import numpy as np
import raytracing.material as mat
import raytracing.geometry as geom
from raytracing import World, OpticalObject, Ray


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def get_material(obj):
    """Extracts the optical material of an object from its description

    :type obj: inkex.ShapeElement
    :rtype: list of OpticMaterial
    """

    desc = get_description(obj)
    return materials_from_description(desc)


def get_geometry(obj):
    """
    Converts the geometry of inkscape elements to a form suitable for the
    ray tracing module

    :type obj: inkex.ShapeElement
    :rtype: GeometricObject
    """

    # Treats all objects as cubic Bezier curves. This treatment is exact
    # for all primitives except circles and ellipses that are only
    # approximated by Bezier curves.
    # TODO: implement exact representation for ellipses
    superpath = inkex.CubicSuperPath(obj.path.to_absolute())
    composite_bezier = superpath_to_bezier_segments(superpath)
    return composite_bezier


def get_description(element):
    """
    :type element: inkex.BaseElement
    :rtype: str
    """

    for child in element.getchildren():
        if child.tag == inkex.addNS('desc', 'svg'):
            return child.text
    return ''


def get_beam(element):
    """
    :type element: inkex.PathElement
    :rtype: Ray
    """

    # TODO: find a better way to extract beam characteristics
    end_points = np.array([x for x in element.path.to_absolute().end_points])
    origin = end_points[0]
    direction = end_points[1]-end_points[0]
    return Ray(origin, direction)


def materials_from_description(desc):
    """Parses the description to extract the material properties

    :type desc: str
    :rtype: list of OpticalMaterial
    """

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


def superpath_to_bezier_segments(superpath):
    """
    Converts a superpath with a representation
    [Subpath0[handle0_0, point0, handle0_1], ...], ...]
    to a representation of consecutive bezier segments of the form
    CompositeCubicBezier([CubicBezierPath[CubicBezier[point0, handle0_1,
    handle1_0, point1], ...], ...]).

    :rtype: CompositeCubicBezier
    """

    composite_bezier = geom.CompositeCubicBezier()
    for subpath in superpath:
        bezier_path = geom.CubicBezierPath()
        for (__, p0, p1), (p2, p3, __) in pairwise(subpath):
            bezier = geom.CubicBezier([p0, p1, p2, p3])
            bezier_path.add_bezier(bezier)
        composite_bezier.add_subpath(bezier_path)
    return composite_bezier


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

    def effect(self):
        """
        Loads the objects and outputs a svg with the beams after propagation
        """

        # In addition to the primitives handled, it is also necessary to
        # break the groups apart
        filter_ = self._filter_primitives + (inkex.Group,)
        for obj in self.svg.selection.filter(filter_).values():
            self.process_object(obj)
        self._document_as_border()
        for beam in self._beam_seeds:
            self._world.propagate_beam(beam["source"])

    def process_object(self, obj):
        """Add the object to the ray tracing data structure"""
        if isinstance(obj, inkex.Group):
            self.process_group(obj)
        elif isinstance(obj, self._filter_primitives):
            materials = get_material(obj)
            if len(materials) > 1:
                message = f"The element \"{obj.get_id()}\" has more than  " \
                          f"one optical material and will be ignored:\n" \
                          f"{get_description(obj)}\n"
                inkex.utils.errormsg(message)
            elif len(materials) == 1:
                geometry = get_geometry(obj)
                if isinstance(materials[0], mat.BeamSeed):
                    ray = get_beam(obj)
                    self._beam_seeds.append({"source": ray, "node": obj})
                else:
                    opt_obj = OpticalObject(geometry, materials[0])
                    self._world.add_object(opt_obj)

    def process_group(self, group):
        """Splits the objects inside a group and treats them individually"""

        for obj in group:
            self.process_object(obj)
        # TODO : broadcast the information in the group description to all
        #  children, it is discarded for now

    def _document_as_border(self):
        """
        Adds a beam blocking contour on the borders of the document to
        prevent the beams from going to infinity
        """

        svg = self.document.getroot()
        w = self.svg.unittouu(svg.get('width'))
        h = self.svg.unittouu(svg.get('height'))
        contour_geometry = geom.CompositeCubicBezier([geom.CubicBezierPath([
            geom.CubicBezier([[0, 0], [0, 0], [w, 0], [w, 0]]),
            geom.CubicBezier([[w, 0], [w, 0], [w, h], [w, h]]),
            geom.CubicBezier([[w, h], [w, h], [0, h], [0, h]]),
            geom.CubicBezier([[0, h], [0, h], [0, 0], [0, 0]])])])
        self._document_border = OpticalObject(contour_geometry, mat.BeamDump())
        self._world.add_object(self._document_border)


if __name__ == '__main__':
    Tracer().run()
