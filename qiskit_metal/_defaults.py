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
File contains basic dicitonaries.

Created 2019

@author: Zlatko K. Minev
"""

from .toolbox_python.attr_dict import Dict

################################################################################
# Default Paramters

DEFAULT_OPTIONS = Dict(
    cpw=Dict(
        width='10um',
        gap='6um',
        mesh_width='6um',
        fillet='90um',
    )
)
r"""
DEFAULT_OPTIONS:
------------------------
    Dictionary of the needed options for all functions defined in this module.
    Each options should also have a default value.

    This dictionary pointer should not be overwritten. Rather, update the dictionary values.
"""


DEFAULT = Dict(
    units='mm',
    chip='main',
    buffer_resolution=16, # for shapely buffer
    buffer_mitre_limit=5.0,
)
r"""
Default paramters for many basic functions:
------------------------

:chip:           Default name of chip to draw on.

.. sectionauthor:: Zlatko K Minev <zlatko.minev@ibm.com>
"""
