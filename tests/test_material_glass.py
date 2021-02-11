from inkex.tester import ComparisonMixin, TestCase

from render_raytracing import Tracer


class GlassTest(ComparisonMixin, TestCase):
    effect_class = type("glass_test", (Tracer,), {})
    compare_file = 'svg/glass.svg'
    comparisons = [
            ('--id=g1',),
    ]
