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
"""GUI front-end interface for Qiskit Metal in PySide2."""
# pylint: disable=invalid-name

import logging
import os
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING, List

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QAction
from PySide6.QtWidgets import (QWidget, QDialog, QDockWidget, QFileDialog,
                               QLabel, QMainWindow, QMessageBox, QVBoxLayout)
from PySide6.QtCore import QSortFilterProxyModel
from qiskit_metal._gui.widgets.qlibrary_display.delegate_qlibrary import \
    LibraryDelegate
from qiskit_metal._gui.widgets.qlibrary_display.file_model_qlibrary import \
    QFileSystemLibraryModel
from qiskit_metal._gui.widgets.qlibrary_display.proxy_model_qlibrary import \
    LibraryFileProxyModel

from qiskit_metal import config, qlibrary
from qiskit_metal.designs.design_base import QDesign
from qiskit_metal._gui.elements_window import ElementsWindow
from qiskit_metal._gui.net_list_window import NetListWindow
from qiskit_metal._gui.main_window_base import (QMainWindowBaseHandler, QMainWindowExtensionBase,
                               kick_start_qApp)
from qiskit_metal._gui.main_window_ui import Ui_MainWindow
from qiskit_metal._gui.renderer_gds_gui import RendererGDSWidget
from qiskit_metal._gui.renderer_hfss_gui import RendererHFSSWidget
from qiskit_metal._gui.renderer_q3d_gui import RendererQ3DWidget
from qiskit_metal._gui.utility._handle_qt_messages import slot_catch_error
from qiskit_metal._gui.utility._toolbox_qt import doShowHighlighWidget
from qiskit_metal._gui.widgets.all_components.table_model_all_components import \
    QTableModel_AllComponents
from qiskit_metal._gui.widgets.build_history.build_history_scroll_area import \
    BuildHistoryScrollArea
from qiskit_metal._gui.widgets.create_component_window import parameter_entry_window as pew
from qiskit_metal._gui.widgets.edit_component.component_widget import ComponentWidget
from qiskit_metal._gui.widgets.plot_widget.plot_window import QMainWindowPlot
from qiskit_metal._gui.widgets.variable_table import PropertyTableWidget

if not config.is_building_docs():
    pass

if TYPE_CHECKING:
    from ..renderers.renderer_mpl.mpl_canvas import PlotCanvas  # pylint: disable=syntax-error


