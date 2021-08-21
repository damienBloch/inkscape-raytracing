from inkex.tester import ComparisonMixin, TestCase

from inkscape_raytracing.render import Tracer


class GlassTest(ComparisonMixin, TestCase):
    effect_class = type("glass_test", (Tracer,), {})
    compare_file = 'svg/glass.svg'
    comparisons = [
            ('--id=g1271',),
    ]
