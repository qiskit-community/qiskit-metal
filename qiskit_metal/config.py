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
Created 2019

File contains some config definitions. Mostly internal.

@author: Zlatko K. Minev
"""

import logging

from .toolbox.addict import Dict
from ._base_dicts import DEFAULT_OPTIONS, DEFAULT # pylint: disable=unused-import

####################################################################################
# GUI RELATED CONFIG
###


"""
CREATE_METAL_CLASSES
    Name of classes that will be available to be created in the GUI
    Assumes that the module file name is the same as the class name.
    For example, provided
        'qiskit_metal.objects.Metal_Transmon_Pocket'
    it will basically perform:
        from qiskit_metal.objects.Metal_Transmon_Pocket import  Metal_Transmon_Pocket
"""
CREATE_METAL_CLASSES = [
    'qiskit_metal.objects.qubits.Metal_Transmon_Pocket',
    'qiskit_metal.objects.qubits.Metal_Crossmon_Transmon_Pocket',
    'qiskit_metal.objects.interconnects.Metal_cpw_connect',
    'qiskit_metal.objects.qubits.Metal_Transmon_Pocket_CL']


# Tips for the gui
tips = [
    'Right clicking the tree elements allows you to do neat things.',
    '''You can show all connector names on the plot by clicking the connector\
 icon in the plot toolbar.''',

    '''The gui and the python code work synchronously. If you modify something\
 in the gui, it will be reflected in your python interperter and vice versa.\
 Note that the gui does not automatically refresh on all events if you update\
 variables from the python interperter.''',

    '''Changed some object parameters? Click the <b>Remake</b> button in the main\
 toolbar to recreate the polygons.'''
]


####################################################################################
# LOGGING RELATED CONFIG
###
_log_format = '%(asctime)s %(levelname)s [%(funcName)s]: %(message)s'
_log_datefmt = '%I:%M%p %Ss'

# GUI Logging
log_lines = 300
_gui = Dict(
    log_style=".DEBUG {color: green;}\n.WARNING,.ERROR,.CRITICAL {color: red;}\n.ERROR,.CRITICAL {font-weight: bold;}\n"
)