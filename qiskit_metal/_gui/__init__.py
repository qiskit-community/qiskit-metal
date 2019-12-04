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
GUI module, handles user interface.

The gui module is only loaded if PyQt5 can be found

Created on Tue May 14 17:13:40 2019
@author: Zlatko
"""
__author__ = 'Zlatko K. Minev'
__version__ = '0.2.2'

# Check if PyQt5 is available for import
try:
    import PyQt5
    __ihave_pyqt__ = True
except (ImportError, ModuleNotFoundError):
    __ihave_pyqt__ = False

if __ihave_pyqt__:
    # Add hook for when we start the gui - Logging for QT errors
    from ._handle_qt_messages import QtCore, _pyqt_message_handler
    QtCore.qInstallMessageHandler(_pyqt_message_handler)
    del QtCore, _pyqt_message_handler

    # main window
    from .main_window import MetalGUI

else:
    def MetalGUI(*args, **kwargs): # pylint: disable=unused-argument
        """
        ERROR: unable to load PyQt5! Please make sure PyQt5 is installed.
        See Metal installation instrucitons and help.
        """

        _error_msg = r'''ERROR: CANNOT START GUI because COULD NOT LOAD PyQT5;
        Try `import PyQt5` This seems to have failed.
        Have you installed PyQt5?
        See install readme
        '''

        print(_error_msg)

        raise Exception(_error_msg)
