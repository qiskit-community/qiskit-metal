# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Module containing all Qiskit Metal designs.

@date: 2019
@author: Zlatko Minev, ... (IBM)
"""
import numpy as np
from .. import Dict
from .. import draw
#from .. import config

def is_design(obj):
    """Check if an object is a Metal Design, i.e., an instance of
     `DesignBase`.

    The problem is that the `isinstance` built-in method fails
    when this module is reloaded.

    Arguments:
        obj {[object]} -- Test this object

    Returns:
        [bool] -- True if is a Metal design
    """
    if isinstance(obj, Dict):
        return False

    return hasattr(obj, '__i_am_design__')

class DesignBase():
    """
    DesignBase is the base class for Qiskit Metal Designs.
    A design is the most top-level object in all of Qiskit Metal.
    """


    # Dummy private attribute used to check if an instanciated object is
    # indeed a DesignBase class. The problem is that the `isinstance`
    # built-in method fails when this module is reloaded.
    # Used by `is_design` to check.
    __i_am_design__ = True

    def __init__(self):
        pass  # super().__init__()


####################################################################################
###
# Connector
# TODO: Decide how to handle this.
#   Should this be a class?
#   Should we keep function here or just move into design?

def make_connector(points: list, flip=False, chip='main'):
    """
    Works in user units.

    Arguments:
        points {[list of coordinates]} -- Two points that define the connector

    Keyword Arguments:
        flip {bool} -- Flip the normal or not  (default: {False})
        chip {str} -- Name of the chip the connector sits on (default: {'main'})

    Returns:
        [type] -- [description]
    """
    assert len(points) == 2

    # Get the direction vector, the unit direction vec, and the normal vector
    vec_dist, vec_dist_unit, vec_normal = draw.get_vec_unit_norm(points)

    if flip:
        vec_normal = -vec_normal

    return Dict(
        points=points,
        middle=np.sum(points, axis=0)/2.,
        normal=vec_normal,
        tangent=vec_dist_unit,
        width=np.linalg.norm(vec_dist),
        chip=chip
    )
