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
# pylint: disable=wrong-import-position

"""
Main Qiskit Metal public functionality.

Created on Tue May 14 17:13:40 2019

@author: Zlatko K. Minev
"""

__author__ = 'Zlatko Minev, Thomas McConkey, and them IBM Quantum Team'
__version__ = '0.05.1'

##############################################################################
### INTERNAL SETUP

## Setup logging

from .toolbox.logging import logging, setup_logger
from . import config

logger = setup_logger('Metal', config.log.format, config.log.datefmt)
del setup_logger

## Setup logging for GUI mpl
#TODO: remove this dependency - needed for gui at the moment

import matplotlib as mpl
mpl.rcParams['toolbar'] = 'toolmanager'
__LOG = logging.getLogger('matplotlib.backend_managers')
__LOG.setLevel(logging.ERROR)
del __LOG
del logging


##############################################################################
### Imports for user

# Core classes and default dictionaries
from .toolbox.attr_dict import Dict
from .config import DEFAULT, DEFAULT_OPTIONS

# Core class check functions
from .components import is_component
from .components import is_element
from .designs import is_design

# Core Modules for user to use
from . import designs
from . import components
from . import draw
from . import renderers
from . import analyses
from . import toolbox
from . import toolbox_metal

# Metal GUI
from ._gui import Metal_gui

# Utility functions
from .toolbox.utility_functions import copy_update
from .toolbox.utility_functions import display_options
