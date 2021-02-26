from raytracing.geometry.geometric_object import AABBox

def test_englobing_AABBox():
    A0 = AABBox([0, 0], [1, 2])
    A1 = AABBox([1, 0], [2, 1])

    englobing = AABBox.englobing_aabbox([A0, A1])
    assert englobing == AABBox([0, 0], [2, 2])