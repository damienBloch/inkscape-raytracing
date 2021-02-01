import numpy as np
from typing import Optional


class ShadeRec(object):
    """
    This object contains the information needed to process the collision
    between a ray and an object.
    """

    def __init__(self):
        self.hit_an_object: bool = False
        self.local_hit_point: Optional[np.ndarray] = None
        self.normal: Optional[np.ndarray] = None
        self.travel_dist: float = np.inf

    def __repr__(self):
        return f"ShadeRec({self.hit_an_object}, {self.local_hit_point}, " \
               f"{self.normal}, {self.travel_dist})"
