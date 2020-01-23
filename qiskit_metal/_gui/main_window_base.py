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
GUI front-end interface for Qiskit Metal in PyQt5.
@author: Zlatko Minev, IBM
"""

# pylint: disable=invalid-name

import os
#import sys
import logging
#import traceback
#import importlib

from pathlib import Path

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow  # , QAction,
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot

from .. import config
from ..toolbox_python._logging import setup_logger
from ._handle_qt_messages import catch_exception_slot_pyqt

from .main_window_ui import Ui_MainWindow
from .widgets.log_metal import LoggingHandlerForLogWidget
from .component_widget_ui import Ui_ComponentWidget


class QMainWindowBaseHandler():
    """Abstract Class to wrap and handle main window .

    Assumes a UI that has
        log_text : a QText for logging

    Assumes we have functions:
        setup_logger

    Assumes we have objects
         config.log.format, config.log.datefmt,config._ipython
    """
    _myappid = 'QiskitMetal'
    _img_logo_name = 'my_logo.png'
    _img_folder_name = '_imgs'
    _dock_names = []
    _QMainWindowClass = QMainWindow

    @staticmethod
    def __UI__() -> QMainWindow:  # pylint: disable=invalid-name
        """Abstract, replace with UI class"""
        return None

    def __init__(self, logger: logging.Logger = None):
        """
        Can pass in logger
        """

        # Logger
        if not logger:
            logger = setup_logger('gui', config.log.format,
                                  config.log.datefmt,
                                  force_set=True,
                                  capture_warnings=False)
            logger.setLevel(logging.DEBUG)
        self.logger = logger
        self._log_handler = None

        # File paths
        self.path_gui = self._get_file_path()  # Path to gui folder
        self.path_imgs = Path(self.path_gui)/self._img_folder_name  # Path to gui imgs folder
        if not self.path_imgs.is_dir():
            print(f'Bad File path for images! {self.path_imgs}')

        # Main Window and App level
        self.main_window = self._QMainWindowClass()
        self.qApp = self._setup_qApp()
        self._setup_main_window_tray()
        self.style_window()

        # UI
        self.ui = self.__UI__()
        self.ui.setupUi(self.main_window)
        self.main_window.ui = self.ui

        self._setup_logger()
        self._setup_window_size()

        self._dock_raises = None
        self._setup_dock_show()

        self._ui_adjustments()  # overwrite

    def style_window(self):
        # fusion macintosh # windows
        self.main_window.setStyle(QtWidgets.QStyleFactory.create("fusion"))
        #self.load_stylesheet(r'C:\zkm-code\qiskit_metal\qiskit_metal\_gui\styles\darkorange_v1.qss')

    def _ui_adjustments(self):
        """Any touchups to the loaded ui that need be done soon
        """
        pass

    def _get_file_path(self):
        """Get the dir name of the current path in which this file is stored"""
        return os.path.dirname(__file__)

    def _setup_qApp(self):
        """
        Only one qApp can exist at a time, so check before creating one.
        See also https://github.com/matplotlib/matplotlib/blob/9984f9c4db7bfb02ffca53b7823acb8f8e223f6a/lib/matplotlib/backends/backend_qt5.py#L98
        """

        self.qApp = QApplication.instance()

        if self.qApp is None:
            self.logger.warning("QApplication.instance is None.")

            # Kickstart()

            # Did it work now
            self.qApp = QApplication.instance()

            if self.qApp is None:

                self.logger.error(r"""ERROR: QApplication.instance is None.
                Did you run a cell with the magic in IPython?
                ```python
                    %gui qt
                ```
                This command allows IPython to integrate itself with the Qt event loop,
                so you can use both a GUI and an interactive prompt together.
                Reference: https://ipython.readthedocs.io/en/stable/config/eventloops.html
                """)

        # for window platofrms only
        if os.name.startswith('nt'):
            # Arbitrary string, needed for icon in taskbar to be custom set proper
            # https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                self._myappid)

        return self.qApp

    def _setup_main_window_tray(self):

        if self.path_imgs.is_dir():
            icon = QIcon(str(self.path_imgs/self._img_logo_name))
            self.main_window.setWindowIcon(icon)

            # not sure if this works, but let's try
            self._icon_tray = QtWidgets.QSystemTrayIcon(icon, self.main_window)
            self._icon_tray.show()
            self.qApp.setWindowIcon(icon)

    @catch_exception_slot_pyqt()
    def _setup_logger(self):
        """
        Setup logging UI
        """

        if hasattr(self.ui, 'log_text'):

            self.ui.log_text.img_path = self.path_imgs
            #self.ui.log_text.img_path = Path(self.path_imgs)

            self.ui.log_text.add_logger(self._myappid)
            self._log_handler = LoggingHandlerForLogWidget(
                self._myappid, self, self.ui.log_text)
            self.logger.addHandler(self._log_handler)

            self.ui.log_text.wellcome_message()

        else:
            self.logger.warning('UI does not have `log_text`')

    def _setup_dock_show(self):
        self._dock_raises = {}
        for dock in self._dock_names:

            # Function
            @pyqtSlot(bool, name=f'raise_{dock}')
            def raise_(state: bool, dock_name=dock):
                #print(dock_name, state)
                _dock = getattr(self.ui, dock_name)
                if state:
                    self.logger.debug(f'Raising dock {dock_name}')
                    _dock.setVisible(True)
                    _dock.show()
                    _dock.raise_()
                else:
                    self.logger.debug(f'Hiding dock {dock_name}')
                    _dock.setVisible(False)

            self._dock_raises[dock] = raise_

            # Connect to action
            action = dock.replace('dock', 'action')
            if hasattr(self.ui, action):
                #self.logger.debug(f'DOCK {dock} has an action {action}')
                _action = getattr(self.ui, action)
                # _action.triggered.disconnect() # TypeError if none
                _action.triggered.connect(self._dock_raises[dock])
            else:
                self.logger.warning(
                    f'DOCK {dock} should have had an action {action}, but it did not!')

    def _setup_window_size(self):
        screen = self.qApp.primaryScreen()
        # screen.name()

        rect = screen.availableGeometry()
        rect.setWidth(rect.width()*0.9)
        rect.setHeight(rect.height()*0.9)
        rect.setLeft(rect.left()+rect.width()*0.1)
        rect.setTop(rect.top()+rect.height()*0.1)
        self.main_window.setGeometry(rect)

    def load_stylesheet(self, path=None):
        """
        Load and set stylesheet for the main gui

        Keyword Arguments:
            path {[str]} -- [Path tos tylesheet. Can also de default] (default: {None})
        """

        if path == 'default':
            self.main_window.setStyleSheet(path)
            return True

        #if path is None:
        #    path = self.path_imgs.parent/'styles'/self._style_sheet_name

        path = Path(path)
        self._style_sheet_path = str(path)

        if path.is_file():
            stylesheet = path.read_text()
            # replace all :/ with the corrent path or handle correctly
            #TODO: Change to Url replace
            stylesheet = stylesheet.replace(':/', str(self.path_imgs))

            self.main_window.setStyleSheet(stylesheet)
        else:
            self.logger.error('Could not find the stylesheet file where expected %s', path)
            return False

        return True


def kick_start_qApp():

    qApp = QApplication.instance()

    if qApp is None:
        logging.error("QApplication.instance is None.")

        if config._ipython:
            # Pithyon has magic for loop
            logging.error("QApplication.instance: Attempt magic IPython %%gui qt5")
            try:
                from IPython import get_ipython
                ipython = get_ipython()
                ipython.magic('gui qt5')

            except Exception as e:
                logging.error(f"FAILED: {e}")
                print(e)

        else:
            # We are not running form IPython, manually boot
            logging.error("QApplication.instance: Attempt to manually create qt5 QApplication")
            qApp = QtWidgets.QApplication(["qiskit-metal"])
            qApp.lastWindowClosed.connect(qApp.quit)

    return qApp
