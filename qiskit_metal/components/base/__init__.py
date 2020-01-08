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
@auhtor: Zlatko Minev
@date: 2019
"""
from ...toolbox_python.attr_dict import Dict
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


from .base import BaseComponent
