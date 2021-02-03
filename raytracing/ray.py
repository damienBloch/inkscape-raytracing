import numpy as np


def orthogonal(vec):
    """Returns an orthogonal vector while conserving the norm"""

    return np.array([-vec[1], vec[0]])


class Ray(object):
    """This class implements a 2D line with an origin point and a direction.

    :ivar origin: point from which the beam starts
    :vartype origin: array_like of size 2
    :ivar direction: vector pointing in the direction of the beam. If its
        norm is not 1, it will be rescaled to be a unit vector
    :vartype direction: array_like of size 2
    """

    def __init__(self, origin, direction):
        self.origin: np.ndarray = np.array(origin)
        self.direction: np.ndarray = \
            np.array(direction)/np.linalg.norm(direction)

    def __repr__(self):
        return f"Ray({self.origin}, {self.direction})"

    # If a beam hits an object before having traveled a minimum distance
    # from its origin, the collision is ignored. This prevents infinite
    # collision in case the origin of a beam is on the surface of an object
    min_travel: float = 1e-8
