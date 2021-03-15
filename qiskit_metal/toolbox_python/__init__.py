# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
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

Headings
---------------

.. autosummary::
    :toctree: ../stubs/

    MetalTutorialMagics
    Headings
    Color


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
from .display import MetalTutorialMagics
from .display import Color
