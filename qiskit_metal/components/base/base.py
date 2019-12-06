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
This is the main module that defines what a component is in Qiskit Metal.
See the docstring of BaseComponent
    >> ?BaseComponent

@author: Zlatko Minev, Thomas McConekey, ... (IBM)
@date: 2019
"""

from ...toolbox_python.attr_dict import Dict
# from ..elements.base import


__all__ = ['is_component', 'BaseComponent']


def is_component(obj):
    """Check if an object is an instance of `BaseComponent`.

    The problem is that the `isinstance` built-in method fails
    when this module is reloaded.

    Arguments:
        obj {[object]} -- Test this object

    Returns:
        [bool] -- True if is a Metal object
    """
    if isinstance(obj, Dict):
        return False

    return hasattr(obj, '__i_am_component__')


class BaseComponent():

    # Dummy private attribute used to check if an instanciated object is
    # indeed a BaseComponent class. The problem is that the `isinstance`
    # built-in method fails when this module is reloaded.
    # Used by `is_component` to check.
    __i_am_component__ = True

    def __init__(self, name: str, design):
        self.name = name
        self.design = design  # parent

        self.elements = Dict()

    def get_all_geom(self):
        """
        Get all shapely geometry as a dict
        """
        return {elem.full_name : elem.geom for name, elem in self.elements}
