from inkscape_raytracing.inkex.tester import ComparisonMixin, TestCase

from inkscape_raytracing.render import Raytracing


class BeamTest(ComparisonMixin, TestCase):
    effect_class = type("test_beam", (Raytracing,), {})
    compare_file = "svg/beams.svg"
    comparisons = [
        ("--id=layer1",),
    ]


