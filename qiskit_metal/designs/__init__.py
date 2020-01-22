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
@author: Zlatko Minev (IBM)
"""

from .. import Dict

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

from .design_base import DesignBase
from .design_planar import DesignPlanar
