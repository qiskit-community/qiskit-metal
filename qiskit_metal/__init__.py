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

# pylint: disable=wrong-import-order

"""
Main Qiskit Metal public functionality.

Created on Tue May 14 17:13:40 2019

@author: Zlatko K. Minev
"""

##############################################################################
### Setup logging

from .toolbox.logging import logging, setup_logger
from . import config

logger = setup_logger('Metal', config._log_format, config._log_datefmt)
if 1:
    #TODO: remove this dependency
    import matplotlib as mpl
    mpl.rcParams['toolbar'] = 'toolmanager'
    __log = logging.getLogger('matplotlib.backend_managers')
    __log.setLevel(logging.ERROR)
    del __log
del setup_logger

__author__ = 'Zlatko K. Minev'
__version__ = '0.1.0'


##############################################################################
### Imports for user

from .toolbox.attribute_dictionary import Dict
from .config import DEFAULT, DEFAULT_OPTIONS
from .toolbox.utility_functions import copy_update
#from .toolbox.parsing import parse_value

# Objects
from . import objects
from .objects.base_objects.Metal_Object import Metal_Object
from .objects.base_objects.Metal_Utility import is_metal_object
from .objects.interconnects.Metal_cpw_connect import Metal_cpw_connect
from .objects.qubits.Metal_Transmon_Pocket import Metal_Transmon_Pocket
from .objects.qubits.Metal_Transmon_Cross import Metal_Transmon_Cross
from .backend.import_export import save_metal, load_metal


# Design
from .objects.base_objects.Metal_Utility import is_metal_design
from .objects.base_objects.Metal_Design_Planar import Design_Planar

from . import draw_functions
from . import draw_cpw
from . import draw_utility
from . import draw_hfss

# Guis
from ._gui import Metal_gui
#from .toolbox.mpl_interaction import figure_pz  # used for interactive figures

from .toolbox.utility_functions import display_options

global design #setting design to be global for easy access to necessary parameters through out all functions