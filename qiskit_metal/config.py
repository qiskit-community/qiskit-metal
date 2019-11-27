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
# pylint: disable=invalid-name

"""
Created 2019

File contains some config definitions. Mostly internal.

@author: Zlatko K. Minev
"""

from .toolbox.attribute_dictionary import Dict
from ._defaults import DEFAULT_OPTIONS, DEFAULT  # pylint: disable=unused-import

####################################################################################
# RENDERER CONFIG

# Define the renderes to load. Just provide the module names here.
# The renderes will be loaded at ...
renderers_to_load = dict(
    metal='qiskit_metal.renderers.metal',
    ansys='qiskit_metal.renderers.ansys',
    gds='qiskit_metal.renderers.gds'
)

####################################################################################
# GUI CONFIG

"""
GUI_CONFIG

    load_metal_modules
    ---------------------------
    Name of class folders that contain modules that will be available to be
    created in the GUI

    Conventions:
    Assumes that the module file name is the same as the class name contained in it.
    For example, provided `qiskit_metal.qubits` has `Metal_Transmon_Pocket.py`, the
    gui will do
        `from qiskit_metal.qubits.Metal_Transmon_Pocket import Metal_Transmon_Pocket`

    tips
    ---------------------------
    Tips that the user can define to show in the gui. These rotate each time the gui is started.
"""
GUI_CONFIG = Dict(

    load_metal_modules=Dict(
        Qubits='qiskit_metal.objects.qubits',
        Interconnects='qiskit_metal.objects.interconnects',
        Connectors='qiskit_metal.objects.connectors'

    ),

    exclude_metal_classes=['Metal_Qubit'],

    tips=[
        'Right clicking the tree elements allows you to do neat things.',

        'You can show all connector names on the plot by clicking the connector'
        'icon in the plot toolbar.',

        'The gui and the python code work synchronously. If you modify something'
        'in the gui, it will be reflected in your python interperter and vice versa.'
        'Note that the gui does not automatically refresh on all events if you update'
        'variables from the python interperter.',

        'Changed some object parameters? Click the <b>Remake</b> button in the main'
        'toolbar to recreate the polygons.'
    ],

    logger=Dict(
        style=".DEBUG {color: green;}\n.WARNING,.ERROR,.CRITICAL {color: red;}\n.'\
                'ERROR,.CRITICAL {font-weight: bold;}\n",
        num_lines=500,
    ),

)

log = Dict(
    format='%(asctime)s %(levelname)s [%(funcName)s]: %(message)s',
    datefmt='%I:%M%p %Ss'
)


####################################################################################
# USER CONFIG
