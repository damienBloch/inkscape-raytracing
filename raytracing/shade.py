import numpy as np


class ShadeRec(object):
    """This object contains the information needed to process the collision
    between a ray and an object.

    :vartype hit_an_object: Bool
    :vartype local_hit_point: None or array_like of size 2
    :vartype normal: None or array_like of size 2
    :vartype travel_distance: float
    """

    def __init__(self):
        self.hit_an_object = False
        self.local_hit_point = None
        self.normal = None
        self.travel_distance = np.inf

    def __repr__(self):
        return f"ShadeRec({self.hit_an_object}, {self.local_hit_point}, " \
               f"{self.normal}, {self.travel_distance})"
