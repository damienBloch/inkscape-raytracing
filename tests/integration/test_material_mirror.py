from inkscape_raytracing.inkex.tester import ComparisonMixin, TestCase
from inkscape_raytracing.inkex.tester.filters import CompareNumericFuzzy

from inkscape_raytracing.render import Raytracing


class MirrorTest(ComparisonMixin, TestCase):
    effect_class = type("mirror_test", (Raytracing,), {})
    compare_file = "svg/mirror.svg"
    compare_filters = [CompareNumericFuzzy()]
    comparisons = [
        ("--id=g1553",),
    ]
