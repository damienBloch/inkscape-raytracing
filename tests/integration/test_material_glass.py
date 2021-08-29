from inkscape_raytracing.inkex.tester import ComparisonMixin, TestCase

from inkscape_raytracing.render import Raytracing


class GlassTest(ComparisonMixin, TestCase):
    effect_class = type("glass_test", (Raytracing,), {})
    compare_file = 'svg/glass.svg'
    comparisons = [
            ('--id=g1271',),
    ]
