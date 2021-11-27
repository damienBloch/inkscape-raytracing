from typing import Optional

import numpy as np




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

        from .geometry import GeometricObject

        self.hit_geometry: Optional[GeometricObject] = None

    def __repr__(self):
        return (
            f"ShadeRec({self.hit_an_object}, {self.local_hit_point}, "
            f"{self.normal}, {self.travel_dist})"
        )

    def set_normal_same_side(self, point: np.ndarray):
        if self.normal is None:
            raise RuntimeError("Can't find normal orientation if not already defined.")
        elif self.local_hit_point is None:
            raise RuntimeError(
                "Can't find normal orientation if hit point not defined."
            )
        elif np.dot(self.normal, self.local_hit_point - point) > 0:
            self.normal = -self.normal
