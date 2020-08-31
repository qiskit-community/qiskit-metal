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
===================================================
Toolbox_python (:mod:`qiskit_metal.toolbox_python`)
===================================================

.. currentmodule:: qiskit_metal.toolbox_python

This folder contains code that is general and not Metal specific.

Created on Tue May 14 17:13:40 2019

@author: Zlatko Minev (IBM)

Headings
---------------

.. autosummary::
    :toctree: ../stubs/

    Headings


Submodules
---------------

.. autosummary::
    :toctree: ../stubs/

    _logging
    display
    utility_functions

"""

from .attr_dict import Dict
from .display import format_dict_ala_z, Headings

#from .. import config
#if config.is_building_docs():
#    from . import _logging
#    from . import display
#    from . import utility_functions
