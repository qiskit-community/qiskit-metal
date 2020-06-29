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
=================================================
GUI (:mod:`qiskit_metal._gui`)
=================================================

.. currentmodule:: qiskit_metal._gui

GUI module, handles user interface.

The gui module is only loaded if PyQt5 can be found.

Created on Tue May 14 17:13:40 2019
@author: Zlatko


UNDER CONSTRUCTION

UNDER-CONSTRUCTION
---------------

.. autosummary::
    :toctree: ../stubs/

    UNDER-CONSTRUCTION

"""

import logging
from .. import __version__

# Check if PyQt5 is available for import
try:
    import PyQt5
    __ihave_pyqt__ = True
except (ImportError, ModuleNotFoundError):
    __ihave_pyqt__ = False

if __ihave_pyqt__:

    # Add hook for when we start the gui - Logging for QT errors
    from .utility._handle_qt_messages import QtCore, _pyqt_message_handler
    QtCore.qInstallMessageHandler(_pyqt_message_handler)
    del QtCore, _pyqt_message_handler

    # main window
    from .main_window import MetalGUI as _MetalGUI
    from .main_window_base import kick_start_qApp

    def MetalGUI(*args, **kwargs):

        qApp = kick_start_qApp()

        if not qApp:
            # Why is it none
            logging.error("""Could not start PyQt5 event loop using QApplicaiton. """)

        return _MetalGUI(*args, **kwargs)
else:

    # Function as an error function for the class MetalGUI
    def MetalGUI(*args, **kwargs): # pylint: disable=unused-argument,bad-option-value,invalid-name
        """
        ERROR: Unable to load PyQt5! Please make sure PyQt5 is installed.
        See Metal installation instrucitons and help.
        """

        _error_msg = r'''ERROR: CANNOT START GUI because COULD NOT LOAD PyQT5;
        Try `import PyQt5` This seems to have failed.
        Have you installed PyQt5?
        See install readme
        '''

        print(_error_msg)

        raise Exception(_error_msg)
