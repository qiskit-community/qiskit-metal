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

# pylint: disable=wrong-import-order
# pylint: disable=wrong-import-position
"""Qiskit Metal"""
__version__ = '0.1.2'
__license__ = "Apache 2.0"
__copyright__ = 'Copyright IBM 2019-2020'
__author__ = 'Zlatko Minev, Thomas McConkey, and them IBM Quantum Team'
__status__ = "Development"

###########################################################################
### Windows OS catch for library geopandas not installed with setup.py

import os
if os.name == 'nt':
    try:
        import geopandas
    except ImportError:
        print(" \
            QISKIT METAL INFORMATION: >>>>>>>>>> One last installation step. <<<<<<<<<<<\n \
            >>>>>> Packages fiona and gdal have a known install issue on Windows. <<<<<<\n \
            >>>>>>>>>> geopandas depends on fiona, and fiona depends on gdal. <<<<<<<<<<\n \
            >> To prevent the unavoidable pip installation fail, we excluded geopandas <\n \
            >>>>>> from the list of qiskit-metal package dependencies in Windows. <<<<<<\n \
            >>>>>>>> Before you can use Qiskit Metal, please install geopandas. <<<<<<<<\n \
            >>>> For more information, you can follow the instructions on this FAQ <<<<<\n \
            >>>>>>>>>>>>> https://qiskit.org/documentation/metal/faq.html <<<<<<<<<<<<<<\n"
             )
        raise


###########################################################################
### Basic Setups
## Setup Qt
def __setup_Qt_backend():  # pylint: disable=invalid-name
    """Setup matplotlib to use Qt5's visualization.

    This function needs to remain in the __init__ of the library's root
    to prevent Qt windows from hanging.
    """
    # pylint: disable=import-outside-toplevel

    # When in vscode and in debug-mode, may want to comment
    # next line out, "os.environ["QT_API"] = "pyside2""
    os.environ["QT_API"] = "pyside2"

    from PySide2 import QtCore  #, QtWidgets
    from PySide2.QtCore import Qt

    def set_attribute(name: str, value=True):
        """Describes attributes that change the behavior of application-wide
        features."""
        if hasattr(Qt, name):
            # Does Qt have this attribute
            attr = getattr(Qt, name)
            if not QtCore.QCoreApplication.testAttribute(attr) == value:
                # Only set if not already set
                QtCore.QCoreApplication.setAttribute(attr, value)

    if 1:

        if QtCore.QCoreApplication.instance() is None:
            # No application launched yet

            # zkm: The following seems to fix warning.
            # For example if user ran %gui qt already.
            #  Qt WebEngine seems to be initialized from a plugin.
            # Please set Qt::AA_ShareOpenGLContexts using QCoreApplication::setAttribute
            #  before constructing QGuiApplication.
            # https://stackoverflow.com/questions/56159475/qt-webengine-seems-to-be-initialized
            # Enables resource sharing between the OpenGL contexts used by classes
            #  like QOpenGLWidget and QQuickWidget.
            # Has to do with render mode 'gles'. There is also desktop and software.
            # QCoreApplication.setAttribute(QtCore.Qt.AA_UseOpenGLES)
            # QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
            # QCoreApplication.setAttribute(QtCore.Qt.AA_DisableShaderDiskCache)
            set_attribute('AA_ShareOpenGLContexts')

            # Enables high-DPI scaling in Qt on supported platforms (see also High DPI Displays).
            # Supported platforms are X11, Windows and Android.
            # Enabling makes Qt scale the main (device independent) coordinate
            # system according to display scale factors provided by the
            # operating system.
            set_attribute('AA_EnableHighDpiScaling')

            # Make QIcon::pixmap() generate high-dpi pixmaps that can be larger than
            #  the requested size.
            set_attribute('AA_UseHighDpiPixmaps')

            # Other options of interest:
            # AA_DontUseNativeMenuBar
            # AA_MacDontSwapCtrlAndMeta

    if not os.getenv('QISKIT_METAL_HEADLESS', None):
        # pylint: disable=import-outside-toplevel
        import matplotlib as mpl
        mpl.use("Qt5Agg")
        # pylint: disable=redefined-outer-name
        import matplotlib.pyplot as plt
        plt.ion()  # interactive


__setup_Qt_backend()
del __setup_Qt_backend

## Setup logging
from . import config
from .toolbox_python._logging import setup_logger

logger = setup_logger('metal',
                      config.log.format,
                      config.log.datefmt,
                      capture_warnings=True)  # type: logging.Logger
del setup_logger

###########################################################################
### User-accessible scope

# Metal Dict
from .toolbox_python.attr_dict import Dict

# Due to order of imports
from ._is_design import is_design, is_component

# Core modules for user to use
from .toolbox_metal.parsing import is_true
from . import qlibrary
from . import designs
from . import draw
from . import renderers
from . import qgeometries
from . import analyses
from . import toolbox_python
from . import toolbox_metal

# Metal GUI
from ._gui.main_window import MetalGUI

# Utility modules
# For plotting in matplotlib;  May be superseded by a renderer?
from .renderers.renderer_mpl import mpl_toolbox as plt

# Utility functions
from .toolbox_python.display import Headings

# Import default renderers
from .renderers import setup_renderers

# Common-use
from .qlibrary import QComponent
from .toolbox_metal.about import about, open_docs
