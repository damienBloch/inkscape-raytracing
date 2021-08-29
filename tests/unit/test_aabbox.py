from inkscape_raytracing.raytracing import Vector
from inkscape_raytracing.raytracing.geometry import AABBox


def test_englobing_AABBox():
    A0 = AABBox(Vector(0, 0), Vector(1, 2))
    A1 = AABBox(Vector(1, 0), Vector(2, 1))

    englobing = AABBox.englobing((A0, A1))
    assert englobing == AABBox(Vector(0, 0), Vector(2, 2))

