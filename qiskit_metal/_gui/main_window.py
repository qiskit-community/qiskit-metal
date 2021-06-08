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
"""GUI front-end interface for Qiskit Metal in PySide2."""
# pylint: disable=invalid-name

import logging
import os
from pathlib import Path
from typing import List, TYPE_CHECKING

from PySide2.QtCore import QTimer, Qt
from PySide2.QtWidgets import (QDockWidget, QFileDialog, QLabel, QMainWindow,
                               QMessageBox)
from PySide2.QtGui import QIcon, QPixmap
from qiskit_metal._gui.widgets.qlibrary_display.delegate_qlibrary import LibraryDelegate
from qiskit_metal._gui.widgets.qlibrary_display.file_model_qlibrary import QFileSystemLibraryModel
from qiskit_metal._gui.widgets.qlibrary_display.proxy_model_qlibrary import LibraryFileProxyModel
from .elements_window import ElementsWindow
from .main_window_base import QMainWindowBaseHandler, QMainWindowExtensionBase, kick_start_qApp
from .main_window_ui import Ui_MainWindow
from .renderer_gds_gui import RendererGDSWidget
from .renderer_hfss_gui import RendererHFSSWidget
from .renderer_q3d_gui import RendererQ3DWidget
from .utility._handle_qt_messages import slot_catch_error
from .widgets.all_components.table_model_all_components import \
    QTableModel_AllComponents
from .widgets.build_history.build_history_scroll_area import BuildHistoryScrollArea
from .widgets.create_component_window import parameter_entry_window as pew
from .widgets.edit_component.component_widget import ComponentWidget
from .widgets.plot_widget.plot_window import QMainWindowPlot
from .widgets.variable_table import PropertyTableWidget
from .. import config, qlibrary
from ..designs.design_base import QDesign

if not config.is_building_docs():
    from ..toolbox_metal.import_export import load_metal_design

if TYPE_CHECKING:
    from ..renderers.renderer_mpl.mpl_canvas import PlotCanvas


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
            self.ui.tabWidget.setCurrentWidget(self.ui.tabElements)
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
            buttons=(QMessageBox.Yes | QMessageBox.No))
        if ret == QMessageBox.Yes:
            self.logger.info('Delete all components.')
            self.design.delete_all_components()
            if self.component_window:
                self.gui.component_window.set_component(None)
            self.gui.refresh()

    @slot_catch_error()
    def save_design_as(self, _=None):
        """Handles click on Save Design As."""
        filename = QFileDialog.getSaveFileName(
            None,
            'Select a new location to save Metal design to',
            self.design.get_design_name() + '.metal',
            selectedFilter='*.metal')[0]

        if filename:
            self.gui.save_file(filename)

    @slot_catch_error()
    def save_design(self, _=None):
        """Handles click on save design."""
        if self.design:
            if self.design.save_path:
                self.gui.save_file()
            else:
                self.save_design_as()
        else:
            self.logger.info('No design present.')
            QMessageBox.warning(self, 'Warning', 'No design present! Can'
                                't save')

    @slot_catch_error()
    def load_design(self, _):
        """Handles click on loading metal design."""
        filename = QFileDialog.getOpenFileName(
            None,
            'Select location to load Metal design from',
            selectedFilter='*.metal')[0]
        if filename:
            self.logger.info(f'Attempting to load design file {filename}')
            design = load_metal_design(filename)
            self.logger.info(
                f'Successfully loaded file. Now setting design into gui.')
            self.handler.set_design(design)
            self.logger.info(f'Successfully set design. Loaded and done.')

    @slot_catch_error()
    def full_refresh(self, _=None):
        """Handles click on Refresh."""
        self.logger.info(
            f'Force refresh of all widgets (does not rebuild components)...')
        self.gui.refresh()

    @slot_catch_error()
    def rebuild(self, _=None):
        """Handles click on Rebuild."""
        self.logger.info(
            f'Rebuilding all components in the model (and refreshing widgets)...'
        )
        self.gui.rebuild()

    @slot_catch_error()
    def create_build_log_window(self, _=None):
        """"Handles click on Build History button."""
        self.gui.gui_create_build_log_window()

    @slot_catch_error()
    def activate_developer_mode(self, ison: bool):
        """
        Sets the correct UI features for developer mode
        Args:
            ison: Whether developer mode is active

        """
        if ison:
            QMessageBox.warning(
                self, "Notice",
                "If you're editing a component via an external IDE,"
                " don't forget to refresh the component's file"
                " in the Library before rebuilding so your changes"
                " will take effect.")

        self.gui.ui.dockLibrary_tree_view.set_dev_mode(ison)
        self.gui.is_dev_mode = ison
        self.gui._set_rebuild_unneeded()
        # import rebuild
        # rebuild.activate_developer_mode(RebuildAction, RebuildFunction, QLibraryTree)
        # else:
        #  deactivateDeveMode()


