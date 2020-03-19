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

'''
@date: 2019
@author: Zlatko K Minev
converted to v0.2: Thomas McConkey 2020-03-18


.. code-block::
     ________________________________
    |______ ____           __________|
    |      |____|         |____|     |
    |        __________________      |
    |       |                  |     |
    |       |__________________|     |
    |                 |              |
    |                 x              |
    |        _________|________      |
    |       |                  |     |
    |       |__________________|     |
    |        ______                  |
    |_______|______|                 |
    |________________________________|


'''


from copy import deepcopy

#from ... import DEFAULT, DEFAULT_OPTIONS, Dict, draw
#from ...renderers.renderer_ansys import draw_ansys
#from ...renderers.renderer_ansys.parse import to_ansys_units
#from .Metal_Qubit import Metal_Qubit

DEFAULT_OPTIONS['Metal_Transmon_Pocket.connectors'] = Dict(
    pad_gap='15um',
    pad_width='125um',
    pad_height='30um',
    pad_cpw_shift='5um',
    pad_cpw_extent='25um',
    cpw_width=DEFAULT_OPTIONS.cpw.width,
    cpw_gap=DEFAULT_OPTIONS.cpw.gap,
    cpw_extend='100um',  # how far into the ground to extend the CPW line from the coupling pads
    pocket_extent='5um',
    pocket_rise='65um',
    loc_W=+1,  # width location  only +-1
    loc_H=+1,  # height location only +-1
)