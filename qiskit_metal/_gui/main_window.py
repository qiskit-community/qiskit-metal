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
Main GUI frontend interface for Metal.
@author: Zlatko
"""

import sys
import logging
import traceback
import importlib

from pathlib import Path

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QDir, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QDockWidget
from PyQt5.QtWidgets import QTextEdit, QLineEdit, QMessageBox
from PyQt5.QtWidgets import QAction, QInputDialog, QFileDialog
from PyQt5.QtWidgets import QLabel, QMenu, QToolButton, QStyle

from ..config import GUI_CONFIG
from .. import logger, save_metal, load_metal
from ..draw_utility import plot_simple_gui_spawn, plot_simple_gui_style
from ..draw_utility import draw_all_objects

from . import widgets
from .widgets.toolbar_icons import add_toolbar_icon
from .widgets.dialog_create_metal import Dialog_create_metal
from .widgets.trees.metal_objects import Tree_Metal_Objects
from .widgets.trees.default_options import Tree_Default_Options
from .widgets.log_metal import Logging_Window_Widget, Logging_Hander_for_Log_Widget
from ._handle_qt_messages import catch_exception_slot_pyqt


class Metal_gui(QMainWindow):
    myappid = u'qiskit.metal.main_gui'
    _window_title = "Qiskit Metal - Quantum VLSI and Sims"
    _icon_default_create = 'create.png' # Maybe move to stylesheet
    _icon_size_create = 40  # 31px typical; QStyle.PM_ToolBarIconSize/2 # QtWidgets - typical setting

    def __init__(self, design, objects=None, DEFAULT_OPTIONS=None):
        '''
        When running in IPython and Jupyter, make sure you have the QT loop launched.

        .. code-block python
            %matplotlib qt
            %gui qt
            from qiskit_metal import Metal_gui, PlanarDesign

            layout = PlanarDesign()
            gui = Qiskit_Metal_GUI(layout)
        '''

        self._setup_qApp()

        super().__init__()

        # params
        self.design = design
        self._objects = None
        self._DEFAULT_OPTIONS = None

        # set params
        self.set_objects(objects)
        self.set_DEFAULT_OPTIONS(DEFAULT_OPTIONS)

        # Params we will specify
        self._style_sheet_name = 'metal_default.qss'
        self._style_sheet_path = None
        self.toolbar_create_metal = None

        # create workspace
        self._setup_main_window()
        self._setup_menu_bar()
        self._setup_plot()
        self._setup_tree_view()
        self._setup_tree_design_options()
        self._setup_tree_default_options()
        self._setup_window_style()
        self._setup_main_toolbar()
        self._setup_logging()
        self._setup_file_menu()

        # refresh
        self.show()
        self.refresh_all()
        self.raise_()

        self.fig_tight_layout()

    def _setup_qApp(self):
        self.logger = logger

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

        if sys.platform.startswith('win'):
            # For window only
            # Arbitrary string, needed for icon in taskbar to be custom set proper
            # https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(self.myappid)

    def _setup_main_window(self):
        self.setWindowTitle(self._window_title)

        self.imgs_path = Path(widgets.__file__).parent.parent / '_imgs'
        if not self.imgs_path.is_dir():
            print(f'Metal Main Window: Bad file path for loading images! {self.imgs_path}')
        else:
            icon = QIcon(str(self.imgs_path/'qiskit_logo1.png'))
            self.setWindowIcon(icon)
            # try not sur eif works:
            self.icon_tray = QtWidgets.QSystemTrayIcon(icon, self)
            self.icon_tray.show()
            self.qApp.setWindowIcon(icon)

        self.setDockOptions(QMainWindow.AllowTabbedDocks |
                            QMainWindow.AllowNestedDocks)
        self.setAnimated(True)

        # Dummy
        self.setCentralWidget(QTextEdit())
        self.centralWidget().hide()

        self.resize(1200, 850)
        # Resize events are handled by self.resizeEvent()

    def _setup_logging(self, catch_exceptions=True):
        '''
        Make logging window and handle traceback exceptions
        based on: https://stackoverflow.com/questions/28655198/best-way-to-display-logs-in-pyqt
        '''
        # Log window widget
        self.logger_window = Logging_Window_Widget(self.imgs_path)

        # Handlers
        self.logger_window.add_logger('Metal')
        self._log_handler = Logging_Hander_for_Log_Widget('Metal', self)
        logger.addHandler(self._log_handler)  # logger is the metal logger Metal

        # TODO: Make modular and add pyEPR
        # if 0:
        #     self.logger_window.add_logger('pyEPR')
        #     self._log_handler_pyEPR = logging.getLogger('pyEPR')
        #     self._log_handler_pyEPR.addHandler(self._log_handler_pyEPR)

        # Handle exceptions with tracebakck
        def excepthook(type, value, tb):
            """
            This function prints out a given traceback and exception to sys.stderr.
            When an exception is raised and uncaught, the interpreter calls sys.excepthook
            h three arguments, the exception class, exception instance, and a traceback object.
            In an interactive session this happens just before control is returned to the
            prompt; in a Python program this happens just before the program exits.
            The handling of such top-level exceptions can be customized by assigning another
            three-argument function to sys.excepthook.
            """
            traceback_string = '\n'.join(traceback.format_exception(type, value, tb))
            self.logger_window.log_message_to('Errors', traceback_string)
            traceback.print_exception(type, value, tb)

        self._logger_excepthook = excepthook
        if catch_exceptions:
            sys.excepthook = excepthook

        # Add dock, position and style
        self.logView_dock = self._add_dock('Logs', self.logger_window, 'Right')
        self.tabifyDockWidget(self.tree_def_ops.dock, self.logView_dock)

    def _setup_menu_bar(self):
        self.menu = self.menuBar()
        self.menu_file = self.menu.addMenu("File")
        self.menu_plot = self.menu.addMenu("Plot")
        self.menu_act = self.menu.addMenu("Actions")
        self.menu_windows = self.menu.addMenu("Windows")

        self._setup_plot_menu()
        self._setup_window_menu()

    def _setup_window_menu(self):
        self.menu_windows.astyle = self.menu_windows.addAction("Reload stylesheet")
        self.menu_windows.astyle.triggered.connect(self.reload_stylesheet)

        self.menu_windows.addSection('Show / Hide:')

    def _setup_file_menu(self):
        self.menu_file.addSeparator()
        self.menu_file.quit = self.menu_file.addAction("&Quit")
        self.menu_file.quit.triggered.connect(self.close)

    def _setup_plot_menu(self):
        '''
        Finish off a few things after all core items have been created,
        Especially the tree views. Link them in the toolbar.
        '''
        self.menu_plot.addSeparator()

        self.menu_plot.tight_action = QAction('Figure tight layout')
        self.menu_plot.tight_action.triggered.connect(self.fig_tight_layout)
        self.menu_plot.tight = self.menu_plot.addAction(self.menu_plot.tight_action)

    def _setup_plot(self):
        fig_draw, ax_draw = plot_simple_gui_spawn(dict(num=None))
        self.fig_draw = fig_draw
        self.fig_window = self.fig_draw.canvas.window()
        self.ax_draw = ax_draw

        self.draw_dock = self._add_dock(
            'Drawing window', self.fig_window, 'Left', 400)

        # Custom toolbars
        toolbar = self.fig_draw.canvas.manager.toolbar
        menu = self.menu_plot

        add_toolbar_icon(toolbar, 'action_refresh_plot',
                         self.imgs_path/'refresh-button.png',
                         self.re_draw,
                         'Refreshes the plot area only.',
                         'R', self.menu,
                         label='Refresh plot')

        toolbar.addSeparator()

        add_toolbar_icon(toolbar, 'action_draw_connectors',
                         self.imgs_path/'show_connectors.png',
                         self.draw_connectors,
                         'Shows the name of all connectors in the plot area.',
                         'Shift+C', menu,
                         label='Show connectors')

        menu.addSeparator()
        toolbar.addSeparator()

        self.fig_draw.show()

    def _setup_main_toolbar(self):
        self.toolbar_main = self.addToolBar(
            'Main functions')  # tood have htis add a menu show hide
        toolbar = self.toolbar_main
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        menu = self.menu_act

        menu.addSeparator()

        add_toolbar_icon(toolbar, 'action_refresh_all',
                         self.imgs_path/'refresh-all.png',
                         self.refresh_all,
                         'Refresh all trees and plots in the gui.',
                         'Ctrl+R', menu,
                         label="&Refresh\nall")

        add_toolbar_icon(toolbar, 'action_remake_all_objs',
                         self.imgs_path/'gears.png',
                         self.remake_all,
                         'Remake all objects with their current parameters',
                         'M', menu,
                         label="Re&make\nall")

        add_toolbar_icon(toolbar, 'action_clear_all_objects',
                         self.imgs_path/'clear-button.png',
                         self.clear_all_objects,
                         '&Clear\nall',
                         None, menu,
                         label='Clear\nall')

        menu.addSeparator()
        toolbar.addSeparator()

        add_toolbar_icon(toolbar, 'action_save_metal',
                         self.imgs_path/'save.png',
                         self.action_save_metal,
                         'Save metal design to file',
                         'Ctrl+S', self.menu_file,
                         label='&Save\ndesign')

        add_toolbar_icon(toolbar, 'action_open_metal',
                         self.imgs_path/'open.png',
                         self.action_open_metal,
                         'Open metal design file',
                         'Ctrl+O', self.menu_file,
                         label='&Load\ndesign')

        add_toolbar_icon(toolbar, 'action_gds_export',
                         self.imgs_path/'GDS.png',
                         self.action_gds_export,
                         'Export\nto &gds',
                         None, menu,
                         label='Export\nto &gds')

        self._setup_create_objects()

    def _setup_create_objects(self):

        # Decide if tree library might better here rather than toolbar?
        # For now just quick here

        self.toolbar_create_metal = self.addToolBar('Create Metal')
        toolbar = self.toolbar_create_metal
        toolbar.setObjectName('toolbarCreate')
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        toolbar.setIconSize(QSize(self._icon_size_create, self._icon_size_create))

        # Label
        if 0:
            toolbar.title_Label = QLabel("Create\n Metal")
            toolbar.title_Label.setAlignment(QtCore.Qt.AlignCenter)
            toolbar.title_Label.setObjectName('lblCreateMetal')
            toolbar.addWidget(toolbar.title_Label)

        ####
        # Create buttons

        for name, metal_module in GUI_CONFIG.load_metal_modules.items():
            self.add_metal_module(toolbar, name, metal_module)

    def add_metal_module(self, toolbar, name, metal_module):
        assert isinstance(metal_module, str)

        module = load_metal_object_module(metal_module)
        if module is False: # Failed to load module
            return False

        # While Path(module.__file__).parent should work, lets do more propper
        paths_search = module.__spec__.submodule_search_locations # list
        py_file_paths = []
        for path_search in paths_search:
            py_file_paths += list(Path(path_search).glob('*.py'))

        if len(py_file_paths) == 0:
            self.logger.warning(f'Did not find any objects in metal_module={metal_module}'\
                                f' to load.\n Searched in path_search={path_search}')
            return False

        ### Create button for menu dropdown
        button = QToolButton(toolbar)
        button.setText(name)
        button.setPopupMode(QToolButton.InstantPopup)
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.addWidget(button)

        # Icon
        icon_path = self.imgs_path
        if hasattr(module, '_img'):
            icon_path /= module._img
        else:
            icon_path /= self._icon_default_create
        button.setIcon(QIcon(str(icon_path)))


        # Create Menu items
        menu = QMenu()
        menu.setObjectName('createMetal')
        button.setMenu(menu)
        for file_path in py_file_paths:
            submodule_name = str(Path(file_path).stem)
            if not submodule_name.startswith('_'):
                self.add_metal_object(menu, module, submodule_name)

    def add_metal_object(self, menu, parent_module, submodule_name,
                         tool_name=None):
        '''
        Creates wrapper functions and menu actions
        '''

        assert isinstance(submodule_name, str)

        ###########################################################################
        # LOAD MODULE AND CLASS

        # Load the submodule
        submodule_full_name = str(parent_module.__name__) + '.' + submodule_name
        module = load_metal_object_module(submodule_full_name)

        # Load the class from the submodule.
        # Assume the class name is the same as the filename (module name)
        class_name = submodule_name
        log_msg = f'add_metal_object: Loaded module {submodule_full_name} from {parent_module.__file__}\n'
        try:
            metal_class = getattr(module, class_name)
        except Exception as error:
            self.logger.error(log_msg + f'but could not find/load class {class_name}\n'\
                              'Error ({error}): \n{sys.exc_info()}')
            return False

        self.logger.debug(log_msg + f'\n Loaded class {metal_class}')

        ###########################################################################
        ### Create GUI tools

        # Tool name label
        if not tool_name:
            tool_name = class_name

        label = tool_name.replace('_', ' ')
        if 0: # break the name up
            if label.startswith('Metal '):
                label = label[6:]
            if len(label) > 14:
                label = label[:int(len(label)/2)] + '-\n' + \
                    label[int(len(label)/2):]  # split to new line

        #############################
        # Create call function

        @catch_exception_slot_pyqt()
        def create_metal_obj(*args):
            # Load module  on the fly
            # Assumed that the module file name is the same as the class name

            nonlocal class_name
            nonlocal metal_class

            form = Dialog_create_metal(self, metal_class)
            result, my_args = form.get_params()

            if result:
                if my_args['name']:
                    metal_class(self.design, my_args['name'], options=my_args['options'])
                    self.refresh_all()
                else:
                    QMessageBox.about(self, "No name provided.", "Warning: You did not provide a"\
                                      " name for the object. Object will not be created.")
        # Save
        setattr(self, 'create_'+tool_name, create_metal_obj)


        #############################
        # Finally create menu tool and add
        icon_path = self._get_metal_icon_path(metal_class)

        action = menu.addAction(label)
        action.setIcon(QIcon(str(icon_path)))
        action.triggered.connect(create_metal_obj)
        action.setToolTip(f'Create a Qiskit Metal object: {submodule_full_name}')
        setattr(self, 'createA_'+tool_name, action)

        return True

    def _get_metal_icon_path(self, metal_class):

        if not hasattr(metal_class, '_img'):
            return None

        icon_path = self.imgs_path/getattr(metal_class, '_img')

        if not Path(icon_path).is_file():

            icon_path2 = self.imgs_path/'Metal_Object.png'
            logger.warning(f'Could not locate  image path {icon_path}')

            if Path(icon_path2).is_file():
                icon_path = icon_path2
                logger.warning(f'Replacing with  image path {icon_path}')
            else:
                logger.warning(f'Could not even find base image path {icon_path2}')
                return None

        return icon_path

    def _setup_tree_view(self):

        tree = self.tree = Tree_Metal_Objects(self, objects=self.objects, gui=self)
        tree.main_window = QMainWindow(self)
        tree.dock = self._add_dock('Object Explorer', tree.main_window, 'Right', 400)
        tree.dock.setToolTip('Press ENTER after done editing a value to remake the objects.')

        tree.dock.setToolTipDuration(2000)
        # Specifies how long time the tooltip will be displayed, in milliseconds. If the value
        # is -1 (default) the duration is calculated depending on the length of the tooltip.

        # Main window for tree
        tree.main_window.setCentralWidget(tree)
        #main_window.layout_ = QVBoxLayout(self.tree_window)
        # dock.setMinimumWidth(250) # now set the real min width, the first one set the width

        # Toolbar
        # toolbar = main_window.toolbar = main_window.addToolBar(
        #    'Objects Properties Toolbar')
        #tree.add_toolbar_refresh(toolbar, main_window, self.imgs_path)
        #tree.add_toolbar_slider(toolbar, main_window, self.imgs_path)

    def _setup_tree_default_options(self):

        tree = self.tree_def_ops = Tree_Default_Options(
            self, content_dict=self.DEFAULT_OPTIONS, gui=self)
        tree.main_window = QMainWindow(self)
        tree.dock = self._add_dock('Default Properties', tree.main_window, 'Right', 400)
        tree.dock.setToolTip('Press ENTER after done editing a value to remake the objects.')
        tree.dock.setToolTipDuration(2000)

        # Main window for tree
        tree.main_window.setCentralWidget(tree)
        tree.resizeColumnToContents(0)

    def _setup_tree_design_options(self):
        tree = self.tree_design_ops = Tree_Default_Options(
            self, content_dict=self.design.params, gui=self)
        tree.main_window = QMainWindow(self)
        tree.dock = self._add_dock('Design Properties', tree.main_window, 'Right', 400)

        # Main window for tree
        tree.main_window.setCentralWidget(tree)
        self.tabifyDockWidget(self.tree_design_ops.dock, self.tree.dock)
        tree.resizeColumnToContents(0)


        ### ADD VARIABLE TAB
        tree = self.tree_design_vars = Tree_Default_Options(
            self, content_dict=self.design.variables, gui=self)
        tree.main_window = QMainWindow(self)
        tree.dock = self._add_dock('Variables', tree.main_window, 'Right', 400)

        # Main window for tree
        tree.main_window.setCentralWidget(tree)
        self.tabifyDockWidget(self.tree_design_vars.dock, self.tree.dock)
        tree.resizeColumnToContents(0)

    @catch_exception_slot_pyqt()
    def reload_stylesheet(self, _):
        self.load_stylesheet(path=self._style_sheet_path)

    def load_stylesheet(self, path=None):
        """
        Load and set stylesheet for the main gui

        Keyword Arguments:
            path {[str]} -- [Path tos tylesheet. Can also de default] (default: {None})
        """

        if path == 'default':
            self.setStyleSheet(path)
            return True

        if path is None:
            path = self.imgs_path.parent/'_style_sheets'/self._style_sheet_name

        path = Path(path)
        self._style_sheet_path = str(path)

        if path.is_file():
            stylesheet = path.read_text()
            # replace all :/ with the corrent path or handle correctly
            stylesheet = stylesheet.replace(':/', str(self.imgs_path))

            self.setStyleSheet(stylesheet)
        else:
            self.logger.error('Could not find the stylesheet file where expected %s', path)
            return False

        return True

    def _setup_window_style(self):

        # TODO: Not sure this works correctly, probably needs to be fixed
        QDir.setCurrent(str(self.imgs_path.parent))  # should not do this here, change parth
        QtCore.QDir.addSearchPath(':', str(self.imgs_path))

        self.load_stylesheet()

        # fusion macintosh # windows
        self.setStyle(QtWidgets.QStyleFactory.create("fusion"))
        #self.fig_window.statusBar().setStyleSheet(f'''QLabel{{ {base} }}''')

    def _add_dock(self, name, widget, location, minimum_width=None):
        '''
        location: Left, Right, ...
        '''

        dock = QDockWidget(name)

        # Sets the widget for the dock widget to widget.
        # If the dock widget is visible when widget is added, you must show() it explicitly.
        # Note that you must add the layout of the widget before you call this function; if not, the widget will not be visible.
        dock.setWidget(widget)

        # A floating dock widget is presented to the user as an independent window "on top" of its parent QMainWindow,
        # instead of being docked in the QMainWindow.
        dock.setFloating(False)

        # Add Menu button show/hide to main window
        self.menu_windows.addAction(dock.toggleViewAction())

        # Add to main window
        self.addDockWidget(getattr(Qt, location+'DockWidgetArea'), dock)

        if minimum_width:
            dock.setMinimumWidth(minimum_width)

        return dock

    def _logging_remove_handler(self, handler, logger_):
        """Remove logging handler when closing window

        Arguments:
            logger_ {[type]} -- [description]
            handler {[type]} -- [description]
        """
        for i, handler in enumerate(logger_.handlers):
            if handler is handler:
                logger_.handlers.pop(i)
                break

    def closeEvent(self, event):
        """
        This event handler is called with the given event when Qt receives a window close request for a top-level widget from the window system.

            By default, the event is accepted and the widget is closed. ]

        Arguments:
            event {[type]} -- [description]
        """
        try:
            self._logging_remove_handler(self._log_handler, logger)
            if 0:
                self._logging_remove_handler(self._log_handler_pyEPR, logging.getLogger('pyEPR'))
        except Exception as e:
            print(f'Error while closing main gui window: {e}')
        finally:
            super().closeEvent(event)

    ##########################################################################################

    def re_draw_func(self, x):
        """
        Function used when processing the drawing
        Can overwrite to scale. THis is somewhat legacy code,but can be useful
        still

        Example redefinition:
            lambda x: scale_objs(x, 1E3, 1E3, 1E3,(0,0))

        Arguments:
            x {[Dict]} -- [Dict of obecjts ]

        Returns:
            [Dict] -- [Affine transofrmed objects]
        """
        return x

    @catch_exception_slot_pyqt()
    def re_draw(self, *args):  # pylint: disable=unused-argument
        '''
        Calls draw_all_objects. Does correct handling of gui figure.
        The *args is to handle pyQtSlots
        '''
        logger.debug('Redrawing')
        self.fig_window.setStatusTip('Redrawing')
        self.fig_draw.canvas.hide()
        self.ax_draw.clear_me()

        try:
            draw_all_objects(self.objects, ax=self.ax_draw,
                             func=self.re_draw_func)
        except Exception:
            self.logger.error('\n\n'+traceback.format_exc())
            # Alternative:     exc_info = sys.exc_info()  traceback.print_exception(*exc_info)

        plot_simple_gui_style(self.ax_draw)

        self.fig_draw.canvas.show()
        self.fig_draw.canvas.draw()
        self.fig_window.setStatusTip('Redrawing:DONE')

    @catch_exception_slot_pyqt()
    def refresh_tree(self, *args):  # pylint: disable=unused-argument
        """
        Refresh the objects tree
        Calls repopulate on the Tree
        """
        self.tree.rebuild()  # change name to refresh?
        # self.tree_def_ops.refresh()

    @catch_exception_slot_pyqt()
    def refresh_tree_default_options(self, *args):  # pylint: disable=unused-argument
        """
        Refresh the tree with default options.
        Calls repopulate on the Tree
        """
        self.tree_def_ops.rebuild()

    @catch_exception_slot_pyqt()
    def refresh_all(self, *args):  # pylint: disable=unused-argument
        """
        Refresh all trees and plots and entire gui
        """
        self.re_draw()
        self.refresh_tree()
        self.refresh_tree_default_options()
        # print('self.tree_design_ops.rebuild()')
        self.tree_design_ops.rebuild()

    @catch_exception_slot_pyqt()
    def remake_all(self, *args):  # pylint: disable=unused-argument
        """
        Remake all objects and refresh plots
        """
        logger.info('Remaking all Metal objects from options')
        self.design.make_all_objects()
        self.re_draw()

    @catch_exception_slot_pyqt()
    def draw_connectors(self, *args):  # pylint: disable=unused-argument
        """
        Draw all connetors
        args used for pyqt socket
        """
        self.design.plot_connectors(ax=self.ax_draw)
        self.fig_draw.canvas.draw()

    @property
    def objects(self):
        """
        Returns:
            [Dict] -- [Handle to Design's objects]
        """
        return self._objects

    def set_objects(self, objects):
        '''
        Should ideally only ever have 1 instance object of objects
        '''
        if objects is None:
            objects = self.design.objects
        self._objects = objects
        if hasattr(self, 'tree'):
            self.tree.change_content_dict(objects)

    @property
    def DEFAULT_OPTIONS(self):
        """ Gets the DEFAULT_OPTIONS

        Returns:
            [Dict] -- [DEFAULT_OPTIONS]
        """
        return self._DEFAULT_OPTIONS

    def set_DEFAULT_OPTIONS(self, DEFAULT_OPTIONS):
        '''
        Should ideally only ever have 1 instance object of objects
        '''
        if DEFAULT_OPTIONS is None:
            from ..draw_functions import DEFAULT_OPTIONS
        self._DEFAULT_OPTIONS = DEFAULT_OPTIONS
        if hasattr(self, 'tree_def_ops'):
            self.tree_def_ops.change_content_dict(self._DEFAULT_OPTIONS)

    def resizeEvent(self, event):
        """
        Handles the resize event of the main window.
        Overwrittes parent class.
        Does not require a connect this way.

        QT:
        ----------------
        This event handler can be reimplemented in a subclass to receive widget
        resize events which are passed in the event parameter. When resizeEvent()
        is called, the widget already has its new geometry. The old size is
        accessible through QResizeEvent::oldSize().

        The widget will be erased and receive a paint event immediately after
        processing the resize event. No drawing need be (or should be) done inside
        this handler.

        Arguments:
            event {[(QResizeEvent]} -- [https://doc.qt.io/qt-5/qresizeevent.html]
        """
        ans = super().resizeEvent(event)
        self.fig_draw.tight_layout()
        # QApplication.instance().processEvents() # not needed
        return ans

    def fig_tight_layout(self):
        """
        Utility function, Does tight layout and redraw
        """
        self.fig_draw.tight_layout()
        self.fig_draw.canvas.draw()

    def getText(self, description="Select name", name='Name of new object:'):
        """Opens a QT dialog to get text, Utility function

        Keyword Arguments:
            description {str} -- [Dialog description displayed in gui when it pops us] (default: {"Select name"})
            name {str} -- [Dialog name] (default: {'Name of new object:'})

        Returns:
            [str or None] -- text from dialog or none is the test is '' or user cancels
        """
        text, ok_pressed = QInputDialog.getText(self, description, name, QLineEdit.Normal, "")
        if ok_pressed and text != '':
            return text
        return None

    @catch_exception_slot_pyqt()
    def clear_all_objects(self, *args):  # pylint: disable=unused-argument
        """
        Called by gui to clear all objects. Checks first with use dialog
        *args is required for the PyQt5 Socket
        """
        ret = QMessageBox.question(self, '', "Are you sure you want to clear all Metal objects?",
                                   QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            self.design.clear_all_objects()
            self.refresh_all()

    @catch_exception_slot_pyqt()
    def action_gds_export(self, *args):  # pylint: disable=unused-argument
        """
        Handles click on export to gds
        """
        filename = QFileDialog.getSaveFileName(None,
                                               'Select locaiton to export GDS file to')[0]
        if filename:
            self.design.gds_draw_all(filename)

    @catch_exception_slot_pyqt()
    def action_save_metal(self, *args):  # pylint: disable=unused-argument
        """
        Handles click on save design
        """
        filename = QFileDialog.getSaveFileName(None,
                                               'Select locaiton to save Metal objects and design to')[0]
        if filename:
            save_metal(filename, self.design)
            logger.info(f'Successfully save metal to {filename}')

    @catch_exception_slot_pyqt()
    def action_open_metal(self, *args):  # pylint: disable=unused-argument
        """
        Handles click on loading metal design
        """
        filename = QFileDialog.getOpenFileName(None,
                                               'Select locaiton to save Metal objects and design to')[0]
        if filename:
            design = load_metal(filename)  # do_update=True
            self.change_design(design)
            logger.info(f'Successfully loaded file\n file={filename}')

    def change_design(self, design):
        """Used in loading

        Arguments:
            design {[Metal_design_Base instance]} -- [new design]
        """
        self.design = design
        self.set_objects(self.design.objects)
        self.tree_design_ops.change_content_dict(self.design.params)
        self.logger.info('Changed design, updated default dictionaries, etc.')
        self.refresh_all()


def load_metal_object_module(metal_module_name):
    """
    Utility function to load module

    Arguments:
        metal_module_name {[str]} -- name

    Returns:
        imported module or False
    """

    try:
        module = importlib.import_module(metal_module_name)
        return module

    except ImportError as error:
        logger.error(
            f'ERROR (load_metal_object_module): Could not load object module for '\
            f'the toolbar.\n Failed to load \n\n >>> {metal_module_name} <<<\n\n Please check the '\
            f'name path and that the file does not have errors. \n\n**Error:** \n{error}\n\n**ERROR FULL TRACE:**\n'\
            f'{sys.exc_info()}')
        return False
