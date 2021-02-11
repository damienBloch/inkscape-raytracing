from inkex.tester import ComparisonMixin, TestCase

from render_raytracing import Tracer


class BeamTest(ComparisonMixin, TestCase):
    effect_class = type("", (Tracer,), {})
    compare_file = 'svg/beams.svg'
    comparisons = [
            (),
            ('--id=p1', '--id=p2', '--id=p3', '--id=p4', '--id=p5'),
            ('--id=g1',),
    ]
