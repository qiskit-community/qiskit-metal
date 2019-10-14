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
File contains defines the core two basic dicitonaries

Created 2019

@author: Zlatko K. Minev
"""


from .toolbox.addict import Dict

################################################################################
###
### Default Paramters
###

DEFAULT_OPTIONS = Dict()
r"""
DEFAULT_OPTIONS:
------------------------
    Dictionary of the needed options for all functions defined in this module.
    Each options should also have a default value.
"""
DEFAULT_OPTIONS['cpw'] = Dict(
    width='10um',
    gap='6um',
    mesh_width='6um',
    fillet='90um',
)


DEFAULT = Dict({
    'chip'         : 'main',
    'do_PerfE'     : True,  # applied p-erf E BC
    'do_cut'       : True,  # cut from ground plane
    'BC_individual': False, # Apply individual names ot each BC, otherwise requires BC_name
    'col_in_cond'  : (255,0,0), #(196,202,206), # Default color for the inner conductors 100,120,90
    'colors'       : Dict(
        ground_main = (100,120,140),  # lighter:  (196,202,206)
        ),
    'annots' : Dict( # annotaitons
        circ_connectors_ofst = [0.025,0.025],
        circ_connectors = dict( # called by ax.annotate
            color='r',
            arrowprops = dict(color='r', shrink=0.1, width=0.05, headwidth=0.1),
        )
    ),
    '_hfss' : Dict(
        do_mesh=True,  # do mesh rect draw and specify mesh size
    )
})
r"""
Default Paramters for many basic functions:
------------------------

:chip:           Default anme of chip to draw on. Not fully integrated everwhere.
                 TODO Many places still assume main or zero z.
:do_PerfE:       Applied p-erf E BC
:do_cut:         Cut from ground plane
:do_mesh:        Do mesh rect draw and specify mesh size
:BC_individual:  Apply individual names ot each BC, otherwise requires BC_name
:col_in_cond:    Default color for the inner conductors
.. math::

    n_{\mathrm{offset}} = \sum_{k=0}^{N-1} s_k n_k

.. sectionauthor:: Zlatko K Minev <zlatko.minev@ibm.com>
"""
#TODO: Updat the do_PerfE etxc. into hfss
