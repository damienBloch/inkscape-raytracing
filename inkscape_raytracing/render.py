"""
Extension for rendering beam_paths in 2D optics with Inkscape
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import singledispatchmethod
from typing import Iterable, Optional, Final

import inkex
import numpy
from inkex.paths import Line, Move

import raytracing.material
from desc_parser import get_optics_fields
from raytracing import Vector
from raytracing import World, OpticalObject, Ray, BeamPath
from raytracing.geometry import CubicBezier, CompoundGeometricObject
from raytracing.geometry import GeometricObject
from utils import pairwise


@dataclass
class BeamSeed:
    ray: Optional[Ray] = None
    parent: Optional[inkex.ShapeElement] = None


def get_unlinked_copy(clone: inkex.Use) -> Optional[inkex.ShapeElement]:
    """Creates a copy of the original with all transformations applied"""
    copy = clone.href.copy()
    copy.transform = clone.composed_transform() * copy.transform
    copy.style = clone.style + copy.style
    copy.getparent = clone.getparent
    return copy


def get_or_create_beam_layer(parent_layer: inkex.Layer) -> inkex.Layer:
    for child in parent_layer:
        if isinstance(child, inkex.Layer):
            if child.get("inkscape:label") == "generated_beams":
                return child
    new_layer = parent_layer.add(inkex.Layer())
    new_layer.label = "generated_beams"
    return new_layer


def plot_beam_path(beam_path: BeamPath, node: inkex.ShapeElement, layer: inkex.Layer):
    path = inkex.Path()
    if beam_path:
        first_ray = beam_path.first_line.ray
        path += [Move(first_ray.origin.x, first_ray.origin.y)]
        for line in beam_path:
            ray = line.ray
            p1 = ray.origin + line.length * ray.direction
            path += [Line(p1.x, p1.y)]
    element = layer.add(inkex.PathElement())
    # Need to convert to path to get the correct style for inkex.Use
    element.style = node.to_path_element().style
    element.path = path


def plot_beam_envelope(
    beam_path: BeamPath, node: inkex.ShapeElement, layer: inkex.Layer
):
    path1 = inkex.Path()
    path2 = inkex.Path()
    first_ray = beam_path.first_line.ray
    path1 += [Move(first_ray.origin.x, first_ray.origin.y)]
    # path2 += [Move(first_ray.origin.x, first_ray.origin.y)]
    for line in beam_path:
        for l in numpy.arange(0, line.length, 1):
            d = abs((line.ray.abcd[0, 0] + line.ray.abcd[1, 0] * l) * 0.750)
            p1 = (
                line.ray.origin
                + l * line.ray.direction
                + d * line.ray.direction.orthogonal()
            )
            p2 = (
                line.ray.origin
                + l * line.ray.direction
                - d * line.ray.direction.orthogonal()
            )
            path1 += [Line(p1.x, p1.y)]
            path2 += [Line(p2.x, p2.y)]
    # path2.reverse()
    path1 += path2[::-1]
    path1.close()
    element = layer.add(inkex.PathElement())
    element.style = node.to_path_element().style
    element.path = path1


class Raytracing(inkex.EffectExtension):
    """Extension to renders the beam_paths present in the document"""

    # Ray tracing is only implemented for the following inkex primitives
    filter_primitives: Final = (
        inkex.PathElement,
        inkex.Line,
        inkex.Polyline,
        inkex.Polygon,
        inkex.Rectangle,
        inkex.Ellipse,
        inkex.Circle,
    )

    def __init__(self):
        super().__init__()
        self.world = World()
        self.beam_seeds: list[BeamSeed] = list()

    def effect(self) -> None:
        """
        Loads the objects and outputs a svg with the beam_paths after propagation
        """

        # Can't set the border earlier because self.svg is not yet defined
        self.document_border = self.get_document_borders_as_beamdump()
        self.world.add(self.document_border)

        filter_ = self.filter_primitives + (inkex.Group, inkex.Use)
        for obj in self.svg.selection.filter(filter_):
            self.add(obj)

        for seed in self.beam_seeds:
            if self.is_inside_document(seed.ray):
                generated_paths = self.world.propagate_beams(seed.ray)
                for path in generated_paths:
                    try:
                        new_layer = get_or_create_beam_layer(
                            get_containing_layer(seed.parent)
                        )
                        # plot_beam_path(path, seed.parent, new_layer)
                        plot_beam_envelope(path, seed.parent, new_layer)
                    except LayerError as e:
                        inkex.utils.errormsg(e)

    @singledispatchmethod
    def add(self, obj):
        pass

    @add.register
    def _(self, group: inkex.Group):
        for child in group:
            self.add(child)

    @add.register
    def _(self, clone: inkex.Use):
        copy = get_unlinked_copy(clone)
        self.add(copy)

    for type in filter_primitives:

        @add.register(type)
        def _(self, obj):
            """
            Extracts properties and adds the object to the ray tracing data
            structure
            """
            material = get_material(obj)
            if material:
                if isinstance(material, BeamSeed):
                    for ray in get_beams(obj):
                        self.beam_seeds.append(BeamSeed(ray, parent=obj))
                else:
                    geometry = get_geometry(obj)
                    opt_obj = OpticalObject(geometry, material)
                    self.world.add(opt_obj)

    def get_document_borders_as_beamdump(self) -> OpticalObject:
        """
        Adds a beam blocking contour on the borders of the document to
        prevent the beam_paths from going to infinity
        """

        c1x, c1y, c2x, c2y = self.svg.get_viewbox()
        contour_geometry = CompoundGeometricObject(
            (
                CubicBezier(
                    Vector(c1x, c1y),
                    Vector(c1x, c1y),
                    Vector(c2x, c1y),
                    Vector(c2x, c1y),
                ),
                CubicBezier(
                    Vector(c2x, c1y),
                    Vector(c2x, c1y),
                    Vector(c2x, c2y),
                    Vector(c2x, c2y),
                ),
                CubicBezier(
                    Vector(c2x, c2y),
                    Vector(c2x, c2y),
                    Vector(c1x, c2y),
                    Vector(c1x, c2y),
                ),
                CubicBezier(
                    Vector(c1x, c2y),
                    Vector(c1x, c2y),
                    Vector(c1x, c1y),
                    Vector(c1x, c1y),
                ),
            )
        )
        return OpticalObject(contour_geometry, raytracing.material.BeamDump())

    def is_inside_document(self, ray: Ray) -> bool:
        return self.document_border.geometry.is_inside(ray)


def get_material(
    obj: inkex.ShapeElement,
) -> Optional[raytracing.material.OpticMaterial | BeamSeed]:
    """Extracts the optical material of an object from its description"""

    desc = obj.desc
    if desc is None:
        desc = ""
    materials = get_materials_from_description(desc)
    if len(materials) == 0:
        return None
    if len(materials) > 1:
        raise_err_num_materials(obj)
    elif len(materials) == 1:
        return materials[0]


def get_materials_from_description(
    desc: str,
) -> list[raytracing.material.OpticMaterial | BeamSeed]:
    """Run through the description to extract the material properties"""

    materials = list()
    class_alias = dict(
        beam_dump=raytracing.material.BeamDump,
        mirror=raytracing.material.Mirror,
        beam_splitter=raytracing.material.BeamSplitter,
        glass=raytracing.material.Glass,
        beam=BeamSeed,
    )
    for match in get_optics_fields(desc):
        material_type = match.group("material")
        prop_str = match.group("num")
        if material_type in class_alias:
            if material_type == "glass" and prop_str is not None:
                optical_index = float(prop_str)
                materials.append(class_alias[material_type](optical_index))
            else:
                materials.append(class_alias[material_type]())
    return materials


def raise_err_num_materials(obj):
    inkex.utils.errormsg(
        f"The element {obj.get_id()} has more than one optical material and will be"
        f" ignored:\n{obj.desc}\n"
    )


def get_geometry(obj: inkex.ShapeElement) -> GeometricObject:
    """
    Converts the geometry of inkscape elements to a form suitable for the
    ray tracing module
    """

    # Treats all objects as cubic Bezier curves. This treatment is exact
    # for most primitives except circles and ellipses that are only
    # approximated by Bezier curves.
    # TODO: implement exact representation for ellipses
    path = get_absolute_path(obj)
    composite_bezier = convert_to_composite_bezier(path)
    return composite_bezier


def get_absolute_path(obj: inkex.ShapeElement) -> inkex.CubicSuperPath:
    path = obj.to_path_element().path.to_absolute()
    transformed_path = path.transform(obj.composed_transform())
    return transformed_path.to_superpath()


def get_beams(element: inkex.ShapeElement) -> Iterable[Ray]:
    """
    Returns a beam with origin at the endpoint of the path and tangent to
    the path
    """
    bezier_path = convert_to_composite_bezier(get_absolute_path(element))
    for sub_path in bezier_path:
        last_segment = sub_path[-1]
        endpoint = last_segment.eval(1)
        tangent = -last_segment.tangent(1)
        yield Ray(endpoint, tangent)


def convert_to_composite_bezier(
    superpath: inkex.CubicSuperPath,
) -> CompoundGeometricObject:
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
            bezier = CubicBezier(Vector(*p0), Vector(*p1), Vector(*p2), Vector(*p3))
            bezier_path.append(bezier)
        composite_bezier.append(CompoundGeometricObject(bezier_path))
    return CompoundGeometricObject(composite_bezier)


def get_containing_layer(obj: inkex.BaseElement) -> inkex.Layer:
    try:
        return obj.ancestors().filter(inkex.Layer)[0]
    except IndexError:
        raise LayerError(f"Object '{obj.get_id()}' is not inside a layer.")


class LayerError(RuntimeError):
    pass


if __name__ == "__main__":
    Raytracing().run()
