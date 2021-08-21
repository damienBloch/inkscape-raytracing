from inkex.tester import ComparisonMixin, TestCase

from inkscape_raytracing.render import Tracer


class BeamTest(ComparisonMixin, TestCase):
    effect_class = type("test_beam", (Tracer,), {})
    compare_file = "svg/beams.svg"
    comparisons = [
        ("--id=g260",),
    ]