class QMainWindowExtension(QMainWindowExtensionBase):
    """This contains all the functions that the gui needs to call directly from
    the UI.

    This class extends the `QMainWindowExtensionBase` class.

    To access the GUI Handler above this, call:
        self.handler = gui

    Args:
        QMainWindow (QMainWindow): Main window
    """

    def __init__(self):
        super().__init__()
        self.gds_gui = None  # type: RendererGDSWidget
        self.hfss_gui = None  # type: RendererHFSSWidget
        self.q3d_gui = None  # type: RendererQ3DWidget

    @property
    def design(self) -> 'QDesign':
        """Return the design.

        Returns:
            QDesign: The design
        """
        return self.handler.design

    @property
    def gui(self) -> 'MetalGUI':
        """Returns the MetalGUI."""
        return self.handler

    def _set_element_tab(self, yesno: bool):
        """Set which part of the element table is in use.

        Args:
            yesno (bool): True for View, False for Elements
        """

        if yesno:
            self.ui.tabWidget.setCurrentWidget(self.ui.tabQGeometry)
            self.ui.actionElements.setText("View")
        else:
            self.ui.tabWidget.setCurrentWidget(self.ui.mainViewTab)
            self.ui.actionElements.setText("QGeometry")

    def show_renderer_gds(self):
        """Handles click on GDS Renderer action."""
        self.gds_gui = RendererGDSWidget(self, self.gui)
        self.gds_gui.show()

    def show_renderer_hfss(self):
        """Handles click on HFSS Renderer action."""
        self.hfss_gui = RendererHFSSWidget(self, self.gui)
        self.hfss_gui.show()

    def show_renderer_q3d(self):
        """Handles click on Q3D Renderer action."""
        self.q3d_gui = RendererQ3DWidget(self, self.gui)
        self.q3d_gui.show()

    def delete_all_components(self):
        """Delete all components."""
        ret = QMessageBox.question(
            self,
            'Delete all components?',
            "Are you sure you want to clear all Metal components?",
            buttons=QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            self.logger.info('Delete all components.')
            self.design.delete_all_components()
            if self.component_window:
                self.gui.component_window.set_component(None)
            self.gui.refresh()

    @slot_catch_error()
    def save_design_copy(self):
        """Saves a separate copy of design under a different name"""
        filename = QFileDialog.getSaveFileName(
            None,
            'Select a new location to save Metal design to',
            self.design.get_design_name() + '.metal.py',
            selectedFilter='*.metal.py')[0]

        # save python script to file path
        pyscript = self.design.to_python_script()
        #check whether filename is empty or not. Save file only when filename is non-empty.
        if len(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(pyscript)

    @slot_catch_error()
    def save_design(self, _=None):
        """Handles click on save design."""
        if self.design:
            # get file path
            filename = self.design.save_path
            if not filename:
                QMessageBox.warning(
                    self, 'Warning', 'This  will save a .metal.py script '
                    'that needs to be copied into a jupyter notebook to run.'
                    'The "Load" button has not yet been implemented.')

                filename = QFileDialog.getSaveFileName(
                    None,
                    'Select a new location to save Metal design to',
                    self.design.get_design_name() + '.metal.py',
                    selectedFilter='*.metal.py')[0]
                self.design.save_path = filename
            # save python script to file path
            pyscript = self.design.to_python_script()
            #check whether filename is empty or not. Save file only when filename is non-empty.
            if len(filename):
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(pyscript)

                #make it clear it's saving
                saving_dialog = QDialog(self)
                saving_dialog.setWindowModality(Qt.NonModal)
                v = QVBoxLayout()
                saving_dialog.setLayout(v)
                v.addWidget(QLabel("Saving..."))
                saving_dialog.open()
                saving_dialog.show()
                QTimer.singleShot(200, saving_dialog.close)
        else:
            self.logger.info('No design present.')
            QMessageBox.warning(self, 'Warning', 'No design present! Can'
                                't save')

    @slot_catch_error()
    def load_design(self, _):
        """Handles click on loading metal design."""
        raise NotImplementedError()

    @slot_catch_error()
    def full_refresh(self, _=None):
        """Handles click on Refresh."""
        self.logger.info(
            r'Force refresh of all widgets (does not rebuild components)...')
        self.gui.refresh()
        self.gui.ui.mainViewTab.doShow()

    @slot_catch_error()
    def rebuild(self, _=None):
        """Handles click on Rebuild."""
        self.logger.info(
            r'Rebuilding all components in the model (and refreshing widgets)...'
        )
        self.gui.rebuild()
        #self.gui.ui.mainViewTab.doShow()

    @slot_catch_error()
    def create_build_log_window(self, _=None):
        """"Handles click on Build History button."""
        self.gui.gui_create_build_log_window()

    @slot_catch_error()
    def open_web_help(self, _=None):
        """"Handles click on Build History button."""
        webbrowser.open('https://qiskit-community.github.io/qiskit-metal/',
                        new=1)

    @slot_catch_error()
    def set_force_close(self, ison: bool):
        """Set method for force_close

        Args:
            ison (bool): value
        """
        self.force_close = ison

    @slot_catch_error()
    def closeEvent(self, event):
        """whenever a window is closed.

        Passed an event which we can choose to accept or reject.
        """

        if self.force_close:
            super().closeEvent(event)
            return

        will_close = self.ok_to_close()
        if will_close:
            self.save_window_settings()
            super().closeEvent(event)
        else:
            event.ignore()

    def ok_to_close(self):
        """Determine if it ok to continue.

        Returns:
            bool: True to continue, False otherwise
        """
        reply = QMessageBox.question(
            self, "Qiskit Metal", "Save unsaved changes to design?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)

        if reply == QMessageBox.Cancel:
            return False
        elif reply == QMessageBox.Yes:
            _ = self.save_design()
            return True
        return True


class MetalGUI(QMainWindowBaseHandler):
    """Main Qt window for interacting with a Qiskit Metal design.

    MetalGUI wraps a `QDesign` and gives you a synchronized visual view of
    components, variables, and geometry. Anything you do in the GUI (add/edit
    components, tweak options, rebuild) updates the underlying design object,
    and Python-side edits show up in the GUI after a rebuild.

    Key behaviors and subtleties:
    - Starts a Qt event loop if one is not already running.
    - Exposes docks for components, connectors, variables, and logs; you can
      hide/show or undock them without breaking synchronization.
    - The plot window shows the current QGeometry; call ``rebuild()`` after
      changing component options to refresh geometry before exporting or
      autoscaling.
    - Some imports are skipped when ``config.is_building_docs()`` is true to
      keep doc builds lean; avoid that flag in interactive GUI sessions.
    """

    __UI__ = Ui_MainWindow
    _QMainWindowClass = QMainWindowExtension
    _img_logo_name = 'metal_logo.png'
    _stylesheet_default = 'metal_dark'

    # This is somewhat outdated
    _dock_names = [
        'dockComponent', 'dockConnectors', 'dockDesign', 'dockLog',
        'dockLibrary', 'dockVariables'
    ]

    def __init__(self, design: QDesign = None):
        """Create a GUI bound to the provided ``design`` (or create one later).

        Args:
            design (QDesign, optional): The design to visualize and edit. You can
                also call ``set_design`` after constructing the GUI. When passed,
                the GUI will immediately populate docks and the canvas from this
                design. Defaults to None.
        """

        from .utility._handle_qt_messages import QtCore, _qt_message_handler
        QtCore.qInstallMessageHandler(_qt_message_handler)

        self.qApp = kick_start_qApp()
        if not self.qApp:
            logging.error("Could not start Qt event loop using QApplication.")

        super().__init__()

        # use set_design
        self.design = None  # type: QDesign

        # UIs
        self.plot_win = None  # type: QMainWindowPlot
        self.elements_win = None  # type: ElementsWindow
        self.net_list_win = None  # type: NetListWindow
        self.component_window = ComponentWidget(self, self.ui.dockComponent)
        self.variables_window = PropertyTableWidget(self, gui=self)

        self.build_log_window = None

        self._setup_component_widget()
        self._setup_plot_widget()
        self._setup_design_components_widget()
        self._setup_elements_widget()
        self.main_window.show()
        self._setup_variables_widget()
        self._ui_adjustments_final()
        self._setup_library_widget()
        self._setup_net_list_widget()

        # Show and raise
        self.main_window.show()

        # self.qApp.processEvents(QEventLoop.AllEvents, 1)
        # - don't think I need this here, it doesn't help to show and raise
        # - need to call from different thread.
        QTimer.singleShot(150, self._raise)

        if design:
            self.set_design(design)
        else:
            self._set_enabled_design_widgets(False)

    def _raise(self):
        """Raises the window to the top."""
        self.main_window.raise_()

        # Give keyboard focus.
        # On Windows, will change the color of the taskbar entry to indicate that the
        # window has changed in some way.
        self.main_window.activateWindow()

    def _set_enabled_design_widgets(self, enabled: bool = True):
        """Make rebuild and all the other main button disabled.

        Args:
            enabled (bool): True to enable, False to disable the design widgets.  Defaults to True.
        """

        def setEnabled(parent, widgets):
            for widgetname in widgets:
                if hasattr(parent, widgetname):
                    widget: 'QWidget' = getattr(parent, widgetname)
                    if widget:
                        widget.setEnabled(enabled)
                else:
                    self.logger.error(f'GUI issue: wrong name: {widgetname}')

        widgets = [
            'actionSave', 'action_full_refresh', 'actionRebuild',
            'actionDelete_All', 'dockComponent', 'dockLibrary', 'dockDesign',
            'dockConnectors'
        ]
        setEnabled(self.ui, widgets)

        widgets = ['component_window', 'elements_win', 'net_list_win']
        setEnabled(self, widgets)

    def set_design(self, design: QDesign):
        """Bind a ``QDesign`` to the GUI and refresh all views.

        This wires the provided design into the plot window, component lists,
        netlist, variables table, and any renderer sub-GUIs (GDS/HFSS/Q3D).
        Call this once after constructing the GUI or when swapping designs.

        Args:
            design (QDesign): The design to visualize/edit. Must be non-None.
        """
        self.design = design

        self._set_enabled_design_widgets(True)

        self.plot_win.set_design(design)
        self.elements_win.force_refresh()
        self.net_list_win.force_refresh()

        if self.main_window.gds_gui:
            self.main_window.gds_gui.set_design(design)

        if self.main_window.hfss_gui:
            self.main_window.hfss_gui.set_design(design)

        if self.main_window.q3d_gui:
            self.main_window.q3d_gui.set_design(design)

        self.variables_window.set_design(design)

        # Refresh
        self.refresh()

    def _setup_logger(self):
        """Setup the logger."""
        super()._setup_logger()

        logger = logging.getLogger('metal')
        self._log_handler_design = self.create_log_handler('metal', logger)

    def refresh_design(self):
        """Refresh design properties associated with the GUI."""
        self.update_design_name()

    def update_design_name(self):
        """Update the design name."""
        if self.design:
            design_name = self.design.get_design_name()
            self.main_window.setWindowTitle(self.config.main_window.title +
                                            f' — {design_name}')

    def _ui_adjustments(self):
        """Any touchups to the loaded ui that need be done soon."""
        # QTextEditLogger
        self.ui.log_text.img_path = Path(self.path_imgs)
        self.ui.log_text.dock_window = self.ui.dockLog

        # Add a second label to the status bar
        status_bar = self.main_window.statusBar()
        self.statusbar_label = QLabel(status_bar)
        self.statusbar_label.setText('')
        status_bar.addWidget(self.statusbar_label)

        # Docks
        # Left handside
        self.main_window.splitDockWidget(self.ui.dockDesign,
                                         self.ui.dockComponent, Qt.Vertical)
        self.main_window.tabifyDockWidget(self.ui.dockDesign,
                                          self.ui.dockLibrary)
        self.main_window.tabifyDockWidget(self.ui.dockLibrary,
                                          self.ui.dockConnectors)
        self.main_window.tabifyDockWidget(self.ui.dockConnectors,
                                          self.ui.dockVariables)
        self.ui.dockDesign.raise_()
        self.main_window.resizeDocks([self.ui.dockDesign], [350], Qt.Horizontal)

        # Log
        self.ui.dockLog.parent().resizeDocks([self.ui.dockLog], [120],
                                             Qt.Vertical)

        # toolBarView additions
        self._add_additional_qactions_tool_bar_view()

        # Tab positions
        self.ui.tabWidget.setCurrentIndex(0)

    def _ui_adjustments_final(self):
        """Any touchups to the loaded ui that need be done after all the base
        and main ui is loaded."""
        if self.component_window:
            self.component_window.setCurrentIndex(0)

    def _add_additional_qactions_tool_bar_view(self):
        """Programatically add the side toolbar buttons for showing/hiding the main docks
        such as create coomponent, edit one, log dock, etc."""
        toolbar = self.ui.toolBarView
        toolbarInsertBefore = self.ui.actionToggleDocks  # insert before this action

        DOCKS = [(self.ui.dockLibrary, r":/design"),
                 (self.ui.dockDesign, r":/component"), (None, '-----'),
                 (self.ui.dockVariables, r":/variables"),
                 (self.ui.dockConnectors, r":/connectors"),
                 (self.ui.dockLog, r":/log"), (None, '-----')]

        for row in DOCKS:
            dock = row[0]
            iconName = row[1]
            if iconName == '-----':
                toolbar.insertSeparator(toolbarInsertBefore)
                continue

            # Icons
            icon = QIcon()
            icon.addPixmap(QPixmap(iconName), QIcon.Normal, QIcon.Off)

            # Function call & monkey patch class instance ala Monkey Patch
            dock.doShow = doShowHighlighWidget.__get__(dock, type(dock))  # pylint: disable=assignment-from-no-return, no-value-for-parameter

            # QT Action with trigger, embed in toolbar
            action = QAction('', dock, triggered=dock.doShow)
            action.setIcon(icon)
            dock.actionShow = action  # save action

            # insert action in toolbar
            toolbar.insertAction(toolbarInsertBefore, action)

    def _set_element_tab(self, yesno: bool):
        """Set the elements tabl to Elements or View.

        Args:
            yesno (bool): True for elements, False for view
        """
        if yesno:
            self.ui.tabWidget.setCurrentWidget(self.ui.tabQGeometry)
        else:
            self.ui.tabWidget.setCurrentWidget(self.ui.mainViewTab)

    def _setup_component_widget(self):
        """Setup the components widget."""
        if self.component_window:
            self.ui.dockComponent.setWidget(self.component_window)

    def _setup_variables_widget(self):
        """Setup the variables widget."""
        self.ui.dockVariables.setWidget(self.variables_window)
        # hookup to delete action
        self.ui.btn_comp_del.clicked.connect(
            self.ui.tableComponents.delete_selected_rows)
        self.ui.btn_comp_rename.clicked.connect(
            self.ui.tableComponents.rename_row)
        self.ui.btn_comp_zoom.clicked.connect(self.btn_comp_zoom_fx)

    def _setup_plot_widget(self):
        """Create main Window Widget Plot."""
        self.plot_win = QMainWindowPlot(self, self.main_window)

        # Add to the tabbed main view
        self.ui.mainViewTab.layout().addWidget(self.plot_win)

        # add highlight function ala Monkey Patch
        obj = self.ui.mainViewTab
        obj.doShow = doShowHighlighWidget.__get__(obj, type(obj))  # pylint: disable=assignment-from-no-return, no-value-for-parameter

        # Move the dock
        self._move_dock_to_new_parent(self.ui.dockLog, self.plot_win)
        self.ui.dockLog.parent().resizeDocks([self.ui.dockLog], [120],
                                             Qt.Vertical)

    def _move_dock_to_new_parent(self,
                                 dock: QDockWidget,
                                 new_parent: QMainWindow,
                                 dock_location=Qt.BottomDockWidgetArea):
        """The the doc to a different parent window.

        Args:
            dock (QDockWidget): Dock to move
            new_parent (QMainWindow): New parent window
            dock_location (Qt dock location): Location of the dock.
                Defaults to Qt.BottomDockWidgetArea.
        """
        dock.setParent(new_parent)
        new_parent.addDockWidget(dock_location, dock)
        dock.setFloating(False)
        dock.show()
        dock.setMaximumHeight(99999)

    def _setup_elements_widget(self):
        """Create main Window Elements Widget."""
        self.elements_win = ElementsWindow(self, self.main_window)

        # Component filter
        self.ui.tabQGeometry.sort_model = QSortFilterProxyModel()
        self.ui.tabQGeometry.sort_model.setSourceModel(self.elements_win.model)
        self.ui.tabQGeometry.sort_model.setFilterKeyColumn(1)

        self.elements_win.ui.tableElements.setModel(
            self.ui.tabQGeometry.sort_model)
        self.elements_win.ui.tableElements.setSortingEnabled(True)

        # Add a text changed event to the QGeometry/Component/Layer text boxes
        self.elements_win.ui.lineEdit.textChanged.connect(
            self.elements_lineEdit_onChanged)
        self.elements_win.ui.lineEdit_2.textChanged.connect(
            self.elements_lineEdit_2_onChanged)

        # Add to the tabbed main view
        self.ui.tabQGeometry.layout().addWidget(self.elements_win)

    def elements_lineEdit_onChanged(self, text):
        """ Text changed event for QGeometry/Component text box
        Args:
            text: Text typed in the filter box.
        """
        self.ui.tabQGeometry.sort_model.setFilterKeyColumn(1)
        self.ui.tabQGeometry.sort_model.setFilterWildcard(text)

    def elements_lineEdit_2_onChanged(self, text):
        """ Text changed event for QGeometry/Layer text box
        Args:
            text: Text typed in the filter box.
        """
        self.ui.tabQGeometry.sort_model.setFilterKeyColumn(3)
        self.ui.tabQGeometry.sort_model.setFilterWildcard(text)

    def _setup_net_list_widget(self):
        """Create main Window Elements Widget."""
        self.net_list_win = NetListWindow(self, self.main_window)

        self.ui.tabNetList.sort_model = QSortFilterProxyModel()
        self.ui.tabNetList.sort_model.setSourceModel(self.net_list_win.model)

        self.net_list_win.ui.tableElements.setModel(
            self.ui.tabNetList.sort_model)
        self.net_list_win.ui.tableElements.setSortingEnabled(True)

        # Add to the tabbed main view
        self.ui.tabNetList.layout().addWidget(self.net_list_win)

    def _setup_design_components_widget(self):
        """Design components.

        Table model that shows the summary of the components of a design
        in a table with their names, classes, and modules
        """
        model = QTableModel_AllComponents(self,
                                          logger=self.logger,
                                          tableView=self.ui.tableComponents)
        # Add Sort/Filter logic to the components table
        self.ui.proxyModel = QSortFilterProxyModel()
        self.ui.proxyModel.setSourceModel(model)

        # search all columns
        self.ui.proxyModel.setFilterKeyColumn(-1)
        self.ui.tableComponents.setSortingEnabled(True)
        self.ui.tableComponents.setModel(self.ui.proxyModel)

        # Add a text changed event to the filter text box
        self.ui.filter_text_design.textChanged.connect(
            self.filter_text_design_onChanged)

    def filter_text_design_onChanged(self, text):
        """ Text changed event for filter_text_design
        Args:
            text: Text typed in the filter box.
        """
        self.ui.proxyModel.setFilterWildcard(text)

    def _create_new_component_object_from_qlibrary(self, full_path: str):
        """
        Must be defined outside of _setup_library_widget to ensure
        self == MetalGUI and will retain opened ScrollArea

        Args:
            relative_index: QModelIndex of the desired QComponent file in
                the Qlibrary GUI display

        """
        try:
            self.param_window = pew.create_parameter_entry_window(
                self, full_path, self.main_window)
        except Exception as e:
            self.logger.error(
                f"Unable to open param entry window due to Exception: {e} ")

    def _setup_library_widget(self):
        """
        Sets up the GUI's QLibrary display in Model-View-Controler framework

        For debug use:
            view = gui.main_window.ui.dockLibrary_tree_view
            model = gui.ui.dockLibrary.proxy_library_model
            model0 = gui.ui.dockLibrary.library_model
        """
        dock = self.ui.dockLibrary

        # --------------------------------------------------
        # Model

        # getting absolute path of Qlibrary folder
        init_qlibrary_abs_path = os.path.abspath(qlibrary.__file__)
        qlibrary_abs_path = init_qlibrary_abs_path.split('__init__.py')[0]
        self.QLIBRARY_ROOT = qlibrary_abs_path
        self.QLIBRARY_FOLDERNAME = qlibrary.__name__

        # create model for Qlibrary directory
        dock.library_model = QFileSystemLibraryModel(self.path_imgs)

        dock.library_model.setRootPath(self.QLIBRARY_ROOT)

        # QSortFilterProxyModel
        #QSortFilterProxyModel: sorting items, filtering out items, or both.
        #   maps the original model indexes to new indexes, allows a given
        # source model to be restructured as far as views are concerned
        # without requiring any transformations on the underlying data, and
        # without duplicating the data in memory.
        dock.proxy_library_model = LibraryFileProxyModel()
        dock.proxy_library_model.setSourceModel(dock.library_model)
        dock.proxy_library_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        dock.proxy_library_model.setRecursiveFilteringEnabled(True)

        # --------------------------------------------------
        # View
        view = self.ui.dockLibrary_tree_view

        view.setModel(dock.proxy_library_model)
        view.setRootIndex(
            dock.proxy_library_model.mapFromSource(
                dock.library_model.index(dock.library_model.rootPath())))

        # try empty one if no work
        view.setItemDelegate(LibraryDelegate(self.main_window))
        view.itemDelegate().tool_tip_signal.connect(view.setToolTip)

        view.qlibrary_filepath_signal.connect(
            self._create_new_component_object_from_qlibrary)

        # https://stackoverflow.com/questions/16759088/what-is-the-viewport-of-a-tree-widget
        view.viewport().setAttribute(Qt.WA_Hover, True)
        view.viewport().setMouseTracking(True)

        view.resizeColumnToContents(0)

        libraryRootPath = Path(dock.library_model.rootPath()) / "qubits"
        stringLibraryRootPath = str(libraryRootPath)
        view.expand(
            dock.proxy_library_model.mapFromSource(
                dock.library_model.index(stringLibraryRootPath)))

        # Add a text changed event to the filter text box
        self.ui.dockLibrary_filter.textChanged.connect(
            self.dockLibrary_filter_onChanged)

    def dockLibrary_filter_onChanged(self, text):
        """ Text changed event for filter_text_design
        Args:
            text: Text typed in the filter box.
        """
        view = self.ui.dockLibrary_tree_view
        dock = self.ui.dockLibrary
        proxy_model = dock.proxy_library_model

        # Wrap changes to filter_text and setFilterWildcard with reset calls
        proxy_model.beginResetModel()
        try:
            proxy_model.filter_text = text
            proxy_model.setFilterWildcard(text)
        finally:
            proxy_model.endResetModel()

        view.setRootIndex(
            proxy_model.mapFromSource(
                dock.library_model.index(dock.library_model.rootPath())))

        if len(text) >= 1 and proxy_model.rowCount() > 0:
            view.expandAll()
        else:
            view.collapseAll()

    ################################################
    # UI
    def toggle_docks(self, do_hide: bool = None):
        """Show or hide the full plot-area widget / show or hide all docks.

        Args:
            do_hide (bool): Hide or show. Defaults to None -- toggle.
        """
        self.main_window.toggle_all_docks(do_hide)
        self.qApp.processEvents(
        )  # Process all events, so that if we take screenshot next it won't be partially updated

    ################################################
    # Plotting
    def get_axes(self, num: int = None):
        """Return access to the canvas axes. If num is specified, returns the
        n-th axis.

        Args:
            num (int, optional): If num is specified, returns the n-th axis.  Defaults to None.

        Returns:
            List[Axes] or Axes: Of the canvas
        """
        axes = self.plot_win.canvas.axes
        if num is not None:
            axes = axes[num]
        return axes

    @property
    def axes(self) -> List['matplotlib.plt.Axes']:
        """Returns the axes."""
        return self.plot_win.canvas.axes

    @property
    def figure(self):
        """Return axis to the figure of the canvas."""
        return self.plot_win.canvas.figure

    @property
    def canvas(self) -> 'PlotCanvas':
        """Get access to the canvas that handles the figure and axes, and their
        main functions.

        Returns:
            PlotCanvas: The canvas
        """
        return self.plot_win.canvas

    def rebuild(self, autoscale: bool = False):
        """Rebuild all components and refresh the GUI.

        Calls ``design.rebuild()`` (regenerates QGeometry for all components),
        then refreshes tables and plots. Optionally autoscale after the redraw.

        Args:
            autoscale (bool): If True, call ``self.autoscale()`` after refresh.
        """

        self.design.rebuild()
        self.refresh()
        if autoscale:
            self.autoscale()

    def refresh(self):
        """Refreshes everything. Overkill in general.

            * Refreshes the design names in the gui
            * Refreshes the table models
            * Replots everything

        Warning:
            This does *not* rebuild the components.
            For that, call rebuild.
        """

        # Global level
        self.refresh_design()

        # Table models
        self.ui.tableComponents.model().sourceModel().refresh()

        # Redraw plots
        self.refresh_plot()

    def refresh_plot(self):
        """Redraw only the plot window contents."""
        self.plot_win.replot()

    def autoscale(self):
        """Shortcut to autoscale all views."""
        self.plot_win.auto_scale()

    #########################################################
    # COMPONENT FUNCTIONS
    def edit_component(self, name: str):
        """Make the named component active in the component editor widget.

        Args:
            name (str): Component name to load. Must exist in ``design.components``.

        Note:
            This does not rebuild geometry; use ``rebuild()`` if options are changed.
        """
        if self.component_window:
            self.component_window.set_component(name)

    def highlight_components(self, component_names: List[str]):
        """Visually highlight components in the plot canvas.

        Args:
            component_names (List[str]): Names to highlight; others remain unhighlighted.
        """
        self.canvas.highlight_components(component_names)

    def zoom_on_components(self, components: List[str]):
        """Zoom the canvas to fit the given components.

        Args:
            components (List[str]): Names of components to frame.
        """
        bounds = self.canvas.find_component_bounds(components)
        self.canvas.zoom_to_rectangle(bounds)

    def btn_comp_zoom_fx(self):
        """
        Zooms in display on selected QComponent
        """
        names = self.ui.tableComponents.name_of_selected_qcomponent()
        self.zoom_on_components(names)

    @slot_catch_error()
    def gui_create_build_log_window(self, _=None):
        """Creates a separate window that displays the recent successful/fails
        of all components for the design.

        Args:
            _ (object, optional): Default parameters for slot  - used to call from action
        """
        self.build_log_window = BuildHistoryScrollArea(
            self.design.build_logs.data())
        self.build_log_window.show()

    def save_file(self):
        """Save file. Called on exit.

        Raises:
            NotImplementedError: Function not written
        """
        print("TODO: Save file - not yet implemented here")
        raise NotImplementedError()
