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

### # pylint: disable=invalid-name

import logging
import os
import sys
from copy import deepcopy
from pathlib import Path

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox, QDockWidget

from .. import Dict, config
from ..toolbox_python._logging import setup_logger
from . import __version__
from .main_window_ui import Ui_MainWindow
from .utility._handle_qt_messages import catch_exception_slot_pyqt
from .widgets.log_widget.log_metal import LogHandler_for_QTextLog


class QMainWindowExtensionBase(QMainWindow):
    """This contains all the functions tthat the gui needs
    to call directly from the UI

    Extends the `QMainWindow` class
    """

    def __init__(self):
        """  """
        super().__init__()
        # Set manually
        self.handler = None  # type: QMainWindowBaseHandler

    @property
    def logger(self) -> logging.Logger:
        """Get the logger"""
        return self.handler.logger

    @property
    def settings(self) -> QtCore.QSettings:
        """Get the settings"""
        return self.handler.settings

    @property
    def gui(self) -> 'QMainWindowBaseHandler':
        """Get the GUI"""
        self.handler

    def _remove_log_handlers(self):
        """Remove the log handlers"""
        if hasattr(self, 'log_text'):
            self.log_text.remove_handlers(self.logger)

    def destroy(self, destroyWindow: bool = True, destroySubWindows: bool = True):
        """
        When the window is cleaned up from memory.

        Args:
            destroyWindow (bool): Whether or not to destroy the window (Default: True)
            destroySubWindows (bool): Whether or not to destroy sub windows (Default: True)
        """
        self._remove_log_handlers()
        super().destroy(destroyWindow=destroyWindow, destroySubWindows=destroySubWindows)

    def closeEvent(self, event):
        """whenever a window is closed.
        Passed an event which we can choose to accept or reject.
        """
        if self.ok_to_continue():
            self.save_window_settings()
            super().closeEvent(event)

    def ok_to_continue(self):
        """
        Determine if it ok to continue

        Returns:
            bool: True to continue, False otherwise
        """
        if 1:
            reply = QMessageBox.question(self,
                                         "Qiskit Metal",
                                         "Save unsaved changes to design?",
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return False
            elif reply == QMessageBox.Yes:
                return self.handler.save_file()  # TODO: in parent
        return True

    def save_window_settings(self):
        """Save the window settings"""
        self.logger.info('Saving window state')
        # get the current size and position of the window as a byte array.
        self.settings.setValue('metal_version', __version__)
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())
        self.settings.setValue('stylesheet', self.handler._stylesheet)

    def restore_window_settings(self):
        """
        Call a Qt built-in function to restore values
        from the settings file.

        Raises:
            Exception: Error in restoration
        """

        version_settings = self.settings.value('metal_version', defaultValue='0')
        if __version__ > version_settings:
            self.logger.debug(
                f"Clearing window settings [{version_settings}]...")
            self.settings.clear()

        try:
            self.logger.debug("Restoring window settings...")

            # should probably call .encode("ascii") here
            geom = self.settings.value('geometry', '')
            if isinstance(geom, str):
                geom = geom.encode("ascii")
            self.restoreGeometry(geom)

            window_state = self.settings.value('windowState', '')
            if isinstance(window_state, str):
                window_state = window_state.encode("ascii")
            self.restoreState(window_state)

            self.handler.load_stylesheet(self.settings.value('stylesheet',
                                                             self.handler._stylesheet_default))

            # TODO: Recent files
        except Exception as e:
            self.logger.error(f'ERROR [restore_window_settings]: {e}')

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

    def toggle_all_docks(self):
        """Show or hide all docks.
        """
        docks = [widget for widget in self.children() if isinstance(widget, QDockWidget)]
        docks = list(filter(lambda x:  not x.windowTitle().lower().startswith('edit source'), docks))
        # print(docks)
        docks += [widget for widget in self.gui.plot_win.children() if isinstance(widget, QDockWidget)] # specific
        dock_states = {dock: dock.isVisible() for dock in docks}

        do_hide = any(dock_states.values()) # if any are visible then hide all
        for dock in docks:
            if do_hide:
                dock.hide()
            else:
                dock.show()
        # TODO: small -- fix, changes which dock is on top or now

    ##################################################################
    # For actions

    @catch_exception_slot_pyqt()
    def _screenshot(self, _):
        """Used to call from action"""
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

        self.config = deepcopy(config.GUI_CONFIG)
        self.settings = QtCore.QSettings(self._myappid, 'MainWindow')

        # Logger
        if not logger:
            # print('Setting up logger')
            logger = setup_logger(
                # so that they are not all the same
                f'gui{self.__class__.__gui_num__ }',
                config.log.format,
                config.log.datefmt,
                force_set=True,
                create_stream=self.config.stream_to_std,
            )
            log_level = int(
                getattr(logging, self.config.logger.get('level', 'DEBUG')))
            logger.setLevel(log_level)

        self.logger = logger
        self._log_handler = None  # defined in self._setup_logger
        self._stylesheet = self._stylesheet_default  # set by load_stylesheet

        # File paths
        self.path_gui = self._get_file_path()  # Path to gui folder
        self.path_imgs = Path(self.path_gui) / \
            self._img_folder_name  # Path to gui imgs folder
        if not self.path_imgs.is_dir():
            text = f'Bad File path for images! {self.path_imgs}'
            print(text)
            self.logger.error(text)

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

        self.ui.log_text.dock_window = self.ui.dockLog
        self._setup_logger()
        self._setup_window_size()

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

        # for window platofrms only
        # QApplication.platformName() -- on mac: 'cocoa'
        if os.name.startswith('nt'):
            # Arbitrary string, needed for icon in taskbar to be custom set proper
            # https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                self._myappid)

        app = self.qApp
        if app:
            app.setOrganizationName(r"IBM Quantum Metal")
            app.setOrganizationDomain(r"https://www.ibm.com/quantum-computing")
            app.setApplicationName(r"Qiskit Metal")

        return self.qApp

    def _setup_main_window_tray(self):

        if self.path_imgs.is_dir():
            icon = QIcon(str(self.path_imgs/self._img_logo_name))
            self.main_window.setWindowIcon(icon)

            # not sure if this works, but let's try
            self._icon_tray = QtWidgets.QSystemTrayIcon(icon, self.main_window)
            self._icon_tray.show()
            self.qApp.setWindowIcon(icon)

    def create_log_handler(self, name_toshow: str, logger: logging.Logger):
        return LogHandler_for_QTextLog(name_toshow, self, self.ui.log_text, logger)

    @catch_exception_slot_pyqt()
    def _setup_logger(self):
        """
        Setup logging UI.

        Show wellcome message
        """
        if hasattr(self.ui, 'log_text'):

            self.ui.log_text.img_path = self.path_imgs

            self._log_handler = self.create_log_handler('GUI', self.logger)

            QTimer.singleShot(1500, self.ui.log_text.welcome_message)

        else:
            self.logger.warning('UI does not have `log_text`')

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
            # print(f'path_full = {path_full}')
            self._load_stylesheet_from_file(path_full)

        else:
            self._load_stylesheet_from_file(path)

        if result:  # Set successfuly
            self._stylesheet = path
            self.settings.setValue('stylesheet', self._stylesheet)
        else:  # Failed to set
            return False

    def _load_stylesheet_from_file(self, path: str):
        # print(f'path = {path}')
        try:
            path = Path(str(path))
            if path.is_file():
                self._style_sheet_path = str(path)
                stylesheet = path.read_text()
                stylesheet = stylesheet.replace(
                    ':/metal-styles', str(self.path_stylesheets))

                # if windows, double the slashes in the paths
                if os.name.startswith('nt'):
                    stylesheet = stylesheet.replace("\\", "\\\\")

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

    def save_file(self):
        """Save file. Called on exit"""
        raise NotImplementedError()


def kick_start_qApp():

    qApp = QtCore.QCoreApplication.instance()

    if qApp is None:
        try:
            # TODO: See
            QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
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
