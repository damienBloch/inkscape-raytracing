from inkscape_raytracing.raytracing.geometry import AABBox, Point


def test_englobing_AABBox():
    A0 = AABBox(Point(0, 0), Point(1, 2))
    A1 = AABBox(Point(1, 0), Point(2, 1))

    englobing = AABBox.englobing((A0, A1))
    assert englobing == AABBox(Point(0, 0), Point(2, 2))

