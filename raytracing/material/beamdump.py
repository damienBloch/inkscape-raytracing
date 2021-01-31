from .optic_material import OpticMaterial


class BeamDump(OpticMaterial):
    """Material absorbing all beams that hit it"""

    def __init__(self):
        super().__init__()

    def __repr__(self):
        return "BeamDump()"
