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

import logging
import os
import sys
from pathlib import Path

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox
from PyQt5 import QtWidgets, QtCore, QtGui  # pyqt stuff

from .. import Dict, config
from ..toolbox_python._logging import setup_logger
from ._handle_qt_messages import catch_exception_slot_pyqt
from .main_window_ui import Ui_MainWindow
from .widgets.log_metal import LoggingHandlerForLogWidget


class QMainWindowExtensionBase(QMainWindow):
    """This contains all the functions tthat the gui needs
    to call directly from the UI

    Based on QMainWindow
    """

    def __init__(self):
        super().__init__()
        # Set manually
        self.handler = None  # type: QMainWindowBaseHandler

    @property
    def logger(self) -> logging.Logger:
        """Get the logger"""
        return self.handler.logger

    @property
    def settings(self) -> QtCore.QSettings:
        return self.handler.settings

    def _remove_log_handlers(self):
        if hasattr(self, 'log_text'):
            self.log_text.remove_handlers(self.logger)

    def destroy(self, destroyWindow: bool = True, destroySubWindows: bool = True):
        """
        When the window is cleaned up from memory.
        """
        self._remove_log_handlers()
        super().destroy(destroyWindow=destroyWindow, destroySubWindows=destroySubWindows)

    def closeEvent(self, event):
        """whenever a window is closed.
            Passed an event which we can choose to accept or reject.
        """
        self.save_window_settings()
        super().closeEvent(event)

    def save_window_settings(self):
        # get the current size and position of the window as a byte array.
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())
        self.settings.setValue('stylesheet', self.handler._stylesheet)

    def restore_window_settings(self):
        """
        Call a Qt built-in function to restore values
        from the settings file.
        """
        if 1:
            # should probably call .encode("ascii") here
            geom = self.settings.value('geometry', '')
            if isinstance(geom, str):
                geom = geom.encode("ascii")
            self.restoreGeometry(geom)

            window_state = self.settings.value('windowState', '')
            if isinstance(window_state, str):
                window_state = window_state.encode("ascii")
            self.restoreState(window_state)

            # TODO: add stylesheet
            self.handler.load_stylesheet(self.settings.value('stylesheet',
                                                             self.handler._stylesheet_default))

        # except Exception as e:
            # print(f'ERROR [restore_window_settings]: {e}')

    def bring_to_top(self):
        """ Bring window to top.
         Note that on Windows, this doesn't always work quite well
         """
        self.raise_()
        self.activateWindow()

    def get_screenshot(self, name='shot.png', type_='png', display=True, disp_ops=None):
        """
        Grad a screenshot of the main window,
        save to file, and then copy to clipboard.
        """

        # self.bring_to_top()

        path = Path(name).resolve()

        # This will grab the entire screen
        #screen = QtWidgets.QApplication.primaryScreen()
        #screennum = QtWidgets.QDesktopWidget().screenNumber(self)
        # self.logger.info(f'screennum={screennum}')
        #screen = QtWidgets.QApplication.screens()[screennum]
        # screenshot = screen.grabWindow(self.winId())  # QPixelMap
        # see also https://github.com/ColinDuquesnoy/QDarkStyleSheet/blob/6aef1de7e97227899c478a5634d136d80991123e/example/example.py#L292

        # just grab the main window
        screenshot = self.grab()  # type: QtGui.QPixelMap
        screenshot.save(str(path), type_)  # Save

        QtWidgets.QApplication.clipboard().setPixmap(screenshot)  # To clipboard
        self.logger.info(
            f'Screenshot copied to clipboard and saved to:\n {path}')

        if display:
            from IPython.display import Image, display
            _disp_ops = dict(width=500)
            _disp_ops.update(disp_ops or {})
            display(Image(filename=path, **_disp_ops))

    ##################################################################
    # For actions

    @catch_exception_slot_pyqt()
    def _screenshot(self, _):
        self.get_screenshot()

    @catch_exception_slot_pyqt()
    def load_stylesheet_default(self, _):
        """Used to call from action"""
        self.handler.load_stylesheet('default')

    @catch_exception_slot_pyqt()
    def load_stylesheet_metal_dark(self, _):
        """Used to call from action"""
        self.handler.load_stylesheet('metal_dark')

    @catch_exception_slot_pyqt()
    def load_stylesheet_dark(self, _):
        """Used to call from action"""
        self.handler.load_stylesheet('qdarkstyle')

    @catch_exception_slot_pyqt()
    def load_stylesheet_open(self, _):
        """Used to call from action"""
        default_path = str(self.gui.path_stylesheets)
        filename = QFileDialog.getOpenFileName(self,
                                               'Select Qt stylesheet file `.qss`',
                                               default_path)[0]
        if filename:
            self.logger.info(f'Attempting to load stylesheet file {filename}')

            self.handler.load_stylesheet(filename)


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
    _QMainWindowClass = QMainWindowExtensionBase
    __gui_num__ = -1  # used to count the number of gui instances
    _stylesheet_default = 'default'

    @staticmethod
    def __UI__() -> QMainWindow:  # pylint: disable=invalid-name
        """Abstract, replace with UI class"""
        return None

    def __init__(self, logger: logging.Logger = None,
                 handler=False):
        """
        Can pass in logger

        Attributes:
            _settings :        Used to save the state of the window
                This information is often stored in the system
                registry on Windows, and in property list files on macOS and iOS.
        """
        self.__class__.__gui_num__ += 1  # used to give a unique identifier

        self.config = config.GUI_CONFIG
        self.settings = QtCore.QSettings(self._myappid, 'MainWindow')

        # Logger
        if not logger:
            logger = setup_logger(
                # so that they are not all the same
                f'gui{self.__class__.__gui_num__ }',
                self.config.format,
                self.config.datefmt,
                force_set=True,
                create_stream=self.config.stream_to_std,
            )
            logger.setLevel(getattr(logging,
                                    self.config.log.get('level', 'DEBUG')))

        self.logger = logger
        self._log_handler = None
        self._stylesheet = self._stylesheet_default  # set by load_stylesheet

        # File paths
        self.path_gui = self._get_file_path()  # Path to gui folder
        self.path_imgs = Path(self.path_gui) / \
            self._img_folder_name  # Path to gui imgs folder
        if not self.path_imgs.is_dir():
            print(f'Bad File path for images! {self.path_imgs}')

        # Main Window and App level
        self.main_window = self._QMainWindowClass()
        self.main_window.handler = self
        self.qApp = self._setup_qApp()
        self._setup_main_window_tray()

        # Style and window
        self._style_sheet_path = None
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

        self.main_window.restore_window_settings()

    @property
    def path_stylesheets(self):
        return Path(self.path_gui)/'styles'

    def style_window(self):
        # fusion macintosh # windows
        self.main_window.setStyle(QtWidgets.QStyleFactory.create("fusion"))
        # TODO; add stlyesheet to load here - maybe pull form settings

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


        There are three classes:
            QCoreApplication - base class. Used in command line applications.
            QGuiApplication - base class + GUI capabilities. Used in QML applications.
            QApplication - base class + GUI + support for widgets. Use it in QtWidgets applications.

        See:
            https://forum.qt.io/topic/94834/differences-between-qapplication-qguiappication-qcoreapplication-classes/3
            https://github.com/matplotlib/matplotlib/blob/9984f9c4db7bfb02ffca53b7823acb8f8e223f6a/lib/matplotlib/backends/backend_qt5.py#L98
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

        # QApplication.platformName() -- on mac: 'cocoa'

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

            if 1:
                log_name = 'gui'  # self._myappid
                self.ui.log_text.add_logger(log_name)
                self._log_handler = LoggingHandlerForLogWidget(
                    log_name, self, self.ui.log_text)
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
        if self.config.main_window.auto_size:
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
        Load and set stylesheet for the main gui.


        Keyword Arguments:
            path (str) : Path to stylesheet or its name.
                Can be: 'default', 'qdarkstyle' or None.
                `qdarkstyle` requires
                >>> pip install qdarkstyle
        """
        result = True
        self._fuck = path
        print(f"""{path} is 'metal_dark' = {path == 'metal_dark'}""")
        if path == 'default' or path is None:
            self._style_sheet_path = 'default'
            self.main_window.setStyleSheet('default')

        elif path == 'qdarkstyle':
            try:
                import qdarkstyle
            except ImportError:
                QMessageBox.warning(self.main_window, 'Failed.',
                                    'Error, you did not seem to have installed qdarkstyle.\n'
                                    'Please do so from the terminal using\n'
                                    ' >>> pip install qdarkstyle')

            os.environ['QT_API'] = 'pyqt5'
            self.main_window.setStyleSheet(qdarkstyle.load_stylesheet())

        elif path == 'metal_dark':
            path_full = self.path_stylesheets/'metal_dark'/'style.qss'
            print(f'path_full = {path_full}')
            self._load_stylesheet_from_file(path_full)

        else:
            self._load_stylesheet_from_file(path)

        if result: # Set successfuly
            self._stylesheet = path
            self.settings.setValue('stylesheet', self._stylesheet)
        else: # Failed to set
            return False

    def _load_stylesheet_from_file(self, path: str):
        print(f'path = {path}')
        try:
            path = Path(str(path))
            if path.is_file():
                self._style_sheet_path = str(path)
                stylesheet = path.read_text()
                stylesheet = stylesheet.replace(
                    ':/metal-styles', str(self.path_stylesheets))

                self.main_window.setStyleSheet(stylesheet)
                return True

            else:
                self.logger.error(
                    'Could not find the stylesheet file where expected %s', path)
                return False
        except Exception as e:
            self.logger.error(f'_load_stylesheet_from_file error: {e}')

    def screenshot(self, name='shot.png', type_='png', display=True, disp_ops=None):
        """
        Grad a screenshot of the main window,
        save to file, and then copy to clipboard.
        """
        self.main_window.get_screenshot(name, type_, display, disp_ops)


def kick_start_qApp():

    qApp = QtCore.QCoreApplication.instance()

    if qApp is None:
        try:
            QtWidgets.QApplication.setAttribute(
                QtCore.Qt.AA_EnableHighDpiScaling)
        except AttributeError:  # Attribute only exists for Qt >= 5.6
            pass

        qApp = QApplication(sys.argv)

        if qApp is None:
            logging.error("QApplication.instance is None.")

            if config._ipython:
                # iPython has magic for loop
                logging.error(
                    "QApplication.instance: Attempt magic IPython %%gui qt5")
                try:
                    from IPython import get_ipython
                    ipython = get_ipython()
                    ipython.magic('gui qt5')

                except Exception as e:
                    print("exception")
                    logging.error(f"FAILED: {e}")
                    print(e)

            else:
                # We are not running form IPython, manually boot
                logging.error(
                    "QApplication.instance: Attempt to manually create qt5 QApplication")
                qApp = QtWidgets.QApplication(["qiskit-metal"])
                qApp.lastWindowClosed.connect(qApp.quit)

    return qApp
