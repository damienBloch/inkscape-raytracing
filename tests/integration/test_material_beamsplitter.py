from inkscape_raytracing.inkex.tester import ComparisonMixin, TestCase

from inkscape_raytracing.render import Tracer


class BeamSplitterTest(ComparisonMixin, TestCase):
    effect_class = type("beamsplitter_test", (Tracer,), {})
    compare_file = 'svg/beamsplitter.svg'
    comparisons = [
            ('--id=g1116',),
    ]
