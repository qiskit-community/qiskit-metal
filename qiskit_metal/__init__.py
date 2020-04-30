# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019-202.
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
Qiskit Metal main public functionality.

Created on Tue May 14 17:13:40 2019
@author: Zlatko K. Minev
"""
__version__ = '0.2.01'
__license__ = "Apache 2.0"
__copyright__= 'Copyright IBM 2019-2020'
__author__ = 'Zlatko Minev, Thomas McConkey, and them IBM Quantum Team'
__status__ = "Development"

# @mfacchin - Setup matplotlib to use Qt5's visualization
# NOTE: this needs to remain in the __init__ of the library's root to prevent windows from hanging
import matplotlib as mpl
mpl.use("Qt5Agg")
import matplotlib.pyplot as plt
plt.ion()

# Setup logging
from . import config
from .toolbox_python._logging import setup_logger
logger = setup_logger('metal', config.log.format, config.log.datefmt,
                      capture_warnings=True) # type: logging.Logger
del setup_logger

# Metal Dict
from .toolbox_python.attr_dict import Dict

# Due to order of imports
from ._is_design import is_design, is_component

# TODO: Remove the as global variables, just use in design when
# instanciating the default params and overwriting them.
from .config import DEFAULT, DEFAULT_OPTIONS

# Core modules for user to use
from . import components
from . import designs
from . import draw
from . import renderers
from . import elements
from . import analyses
from . import toolbox_python
from . import toolbox_metal

# Metal GUI
from ._gui import MetalGUI

# Utility modules
# For plotting in matplotlib;  May be superseeded by a renderer?
from .renderers.renderer_mpl import toolbox_mpl as plt

# Utility functions
from .toolbox_python.utility_functions import copy_update
from .toolbox_python.utility_functions import display_options

# Import default renderers
from .renderers import setup_renderers
