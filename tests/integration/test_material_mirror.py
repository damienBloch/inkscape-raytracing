from inkex.tester import ComparisonMixin, TestCase

from render_raytracing import Tracer


class MirrorTest(ComparisonMixin, TestCase):
    effect_class = type("mirror_test", (Tracer,), {})
    compare_file = 'svg/mirror.svg'
    comparisons = [
            ('--id=g1553',),
    ]