class MetalGUI(QMainWindowBaseHandler):
    """Qiskit Metal Main GUI.

    This class extends the `QMainWindowBaseHandler` class.

    The GUI can be controlled by the user using the mouse and keyboard or
    API for full control.

    Args:
        QMainWindowBase (QMainWindowBase): Base window
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
        """
        Args:
            design (QDesign, optional): Pass in the design that the GUI should handle.
                Defaults to None.
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
        self.component_window = ComponentWidget(self, self.ui.dockComponent)
        self.variables_window = PropertyTableWidget(self, gui=self)

        self.build_log_window = None
        self.is_dev_mode = False
        self.action_rebuild_deactive_icon = QIcon()
        self.action_rebuild_deactive_icon.addPixmap(QPixmap(":/rebuild"),
                                                    QIcon.Normal, QIcon.Off)
        self.action_rebuild_active_icon = QIcon()
        self.action_rebuild_active_icon.addPixmap(QPixmap(":/rebuild_needed"),
                                                  QIcon.Normal, QIcon.Off)
        self.ui.actionRebuild.setIcon(self.action_rebuild_deactive_icon)
        #self.ui.toolBarDesign.setIconSize(QSize(20,20))

        self._setup_component_widget()
        self._setup_plot_widget()
        self._setup_design_components_widget()
        self._setup_elements_widget()
        self._setup_variables_widget()
        self._ui_adjustments_final()
        self._setup_library_widget()

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
                    widget = getattr(parent, widgetname)  # type: QWidget
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

        widgets = ['component_window', 'elements_win']
        setEnabled(self, widgets)

    def set_design(self, design: QDesign):
        """Core function to set a new design.

        Args:
            design (QDesign): A qiskit metal design, such as a planar one.
                The design contains all components and elements
        """
        self.design = design

        self._set_enabled_design_widgets(True)

        self.plot_win.set_design(design)
        self.elements_win.force_refresh()

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
        """Add QActions to toolBarView that cannot be added via QDesign"""

        # Library
        self.dock_library_qaction = self.ui.dockLibrary.toggleViewAction()
        library_icon = QIcon()
        library_icon.addPixmap(QPixmap(":/component"), QIcon.Normal, QIcon.Off)
        self.dock_library_qaction.setIcon(library_icon)
        self.ui.toolBarView.insertAction(self.ui.actionToggleDocks,
                                         self.dock_library_qaction)

        # Design
        self.dock_design_qaction = self.ui.dockDesign.toggleViewAction()
        design_icon = QIcon()
        design_icon.addPixmap(QPixmap(":/design"), QIcon.Normal, QIcon.Off)
        self.dock_design_qaction.setIcon(design_icon)
        self.ui.toolBarView.insertAction(self.ui.actionToggleDocks,
                                         self.dock_design_qaction)

        # Variables
        self.dock_variables_qaction = self.ui.dockVariables.toggleViewAction()
        variables_icon = QIcon()
        variables_icon.addPixmap(QPixmap(":/variables"), QIcon.Normal,
                                 QIcon.Off)
        self.dock_variables_qaction.setIcon(variables_icon)
        self.ui.toolBarView.insertAction(self.ui.actionToggleDocks,
                                         self.dock_variables_qaction)

        # Connectors
        self.dock_connectors_qaction = self.ui.dockConnectors.toggleViewAction()
        connectors_icon = QIcon()
        connectors_icon.addPixmap(QPixmap(":/connectors"), QIcon.Normal,
                                  QIcon.Off)
        self.dock_connectors_qaction.setIcon(connectors_icon)
        self.ui.toolBarView.insertAction(self.ui.actionToggleDocks,
                                         self.dock_connectors_qaction)

        # Log
        self.dock_log_qaction = self.ui.dockLog.toggleViewAction()
        log_icon = QIcon()
        log_icon.addPixmap(QPixmap(":/log"), QIcon.Normal, QIcon.Off)
        self.dock_log_qaction.setIcon(log_icon)
        self.ui.toolBarView.insertAction(self.ui.actionToggleDocks,
                                         self.dock_log_qaction)

    def _set_element_tab(self, yesno: bool):
        """Set the elements tabl to Elements or View.

        Args:
            yesno (bool): True for elements, False for view
        """
        if yesno:
            self.ui.tabWidget.setCurrentWidget(self.ui.tabElements)
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
            dock_location (Qt dock location): Location of the dock.  Defaults to Qt.BottomDockWidgetArea.
        """
        dock.setParent(new_parent)
        new_parent.addDockWidget(dock_location, dock)
        dock.setFloating(False)
        dock.show()
        dock.setMaximumHeight(99999)

    def _setup_elements_widget(self):
        """Create main Window Elements Widget."""
        self.elements_win = ElementsWindow(self, self.main_window)

        # Add to the tabbed main view
        self.ui.tabElements.layout().addWidget(self.elements_win)

    def _setup_design_components_widget(self):
        """Design components.

        Table model that shows the summary of the components of a design
        in a table with their names, classes, and modules
        """
        model = QTableModel_AllComponents(self,
                                          logger=self.logger,
                                          tableView=self.ui.tableComponents)
        self.ui.tableComponents.setModel(model)

    def _create_new_component_object_from_qlibrary(self, full_path: str):
        """
        Must be defined outside of _setup_library_widget to ensure self == MetalGUI and will retain opened ScrollArea

        Args:
            relative_index: QModelIndex of the desired QComponent file in the Qlibrary GUI display

        """
        try:
            self.param_window = pew.create_parameter_entry_window(
                self, full_path, self.main_window)
        except Exception as e:
            self.logger.error(
                f"Unable to open param entry window due to Exception: {e} ")

    def _refresh_component_build(self, qis_abs_path):
        """Refresh build for a component along a given path.

        Args:
            qis_abs_path (str): Absolute component path.
        """
        self.design.reload_and_rebuild_components(qis_abs_path)
        # Table models
        self.ui.tableComponents.model().refresh()

        # Redraw plots
        self.refresh_plot()
        self.autoscale()

    def _setup_library_widget(self):
        """
        Sets up the GUI's QLibrary display

        """

        # getting absolute path of Qlibrary folder
        init_qlibrary_abs_path = os.path.abspath(qlibrary.__file__)
        qlibrary_abs_path = init_qlibrary_abs_path.split('__init__.py')[0]
        self.QLIBRARY_ROOT = qlibrary_abs_path
        self.QLIBRARY_FOLDERNAME = qlibrary.__name__

        # create model for Qlibrary directory
        self.ui.dockLibrary.library_model = QFileSystemLibraryModel()

        self.ui.dockLibrary.library_model.setRootPath(self.QLIBRARY_ROOT)

        # QSortFilterProxyModel
        #QSortFilterProxyModel: sorting items, filtering out items, or both.  maps the original model indexes to new indexes, allows a given source model to be restructured as far as views are concerned without requiring any transformations on the underlying data, and without duplicating the data in memory.
        self.ui.dockLibrary.proxy_library_model = LibraryFileProxyModel()
        self.ui.dockLibrary.proxy_library_model.setSourceModel(
            self.ui.dockLibrary.library_model)

        self.ui.dockLibrary_tree_view.setModel(
            self.ui.dockLibrary.proxy_library_model)
        self.ui.dockLibrary_tree_view.setRootIndex(
            self.ui.dockLibrary.proxy_library_model.mapFromSource(
                self.ui.dockLibrary.library_model.index(
                    self.ui.dockLibrary.library_model.rootPath())))

        self.ui.dockLibrary_tree_view.setItemDelegate(
            LibraryDelegate(self.main_window))  # try empty one if no work
        self.ui.dockLibrary_tree_view.itemDelegate().tool_tip_signal.connect(
            self.ui.dockLibrary_tree_view.setToolTip)

        self.ui.dockLibrary_tree_view.qlibrary_filepath_signal.connect(
            self._create_new_component_object_from_qlibrary)
        self.ui.dockLibrary_tree_view.qlibrary_rebuild_signal.connect(
            self._refresh_component_build)
        self.ui.dockLibrary_tree_view.qlibrary_file_dirtied_signal.connect(
            self._set_rebuild_needed)

        self.ui.dockLibrary_tree_view.viewport().setAttribute(Qt.WA_Hover, True)
        self.ui.dockLibrary_tree_view.viewport().setMouseTracking(True)

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

    def _set_rebuild_needed(self):
        if self.is_dev_mode:
            self.main_window.ui.actionRebuild.setIcon(
                self.action_rebuild_active_icon)

    def _set_rebuild_unneeded(self):
        self.main_window.ui.actionRebuild.setIcon(
            self.action_rebuild_deactive_icon)

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
    def axes(self) -> List['Axes']:
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
        """
        Rebuild all components in the design from scratch and refresh the gui.
        """
        self._set_rebuild_unneeded()
        if self.is_dev_mode:
            self.refresh_everything()

        self.design.rebuild()
        self.refresh()
        if autoscale:
            self.autoscale()

    def refresh_everything(self):
        """Refresh everything."""

        df = self.ui.dockLibrary.library_model.dirtied_files
        values = {list(df[k])[0] for k in df.keys()}

        for file in values:  # dirtied_files size changes during clean_file
            if '.py' in file:
                file = file[file.index('qiskit_metal'):]
                self.design.reload_and_rebuild_components(file)
                self.ui.dockLibrary.library_model.clean_file(file)
        self.refresh()
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
        self.ui.tableComponents.model().refresh()

        # Redraw plots
        self.refresh_plot()

    def refresh_plot(self):
        """Redraw only the plot window contents."""
        self.plot_win.replot()

    def autoscale(self):
        """Shortcut to autoscale all views."""
        self.plot_win.auto_scale()

    #########################################################
    # Design level
    def save_file(self, filename: str = None):
        """Save the file.

        Args:
            filename (str): Filename to save.  Defaults to None.
        """
        self.design.save_design(filename)

    #########################################################
    # COMPONENT FUNCTIONS
    def edit_component(self, name: str):
        """Set the component to be examined by the component widget.

        Args:
            name (str): Name of component to exmaine.
        """
        if self.component_window:
            self.component_window.set_component(name)

    def highlight_components(self, component_names: List[str]):
        """Hihglight a list of components.

        Args:
            component_names (List[str]): List of component names to highlight
        """
        self.canvas.highlight_components(component_names)

    def zoom_on_components(self, components: List[str]):
        """Zoom to the components.

        Args:
            components (List[str]): List of components to zoom to
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
