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
"""GUI front-end interface for Quantum Metal, built on PySide6."""

import atexit
import logging
import os
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING, List

from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QIcon, QPixmap, QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QDialog,
    QDockWidget,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
)
from PySide6.QtCore import QSortFilterProxyModel
from qiskit_metal._gui.widgets.qlibrary_display.delegate_qlibrary import LibraryDelegate
from qiskit_metal._gui.widgets.qlibrary_display.file_model_qlibrary import (
    QFileSystemLibraryModel,
)
from qiskit_metal._gui.widgets.qlibrary_display.proxy_model_qlibrary import (
    LibraryFileProxyModel,
)

from qiskit_metal import config, qlibrary
from qiskit_metal.designs.design_base import QDesign
from qiskit_metal._gui.elements_window import ElementsWindow
from qiskit_metal._gui.net_list_window import NetListWindow
from qiskit_metal._gui.main_window_base import (
    QMainWindowBaseHandler,
    QMainWindowExtensionBase,
    kick_start_qApp,
)
from qiskit_metal._gui.main_window_ui import Ui_MainWindow
from qiskit_metal._gui.toolbar_layout import TOOLBAR_ICON_PX, apply_toolbar_layout
from qiskit_metal._gui.renderer_gds_gui import RendererGDSWidget
from qiskit_metal._gui.renderer_hfss_gui import RendererHFSSWidget
from qiskit_metal._gui.renderer_q3d_gui import RendererQ3DWidget
from qiskit_metal._gui.utility._handle_qt_messages import slot_catch_error
from qiskit_metal._gui.utility._nudge import offset_length
from qiskit_metal._gui.utility._toolbox_qt import (
    clear_dock_error_badge,
    doShowHighlighWidget,
    doToggleDockWidget,
    single_shot,
)
from qiskit_metal._gui.widgets.all_components.table_model_all_components import (
    QTableModel_AllComponents,
)
from qiskit_metal._gui.widgets.pins import QTableModel_Pins
from qiskit_metal._gui.widgets.build_history.build_history_scroll_area import (
    BuildHistoryScrollArea,
)
from qiskit_metal._gui.widgets.create_component_window import (
    parameter_entry_window as pew,
)
from qiskit_metal._gui.widgets.edit_component.component_widget import ComponentWidget
from qiskit_metal._gui.widgets.plot_widget.plot_window import QMainWindowPlot
from qiskit_metal._gui.tree_view_base import QTreeView_Base
from qiskit_metal._gui.widgets.edit_chip import QTreeModel_Chips
from qiskit_metal._gui.widgets.view_control import LayerVisibilityWidget
from qiskit_metal._gui.widgets.variable_table import PropertyTableWidget

if not config.is_building_docs():
    pass

if TYPE_CHECKING:
    from ..renderers.renderer_mpl.mpl_canvas import PlotCanvas

#: Styling for the selection hint in the status bar. A mid-tone teal reads
#: against both the dark and light stylesheets, so the hint does not need to
#: change with the theme. Scoped to the one label by being set on it directly.
SELECTION_HINT_STYLE = "color: #2a9d8f; font-weight: bold;"

#: Renderer key -> the pip extra that provides it, for the
#: "this renderer is not installed" message. Mirrors the install matrix in
#: docs/installation.rst.
RENDERER_EXTRAS = {
    "hfss": "ansys",
    "q3d": "ansys",
    "aedt_hfss": "ansys",
    "aedt_q3d": "ansys",
    "gmsh": "mesh",
    "elmer": "mesh",
}

# Issues #1048 / #1109: opt-in init-tracing for reporters whose MetalGUI
# silently aborts mid-init on Windows. When QISKIT_METAL_DEBUG_INIT is
# set, each init step prints to stderr with an explicit flush -- the
# last printed line identifies the failing call. No-op when unset.
from qiskit_metal._gui._init_trace import trace_init as _trace_init


def _teardown_qt_widgets():
    """Delete every top-level Qt widget before the interpreter finalizes.

    Fixes the segfault-at-exit reported in issue #1048. PySide6 otherwise
    destroys the ``QApplication`` during ``Py_FinalizeEx`` while ``MetalGUI``'s
    window is still alive; a ``QWidget`` destructor then dispatches an event
    through the main window's ``QMenuBar`` event filter whose target is already
    half-deleted, jumping to a null vtable entry and killing the process (in a
    Jupyter kernel this surfaces as "the kernel appears to have died").

    Deleting the widgets here -- while the interpreter and ``QApplication`` are
    still alive -- destroys them in the correct order. ``deleteLater`` is used
    rather than ``close()`` so this never triggers the "save unsaved changes?"
    dialog (which would block forever on a headless machine). The function is
    idempotent and exception-safe: it is only a best-effort cleanup.
    """
    try:
        # From here to process exit, log emission can race stream closure;
        # logging catches those internally and prints an un-suppressable
        # "--- Logging error ---" block per message via handleError()
        # (so a try/except at the call site never sees it). Turning off
        # logging.raiseExceptions is the documented switch for exactly
        # this production-shutdown situation.
        import logging as _logging

        _logging.raiseExceptions = False

        app = QApplication.instance()
        if app is None:
            return
        # Stop every timer FIRST, then delete. The deleteLater() queue and
        # any due timers are drained by the same processEvents() pass below;
        # without this sweep a timer callback can interleave with the
        # deletions and land on a widget whose C++ half is already gone --
        # a native use-after-free at interpreter exit (the pristine-process
        # exit segfaults in issue #1048 / the macOS CI matrix). QTimer's
        # stop() is safe to call repeatedly and on never-started timers.
        from PySide6.QtCore import QTimer

        for widget in list(app.topLevelWidgets()):
            for timer in widget.findChildren(QTimer):
                timer.stop()
        for widget in list(app.topLevelWidgets()):
            widget.deleteLater()
        app.processEvents()

        # Finish the job: drain the deferred-delete queue explicitly, then
        # destroy the QApplication itself while the interpreter is still
        # fully alive. Without this, the C++ QApplication (and with it the
        # QPA platform plugin and Qt's internal threads) is destroyed
        # during Py_FinalizeEx in whatever order module teardown happens
        # to produce -- the destructor-ordering race behind the rare
        # "completed everything, then exited -11" crashes on slow CI
        # runners (issue #1048, "Still open" in gui_crash_defenses.md).
        # Note the doc's trap about deleteLater under processEvents():
        # DeferredDelete events are only handled by exec() loops or an
        # explicit sendPostedEvents(None, DeferredDelete) -- which is why
        # that call is here and a plain processEvents() is not enough.
        from PySide6.QtCore import QEvent

        app.sendPostedEvents(None, QEvent.DeferredDelete)
        app.processEvents()
        try:
            import shiboken6

            shiboken6.delete(app)
        except Exception:  # pragma: no cover - best-effort finalization
            pass
    except Exception:  # pragma: no cover - cleanup must never raise at exit
        pass


class QMainWindowExtension(QMainWindowExtensionBase):
    """This contains all the functions that the gui needs to call directly from
    the UI.

    This class extends the `QMainWindowExtensionBase` class.

    To access the GUI Handler above this, call::

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
    def design(self) -> "QDesign":
        """Return the design.

        Returns:
            QDesign: The design
        """
        return self.handler.design

    @property
    def gui(self) -> "MetalGUI":
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

    def _renderer_available(self, renderer_key: str, label: str) -> bool:
        """Check a renderer registered, and explain it if not.

        ``QDesign._start_renderers`` skips any renderer whose module or
        transitive dependency is missing -- that is what makes a lite install
        work. The renderer then simply is not in ``design.renderers``, and
        opening its window would fail somewhere deeper with a message that
        does not mention the actual problem.

        This is a dictionary lookup, not an import: the import was already
        attempted (or skipped) when the design was created, so checking here
        costs nothing and cannot undo the lazy-import work.

        Args:
            renderer_key (str): Key in ``design.renderers``.
            label (str): Human name for the message.

        Returns:
            bool: True if the renderer is registered and its window can open.
        """
        if renderer_key in self.design.renderers:
            return True

        message = (
            f"The {label} renderer is not available in this install.\n\n"
            "Its Python dependencies are not present, so it was skipped when "
            "the design was created.\n\n"
            "Install the extra that provides it:\n"
            f'    pip install "quantum-metal[{RENDERER_EXTRAS.get(renderer_key, "full")}]"\n\n'
            "See docs/installation.rst for the full matrix."
        )
        self.logger.warning(
            f"{label} renderer unavailable: '{renderer_key}' is not registered "
            "in design.renderers."
        )
        QMessageBox.warning(self, f"{label} renderer unavailable", message)
        return False

    def _warn_if_ansys_unlikely(self, label: str) -> None:
        """Note that Ansys AEDT itself is a separate, non-Python requirement.

        The Python side registering says nothing about whether AEDT is
        installed and reachable -- that only surfaces when the renderer tries
        to connect. Deliberately does not probe for a running AEDT: that is
        slow and can block the UI.

        Args:
            label (str): Human name for the message.
        """
        if os.name == "nt":
            return
        message = (
            f"{label} needs Ansys AEDT, which is Windows-only. The window will "
            "open, but connecting to AEDT will fail on this platform. For an "
            "Ansys-free path see the open FEM stack (gmsh + Elmer / Palace)."
        )
        self.logger.warning(message)
        # The log dock is hidden by default (see the Log toolbar button),
        # so this-platform-can't-reach-AEDT was easy to miss entirely and
        # only surfaced later as a confusing connection failure. A popup is
        # appropriate here specifically because it's low-frequency -- once
        # per renderer window opened, not per rebuild -- unlike geometry
        # warnings (e.g. check_lengths' short-segment/fillet notices) which
        # can fire many times per edit and would make a popup a nuisance;
        # those stay log-only. Shown once per label per session -- the
        # message doesn't change on repeat clicks, only the annoyance would.
        already_warned = getattr(self, "_ansys_unlikely_warned", None)
        if already_warned is None:
            already_warned = self._ansys_unlikely_warned = set()
        if label not in already_warned:
            already_warned.add(label)
            QMessageBox.warning(self, f"{label} renderer", message)

    def show_renderer_gds(self):
        """Handles click on GDS Renderer action."""
        if not self._renderer_available("gds", "GDS"):
            return
        self.gds_gui = RendererGDSWidget(self, self.gui)
        self.gds_gui.show()

    def show_renderer_hfss(self):
        """Handles click on HFSS Renderer action."""
        if not self._renderer_available("hfss", "HFSS"):
            return
        self._warn_if_ansys_unlikely("HFSS")
        self.hfss_gui = RendererHFSSWidget(self, self.gui)
        self.hfss_gui.show()

    def show_renderer_q3d(self):
        """Handles click on Q3D Renderer action."""
        if not self._renderer_available("q3d", "Q3D"):
            return
        self._warn_if_ansys_unlikely("Q3D")
        self.q3d_gui = RendererQ3DWidget(self, self.gui)
        self.q3d_gui.show()

    def delete_all_components(self):
        """Delete all components."""
        ret = QMessageBox.question(
            self,
            "Delete all components?",
            "Are you sure you want to clear all Metal components?",
            buttons=QMessageBox.Yes | QMessageBox.No,
        )
        if ret == QMessageBox.Yes:
            self.logger.info("Delete all components.")
            self.design.delete_all_components()
            if self.component_window:
                self.gui.component_window.set_component(None)
            self.gui.refresh()

    @slot_catch_error()
    def save_design_copy(self):
        """Saves a separate copy of design under a different name"""
        filename = QFileDialog.getSaveFileName(
            None,
            "Select a new location to save Metal design to",
            self.design.get_design_name() + ".metal.py",
            selectedFilter="*.metal.py",
        )[0]

        # save python script to file path
        pyscript = self.design.to_python_script()
        # check whether filename is empty or not. Save file only when filename is non-empty.
        if len(filename):
            with open(filename, "w", encoding="utf-8") as f:
                f.write(pyscript)

    @slot_catch_error()
    def save_design(self, _=None):
        """Handles click on save design."""
        if self.design:
            # get file path
            filename = self.design.save_path
            if not filename:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "This  will save a .metal.py script "
                    "that needs to be copied into a jupyter notebook to run."
                    'The "Load" button has not yet been implemented.',
                )

                filename = QFileDialog.getSaveFileName(
                    None,
                    "Select a new location to save Metal design to",
                    self.design.get_design_name() + ".metal.py",
                    selectedFilter="*.metal.py",
                )[0]
                self.design.save_path = filename
            # save python script to file path
            pyscript = self.design.to_python_script()
            # check whether filename is empty or not. Save file only when filename is non-empty.
            if len(filename):
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(pyscript)

                # make it clear it's saving
                saving_dialog = QDialog(self)
                saving_dialog.setWindowModality(Qt.NonModal)
                v = QVBoxLayout()
                saving_dialog.setLayout(v)
                v.addWidget(QLabel("Saving..."))
                saving_dialog.open()
                saving_dialog.show()
                single_shot(saving_dialog, 200, saving_dialog.close)
        else:
            self.logger.info("No design present.")
            QMessageBox.warning(self, "Warning", "No design present! Cant save")

    @slot_catch_error()
    def load_design(self, _):
        """Handles click on loading metal design."""
        raise NotImplementedError()

    @slot_catch_error()
    def full_refresh(self, _=None):
        """Handles click on Refresh."""
        self.logger.info(
            r"Force refresh of all widgets (does not rebuild components)..."
        )
        self.gui.refresh()
        self.gui.ui.mainViewTab.doShow()

    @slot_catch_error()
    def rebuild(self, _=None):
        """Handles click on Rebuild."""
        self.logger.info(
            r"Rebuilding all components in the model (and refreshing widgets)..."
        )
        self.gui.rebuild()
        # self.gui.ui.mainViewTab.doShow()

    @slot_catch_error()
    def create_build_log_window(self, _=None):
        """ "Handles click on Build History button."""
        self.gui.gui_create_build_log_window()

    @slot_catch_error()
    def open_web_help(self, _=None):
        """ "Handles click on Build History button."""
        webbrowser.open("https://qiskit-community.github.io/qiskit-metal/", new=1)

    @slot_catch_error()
    def set_force_close(self, ison: bool):
        """Set method for force_close

        Args:
            ison (bool): value
        """
        self.force_close = ison

    def _refresh_timers(self):
        """Every periodic model-refresh timer belonging to this window.

        Three are reachable through the widget tree. The components-table
        model is parented to the ``MetalGUI`` handler rather than into the
        tree, so ``findChildren`` misses it and it is collected explicitly.
        """
        timers = list(self.findChildren(QTimer))

        proxy = getattr(self.ui, "proxyModel", None)
        if proxy is not None:
            try:
                source = proxy.sourceModel()
            except RuntimeError:
                source = None
            timer = getattr(source, "_timer", None)
            if timer is not None:
                timers.append(timer)
        return timers

    def showEvent(self, event):
        """Restart the polling timers when the window becomes visible.

        Pairs with the stop in ``closeEvent`` so that pausing is not a
        one-way trip: closing and reopening the same MetalGUI must leave the
        tables auto-refreshing as before (issue #1048).
        """
        for timer in self._refresh_timers():
            try:
                if not timer.isActive():
                    timer.start()
            except RuntimeError:
                # C++ object already gone -- nothing to restart.
                continue
        super().showEvent(event)
        self.enable_dock_tab_scrolling()

    def _stop_refresh_timers(self):
        """Pause the periodic model-refresh timers.

        Several table/tree models drive themselves from a repeating 500 ms
        ``QTimer``. Nothing stopped them on close, so they kept firing at
        models belonging to a window that was being destroyed -- visible as
        ``AttributeError: Slot 'QTableModel_AllComponents::' not found``, and
        a use-after-free waiting to happen if a tick lands mid-teardown
        (issue #1048). Stopping them makes close deterministic instead of a
        race against the next tick; ``showEvent`` restarts them, so a
        closed-and-reopened window polls again as before.

        Best-effort by design: this runs while the window is going away, so
        a model whose C++ object has already gone is not an error.
        """
        for timer in self._refresh_timers():
            try:
                timer.stop()
            except RuntimeError:
                # Shiboken raises RuntimeError when the timer's C++ object is
                # already gone. That is the desired end state -- a destroyed
                # timer cannot fire -- so there is nothing to do and nothing
                # worth logging on a window that is closing.
                continue

    @slot_catch_error()
    def closeEvent(self, event):
        """whenever a window is closed.

        Passed an event which we can choose to accept or reject.
        """

        if self.force_close:
            self._stop_refresh_timers()
            super().closeEvent(event)
            return

        will_close = self.ok_to_close()
        if will_close:
            self.save_window_settings()
            # Pause the polling timers while the window is hidden; showEvent()
            # restarts them, so closing and reopening the same MetalGUI -- the
            # exact workflow reported in issue #1048 -- keeps working.
            #
            # The log handlers are deliberately NOT detached here. close()
            # only hides the window, so a reopened window must still receive
            # records. They detach from the widget's destroyed signal instead,
            # which is the event that actually makes them dangerous.
            self._stop_refresh_timers()
            super().closeEvent(event)
        else:
            event.ignore()

    def ok_to_close(self):
        """Determine if it ok to continue.

        Returns:
            bool: True to continue, False otherwise
        """
        reply = QMessageBox.question(
            self,
            "Qiskit Metal",
            "Save unsaved changes to design?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
        )

        if reply == QMessageBox.Cancel:
            return False
        elif reply == QMessageBox.Yes:
            _ = self.save_design()
            return True
        return True


class MetalGUI(QMainWindowBaseHandler):
    """Main Qt window for interacting with a Quantum Metal design.

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
    _img_logo_name = "metal_logo.png"
    _stylesheet_default = "metal_dark"

    # This is somewhat outdated
    _dock_names = [
        "dockComponent",
        "dockConnectors",
        "dockDesign",
        "dockLog",
        "dockLibrary",
        "dockVariables",
    ]

    def __init__(self, design: QDesign = None):
        """Create a GUI bound to the provided ``design`` (or create one later).

        Args:
            design (QDesign, optional): The design to visualize and edit. You can
                also call ``set_design`` after constructing the GUI. When passed,
                the GUI will immediately populate docks and the canvas from this
                design. Defaults to None.

        Diagnostic switch (issues #1048 / #1109):
            Set ``QISKIT_METAL_DEBUG_INIT=1`` to trace each init step to
            stderr with explicit flushes. Useful for users seeing the GUI
            silently abort mid-init on Windows -- the last printed step
            identifies the failing call without needing a custom branch.
        """

        _trace_init("MetalGUI.__init__ entered")

        # Startup crash journal (issue #1048) -- FIRST, before any Qt
        # machinery is touched, so a native crash anywhere in the rest of
        # this constructor (QPA plugin init, widget construction,
        # restoreState, show) leaves the journal file behind and the next
        # launch self-heals. See ``startup_journal.py`` for why this is a
        # plain fsync'd file rather than the old QSettings cookie.
        from qiskit_metal._gui.startup_journal import (
            begin_startup,
            previous_startup_crashed,
        )

        if previous_startup_crashed():
            _trace_init("startup journal found -- clearing persisted UI state")
            logging.getLogger("metal").warning(
                "The previous MetalGUI launch did not complete startup "
                "(crashed or was killed). Clearing persisted window state "
                "and starting with the default layout."
            )
            # QSettings is QtCore-only; safe before QApplication exists.
            from PySide6.QtCore import QSettings

            QSettings("QiskitMetal", "MainWindow").clear()
        _trace_init("startup journal: begin")
        begin_startup()

        # Qt backend setup used to run at ``import qiskit_metal`` time;
        # it's now lazy, called the first time MetalGUI is instantiated.
        # Idempotent — second and later calls are no-ops.
        from qiskit_metal import setup_qt_backend

        _trace_init("setup_qt_backend()")
        setup_qt_backend()

        from .utility._handle_qt_messages import QtCore, _qt_message_handler

        _trace_init("qInstallMessageHandler")
        QtCore.qInstallMessageHandler(_qt_message_handler)

        _trace_init("kick_start_qApp()")
        self.qApp = kick_start_qApp()
        if not self.qApp:
            logging.error("Could not start Qt event loop using QApplication.")

        # Register the at-exit Qt teardown exactly once (issue #1048), no
        # matter how many MetalGUIs are built. Done lazily here so a pure
        # headless / ``qm.view`` user who never builds a MetalGUI never
        # registers it. ``unregister`` is a no-op the first time and keeps
        # this idempotent across repeated construction.
        atexit.unregister(_teardown_qt_widgets)
        atexit.register(_teardown_qt_widgets)

        _trace_init("super().__init__() -> QMainWindowBaseHandler")
        super().__init__()

        # use set_design
        self.design = None  # type: QDesign

        # UIs
        self.plot_win = None  # type: QMainWindowPlot
        self.elements_win = None  # type: ElementsWindow
        self.net_list_win = None  # type: NetListWindow
        _trace_init("ComponentWidget()")
        self.component_window = ComponentWidget(self, self.ui.dockComponent)
        _trace_init("PropertyTableWidget()")
        self.variables_window = PropertyTableWidget(self, gui=self)

        self.build_log_window = None

        # All widget construction happens before show(). Calling show()
        # mid-setup (as earlier code did) left the QMainWindow visible as
        # bare scaffolding while filesystem-scanning widgets (library,
        # netlist) dispatched events through partially-constructed docks;
        # on Windows 11 / Qt 6.11 that path could abort silently, leaving
        # only Qt's default object-inspector window briefly visible before
        # the kernel returned (issue #1048).
        _trace_init("_setup_component_widget")
        self._setup_component_widget()
        _trace_init("_setup_plot_widget")
        # Issue #1048 bisection toggle: the embedded matplotlib
        # ``FigureCanvasQTAgg`` is the heaviest QWidget in MetalGUI's tree
        # and a prime suspect for the Qt 6.11 + Intel Iris Xe + WDDM 3.2
        # crash at ``show()``. ``QISKIT_METAL_GUI_NO_PLOT=1`` skips the
        # canvas embed so reporters can isolate whether it's the trigger.
        # The GUI loses its main view -- this is a diagnostic-only flag.
        if os.environ.get("QISKIT_METAL_GUI_NO_PLOT"):
            self.logger.warning(
                "QISKIT_METAL_GUI_NO_PLOT set; skipping plot canvas embed."
            )
        else:
            self._setup_plot_widget()
        _trace_init("_setup_design_components_widget")
        self._setup_design_components_widget()
        _trace_init("_setup_pins_widget")
        self._setup_pins_widget()
        _trace_init("_setup_elements_widget")
        self._setup_elements_widget()
        _trace_init("_setup_variables_widget")
        self._setup_variables_widget()
        _trace_init("_setup_chip_widget")
        self._setup_chip_widget()
        _trace_init("_setup_view_control_widget")
        self._setup_view_control_widget()
        _trace_init("_ui_adjustments_final")
        self._ui_adjustments_final()
        _trace_init("_setup_library_widget")
        self._setup_library_widget()
        _trace_init("_setup_net_list_widget")
        self._setup_net_list_widget()

        # Show and raise — single call after all docks are wired.
        _trace_init("main_window.show()")
        self.main_window.show()

        # Issue #1048 / PR #1129: the crash-cookie set in
        # restore_window_settings() deliberately stays set across the
        # show() call above -- that's the actual crash site the cookie
        # protects against (a restored-but-inconsistent widget tree can
        # pass restoreState() cleanly and only fault when Qt paints it).
        # Only mark startup complete once show() has returned without
        # crashing.
        _trace_init("mark_startup_complete()")
        self.main_window.mark_startup_complete()

        # self.qApp.processEvents(QEventLoop.AllEvents, 1)
        # - don't think I need this here, it doesn't help to show and raise
        # - need to call from different thread.
        # Parented to the main window: _raise touches it, so the deferred
        # call must die with it (short-lived GUIs in tests/scripts).
        single_shot(self.main_window, 150, self._raise)

        if design:
            _trace_init("set_design(design)")
            self.set_design(design)
        else:
            self._set_enabled_design_widgets(False)

        _trace_init("MetalGUI.__init__ complete")

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
                    widget: "QWidget" = getattr(parent, widgetname)
                    if widget:
                        widget.setEnabled(enabled)
                else:
                    self.logger.error(f"GUI issue: wrong name: {widgetname}")

        widgets = [
            "actionSave",
            "action_full_refresh",
            "actionRebuild",
            "actionDelete_All",
            "dockComponent",
            "dockLibrary",
            "dockDesign",
            "dockConnectors",
        ]
        setEnabled(self.ui, widgets)

        widgets = ["component_window", "elements_win", "net_list_win"]
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

        # ``plot_win`` is None when the QISKIT_METAL_GUI_NO_PLOT bisection
        # toggle is set (issue #1048). Tolerate that gracefully so the GUI
        # still builds; the user just won't see the chip canvas.
        if self.plot_win is not None:
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

        # The chip model is constructed before any design exists, so its
        # first load found nothing. Reload now rather than leaving the panel
        # blank until the refresh timer next fires. Guarded because
        # ``set_design`` can be called on a partially built GUI.
        if getattr(self, "chips_model", None) is not None:
            self.chips_model.load()
            if getattr(self, "chips_window", None) is not None:
                self.chips_window.expandAll()
                self.chips_window.autoresize_columns()
        if getattr(self, "layers_window", None) is not None:
            self.layers_window.refresh()

        # Refresh
        self.refresh()

    def _setup_logger(self):
        """Setup the logger."""
        super()._setup_logger()

        logger = logging.getLogger("metal")
        self._log_handler_design = self.create_log_handler("metal", logger)

    def refresh_design(self):
        """Refresh design properties associated with the GUI."""
        self.update_design_name()

    def update_design_name(self):
        """Update the design name."""
        if self.design:
            design_name = self.design.get_design_name()
            self.main_window.setWindowTitle(
                self.config.main_window.title + f" — {design_name}"
            )

    def _ui_adjustments(self):
        """Any touchups to the loaded ui that need be done soon."""
        # QTextEditLogger
        self.ui.log_text.img_path = Path(self.path_imgs)
        self.ui.log_text.dock_window = self.ui.dockLog

        # Add a second label to the status bar
        status_bar = self.main_window.statusBar()

        # ``addPermanentWidget``, not ``addWidget``: the window sets a standing
        # status message ("Qiskit Metal: Quantum Creator"), and Qt hides every
        # *normal* status-bar widget for as long as a message is displayed.
        # Added as normal widgets these labels are constructed, updated, and
        # never seen. Permanent widgets are exempt, and sit to the right of
        # the message rather than fighting it for the same space.
        self.statusbar_label = QLabel(status_bar)
        self.statusbar_label.setText("")
        status_bar.addPermanentWidget(self.statusbar_label)

        # Second label, for what is selected and what you can do with it.
        # Separate from the coordinate readout above because that one updates
        # on every mouse-move; sharing one label would erase the hint the
        # moment the pointer moved.
        self.statusbar_selection = QLabel(status_bar)
        self.statusbar_selection.setText("")
        self.statusbar_selection.setStyleSheet(SELECTION_HINT_STYLE)
        status_bar.addPermanentWidget(self.statusbar_selection)

        # Docks
        # Left handside
        self.main_window.splitDockWidget(
            self.ui.dockDesign, self.ui.dockComponent, Qt.Vertical
        )
        self.main_window.tabifyDockWidget(self.ui.dockDesign, self.ui.dockLibrary)
        self.main_window.tabifyDockWidget(self.ui.dockLibrary, self.ui.dockConnectors)
        self.main_window.tabifyDockWidget(self.ui.dockConnectors, self.ui.dockVariables)
        # Default to the QComponent Library tab on launch — that's the
        # natural starting point for a new design (browse the catalog and
        # drop a component). The QComponents/edit-component tab
        # (``dockDesign``) is only useful once components exist; raising
        # it first showed a near-empty pane on first open.
        self.ui.dockLibrary.raise_()
        # Re-sweep the dock tab bars (scroll buttons) whenever a dock is
        # re-tabbed; the first sweep runs in showEvent.
        for dock in (
            self.ui.dockDesign,
            self.ui.dockComponent,
            self.ui.dockLibrary,
            self.ui.dockConnectors,
            self.ui.dockVariables,
        ):
            dock.dockLocationChanged.connect(
                self.main_window._schedule_dock_tab_scrolling
            )
        self.main_window.tabifiedDockWidgetActivated.connect(
            self.main_window._schedule_dock_tab_scrolling
        )
        self.main_window.resizeDocks([self.ui.dockDesign], [350], Qt.Horizontal)

        # These four are tabified together, so the tab bar already names each
        # one -- the per-dock title bar underneath repeated that name and cost
        # 17px of height apiece. Replace it with an empty widget. Undocking
        # still works by dragging the tab out; show/hide is on the left
        # toolbar and the Docks toggle.
        for _dock in (
            self.ui.dockDesign,
            self.ui.dockLibrary,
            self.ui.dockConnectors,
            self.ui.dockVariables,
        ):
            _dock.setTitleBarWidget(QWidget(_dock))

        # Log
        self.ui.dockLog.parent().resizeDocks([self.ui.dockLog], [120], Qt.Vertical)

        # Theme toggle. The stylesheets were only reachable from a
        # View > Color theme submenu; switching light/dark is frequent enough
        # to deserve one click. Created here and attached to ``self.ui`` so
        # the toolbar spec can resolve it by name like any .ui action.
        self.ui.actionThemeToggle = QAction("Theme", self.main_window)
        # Name it like a .ui action: Qt's saveState() warns about unnamed
        # objects, and the toolbar/menu reachability audits key off
        # objectName -- an unnamed action reads as "missing from the UI"
        # (see DEMOTED_ACTIONS in toolbar_layout.py for why that matters).
        self.ui.actionThemeToggle.setObjectName("actionThemeToggle")
        self.ui.actionThemeToggle.setToolTip("Switch between the dark and light theme")
        self.ui.actionThemeToggle.setStatusTip(self.ui.actionThemeToggle.toolTip())
        self.ui.actionThemeToggle.triggered.connect(self.toggle_theme)

        self._setup_view_switch_actions()

        # Compose the top toolbars from the declarative spec in
        # ``toolbar_layout``: ordering by how often each control is actually
        # used, one shared icon size, and a check that no action is dropped
        # without a recorded decision. Kept out of the .ui because
        # ``main_window_ui.py`` is pyside6-uic output.
        apply_toolbar_layout(self)

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

        # (dock, icon, caption, tooltip). The caption is deliberately one
        # short word -- it sits under the icon on a narrow vertical toolbar.
        # Without it these buttons were icon-only, and because each QAction
        # was built with empty text every one of them inherited the
        # toolbar's own "View Toolbar" tooltip on hover, which said nothing
        # about what the button does.
        DOCKS = [
            (
                self.ui.dockLibrary,
                r":/design",
                "Lib",
                "QComponent library — browse and place new components",
            ),
            (
                self.ui.dockDesign,
                r":/component",
                "Edit",
                "QComponents in this design — select one to edit its options",
            ),
            (None, "-----", None, None),
            (
                self.ui.dockVariables,
                r":/variables",
                "Vars",
                "Design variables — named values reusable in component options",
            ),
            (
                self.ui.dockConnectors,
                r":/connectors",
                "Pins",
                "Pins — connection points exposed by each component",
            ),
            (
                self.ui.dockLog,
                r":/log",
                "Log",
                "Log messages (hidden by default) — click again to close",
            ),
            (None, "-----", None, None),
        ]

        # Show the caption under each icon; icon-only left users guessing.
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.setIconSize(QSize(TOOLBAR_ICON_PX, TOOLBAR_ICON_PX))

        for dock, iconName, caption, tooltip in DOCKS:
            if iconName == "-----":
                toolbar.insertSeparator(toolbarInsertBefore)
                continue
            self._add_dock_toolbar_action(dock, iconName, caption, tooltip, toggle=True)

        # Lets mark_dock_has_error() reach the *real* status bar. dockLog's
        # own parent QMainWindow is plot_win (a sub-window it was moved
        # into), whose statusBar() is explicitly hidden -- self.main_window
        # is the actual outer window whose status bar carries the hover/
        # selection-hint label.
        self.ui.dockLog._status_bar = self.main_window.statusBar()

        # Errors logged while the (hidden-by-default) log dock isn't on
        # screen are otherwise silent -- clear the badge the moment the
        # dock actually becomes visible, regardless of how (toolbar click,
        # View menu, programmatically), rather than duplicating that logic
        # into every path that can show it.
        self.ui.dockLog.visibilityChanged.connect(
            lambda visible: clear_dock_error_badge(self.ui.dockLog) if visible else None
        )

        # The two actions that come from the .ui: give the toggle a tooltip
        # that says what it does rather than repeating its object name.
        self.ui.actionToggleDocks.setText("Dock")
        self.ui.actionToggleDocks.setToolTip("Show or hide all side panels at once")
        self.ui.actionToggleDocks.setStatusTip(self.ui.actionToggleDocks.toolTip())
        self.ui.actionScreenshot.setText("Snap")
        # "Web Help" was long enough to widen the toolbar; kept on it
        # (unlike Build History / Delete-all) rather than demoted, so
        # shortened to match the other one-word toolbar labels.
        self.ui.actionWebHelp.setText("Docs")

        # Ctrl+D (from the .ui) is easy to miss; "R" is the one-key
        # convention every drawing tool uses for rebuild/refresh, and
        # matches the plot toolbar's own single-letter shortcuts (A, L)
        # which already coexist safely with text-entry widgets elsewhere
        # in the window via WindowShortcut context. Added, not replacing
        # Ctrl+D, so existing muscle memory keeps working too.
        self.ui.actionRebuild.setShortcuts(
            [self.ui.actionRebuild.shortcut(), QKeySequence("R")]
        )

    def _setup_view_switch_actions(self):
        """Move the Main View / QGeometry / Net List switch into the toolbar.

        Those three lived in a tab strip above the canvas, costing a full
        32px row to show three words. As an exclusive action group on the top
        toolbar they cost no extra height and sit with the other view
        controls.

        The tab widget stays -- it holds the pages -- but its tab bar is
        hidden. ``currentChanged`` keeps the buttons in sync, so anything
        that switches pages in code (``_set_element_tab``, for instance)
        still leaves the right button checked.
        """
        tab_widget = self.ui.tabWidget
        group = QActionGroup(self.main_window)
        group.setExclusive(True)

        self._view_switch_actions = []
        for index in range(tab_widget.count()):
            action = QAction(tab_widget.tabText(index), self.main_window)
            action.setCheckable(True)
            action.setChecked(index == tab_widget.currentIndex())
            action.setToolTip(f"Show the {tab_widget.tabText(index)} panel")
            action.setStatusTip(action.toolTip())
            action.triggered.connect(
                lambda _checked, i=index: tab_widget.setCurrentIndex(i)
            )
            action.setObjectName(f"actionViewTab{index}")
            group.addAction(action)
            self._view_switch_actions.append(action)
            setattr(self.ui, f"actionViewTab{index}", action)

        def _sync(current):
            """Keep the buttons matching the page actually shown."""
            for i, act in enumerate(self._view_switch_actions):
                act.setChecked(i == current)

        tab_widget.currentChanged.connect(_sync)
        tab_widget.tabBar().hide()

    def _add_dock_toolbar_action(
        self, dock, icon_name: str, caption: str, tooltip: str, toggle: bool = False
    ):
        """Add one dock-raising button to the left toolbar.

        Split out of ``_add_additional_qactions_tool_bar_view`` so docks
        created later in startup -- which that method cannot see, since it
        runs inside ``_ui_adjustments`` during ``super().__init__()`` -- can
        get the same treatment.

        Args:
            dock (QDockWidget): Dock the button raises.
            icon_name (str): Qt resource path for the icon.
            caption (str): Short label shown under the icon. Keep it to about
                four characters: on a vertical toolbar the caption sets the
                bar's width.
            tooltip (str): Description of the panel. Must be set explicitly --
                an action with empty text inherits the toolbar's own tooltip,
                which is how every one of these once read "View Toolbar".
            toggle (bool): If True, clicking the button hides the dock when
                it is the one currently on screen, instead of just
                re-raising it; clicking a tabified sibling still switches to
                it as before. See ``doToggleDockWidget``'s docstring for how
                that distinction is made.
        """
        toolbar = self.ui.toolBarView
        toolbar_insert_before = self.ui.actionToggleDocks

        icon = QIcon()
        icon.addPixmap(QPixmap(icon_name), QIcon.Normal, QIcon.Off)

        # Function call & monkey patch class instance ala Monkey Patch
        show_fn = doToggleDockWidget if toggle else doShowHighlighWidget
        dock.doShow = show_fn.__get__(dock, type(dock))

        action = QAction(caption, dock, triggered=dock.doShow)
        action.setIcon(icon)
        action.setToolTip(tooltip)
        action.setStatusTip(tooltip)
        dock.actionShow = action  # save action
        dock._icon_normal = icon  # restore point for mark_log_error's badge

        toolbar.insertAction(toolbar_insert_before, action)

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

    def _setup_chip_widget(self):
        """Create the chip-stack editor dock.

        Components, variables and pins each had a dock; the chip stack --
        die size, material, layer bounds -- had none, so changing it meant
        dropping to a notebook. ``design.chips`` is a nested ``Dict`` of the
        same shape the component-options tree already edits, so this reuses
        that model rather than introducing another editor.

        Built in code rather than the .ui because ``main_window_ui.py`` is
        pyside6-uic output; it is tabified alongside the other left docks.
        """
        self.ui.dockChips = QDockWidget("Chip", self.main_window)
        self.ui.dockChips.setObjectName("dockChips")

        view = QTreeView_Base(self.ui.dockChips)
        view.setAlternatingRowColors(True)
        self.chips_model = QTreeModel_Chips(self.ui.dockChips, gui=self, view=view)
        view.setModel(self.chips_model)
        self.ui.dockChips.setWidget(view)
        self.chips_window = view

        # Chips is a shallow tree (one or two chips, a handful of
        # properties each) -- collapsed-by-default just adds a click for
        # something you almost always want to see immediately, unlike the
        # component/pin trees where collapsed is the useful default.
        view.expandAll()
        view.autoresize_columns()

        self.main_window.tabifyDockWidget(self.ui.dockVariables, self.ui.dockChips)
        # Tabified, so the tab bar names it; a title bar would repeat that.
        self.ui.dockChips.setTitleBarWidget(QWidget(self.ui.dockChips))

        # Give it a left-rail button like the other docks. Done here rather
        # than in the DOCKS table of _add_additional_qactions_tool_bar_view:
        # that runs inside _ui_adjustments during super().__init__(), well
        # before this dock exists.
        self._add_dock_toolbar_action(
            self.ui.dockChips,
            r":/variables",
            "Chip",
            "Chip stack — die size, material and layer bounds",
            toggle=True,
        )

    def _setup_view_control_widget(self):
        """Create the layer-visibility dock.

        ``QMplRenderer`` already tracked ``hidden_layers`` and filtered on it;
        nothing in the GUI could reach that, and there was no way to see which
        layers a design contains.
        """
        self.ui.dockLayers = QDockWidget("Layers", self.main_window)
        self.ui.dockLayers.setObjectName("dockLayers")

        self.layers_window = LayerVisibilityWidget(self, self.ui.dockLayers)
        self.ui.dockLayers.setWidget(self.layers_window)

        self.main_window.tabifyDockWidget(self.ui.dockChips, self.ui.dockLayers)
        self.ui.dockLayers.setTitleBarWidget(QWidget(self.ui.dockLayers))

        self._add_dock_toolbar_action(
            self.ui.dockLayers,
            r":/design",
            "Layer",
            "Show or hide layers, like a GDS editor's layer palette",
            toggle=True,
        )
        # hookup to delete action
        self.ui.btn_comp_del.clicked.connect(
            self.ui.tableComponents.delete_selected_rows
        )
        self.ui.btn_comp_rename.clicked.connect(self.ui.tableComponents.rename_row)
        self.ui.btn_comp_zoom.clicked.connect(self.btn_comp_zoom_fx)

        # btn_comp_rename has no icon in the .ui, unlike its two neighbours,
        # and no explicit tool-button style -- with the default IconOnly
        # style and nothing to show as an icon, it rendered as a blank,
        # unlabeled button. TextOnly makes its "Rename" text actually
        # visible; the other two keep their icon-only default.
        self.ui.btn_comp_rename.setToolButtonStyle(Qt.ToolButtonTextOnly)
        rename_tip = "Rename the selected component"
        self.ui.btn_comp_rename.setToolTip(rename_tip)
        self.ui.btn_comp_rename.setStatusTip(rename_tip)

        filter_tip = "Filter the component list by name, class, or module"
        self.ui.filter_text_design.setToolTip(filter_tip)
        self.ui.filter_text_design.setStatusTip(filter_tip)

    def _setup_plot_widget(self):
        """Create main Window Widget Plot."""
        self.plot_win = QMainWindowPlot(self, self.main_window)

        # Add to the tabbed main view
        self.ui.mainViewTab.layout().addWidget(self.plot_win)

        # add highlight function ala Monkey Patch
        obj = self.ui.mainViewTab
        obj.doShow = doShowHighlighWidget.__get__(obj, type(obj))

        # Move the dock. Start hidden: the log competes with the canvas for
        # vertical space and most sessions never need it. The View toolbar
        # button and the Docks toggle both bring it back, and messages
        # logged while it is hidden are still there when it is opened.
        self._move_dock_to_new_parent(self.ui.dockLog, self.plot_win, visible=False)
        self.ui.dockLog.parent().resizeDocks([self.ui.dockLog], [120], Qt.Vertical)

    def _move_dock_to_new_parent(
        self,
        dock: QDockWidget,
        new_parent: QMainWindow,
        dock_location=Qt.BottomDockWidgetArea,
        visible: bool = True,
    ):
        """The the doc to a different parent window.

        Args:
            dock (QDockWidget): Dock to move
            new_parent (QMainWindow): New parent window
            dock_location (Qt dock location): Location of the dock.
                Defaults to Qt.BottomDockWidgetArea.
            visible (bool): Whether the dock is shown after the move.
                Reparenting happens after ``restore_window_settings``, so
                whatever is set here is the dock's effective startup state.
                Defaults to True.
        """
        dock.setParent(new_parent)
        new_parent.addDockWidget(dock_location, dock)
        dock.setFloating(False)
        dock.setVisible(visible)
        dock.setMaximumHeight(99999)

    def _setup_elements_widget(self):
        """Create main Window Elements Widget."""
        self.elements_win = ElementsWindow(self, self.main_window)

        # Component filter
        self.ui.tabQGeometry.sort_model = QSortFilterProxyModel()
        self.ui.tabQGeometry.sort_model.setSourceModel(self.elements_win.model)
        self.ui.tabQGeometry.sort_model.setFilterKeyColumn(1)

        self.elements_win.ui.tableElements.setModel(self.ui.tabQGeometry.sort_model)
        self.elements_win.ui.tableElements.setSortingEnabled(True)

        # Add a text changed event to the QGeometry/Component/Layer text boxes
        self.elements_win.ui.lineEdit.textChanged.connect(
            self.elements_lineEdit_onChanged
        )
        self.elements_win.ui.lineEdit_2.textChanged.connect(
            self.elements_lineEdit_2_onChanged
        )

        # Add to the tabbed main view
        self.ui.tabQGeometry.layout().addWidget(self.elements_win)

    def elements_lineEdit_onChanged(self, text):
        """Text changed event for QGeometry/Component text box
        Args:
            text: Text typed in the filter box.
        """
        self.ui.tabQGeometry.sort_model.setFilterKeyColumn(1)
        self.ui.tabQGeometry.sort_model.setFilterWildcard(text)

    def elements_lineEdit_2_onChanged(self, text):
        """Text changed event for QGeometry/Layer text box
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

        self.net_list_win.ui.tableElements.setModel(self.ui.tabNetList.sort_model)
        self.net_list_win.ui.tableElements.setSortingEnabled(True)

        # Add to the tabbed main view
        self.ui.tabNetList.layout().addWidget(self.net_list_win)

    def _setup_design_components_widget(self):
        """Design components.

        Table model that shows the summary of the components of a design
        in a table with their names, classes, and modules
        """
        model = QTableModel_AllComponents(
            self, logger=self.logger, tableView=self.ui.tableComponents
        )
        # Add Sort/Filter logic to the components table
        self.ui.proxyModel = QSortFilterProxyModel()
        self.ui.proxyModel.setSourceModel(model)

        # search all columns
        self.ui.proxyModel.setFilterKeyColumn(-1)
        self.ui.tableComponents.setSortingEnabled(True)
        self.ui.tableComponents.setModel(self.ui.proxyModel)

        # Add a text changed event to the filter text box
        self.ui.filter_text_design.textChanged.connect(
            self.filter_text_design_onChanged
        )

    def filter_text_design_onChanged(self, text):
        """Text changed event for filter_text_design
        Args:
            text: Text typed in the filter box.
        """
        self.ui.proxyModel.setFilterWildcard(text)

    def _setup_pins_widget(self):
        """Pins dock: every (component, pin) in the design, flattened into
        one table. ``tableConnectors``/``text_filter_connectors`` exist in
        the .ui but nothing ever set a model on the view or connected the
        filter box -- the dock has shown as permanently empty since it was
        added, on every design, not just ones with unusual pins.
        """
        model = QTableModel_Pins(
            self, logger=self.logger, tableView=self.ui.tableConnectors
        )
        self.ui.pinsProxyModel = QSortFilterProxyModel()
        self.ui.pinsProxyModel.setSourceModel(model)
        self.ui.pinsProxyModel.setFilterKeyColumn(-1)  # search all columns

        self.ui.tableConnectors.setSortingEnabled(True)
        self.ui.tableConnectors.setModel(self.ui.pinsProxyModel)

        self.ui.text_filter_connectors.textChanged.connect(
            self.ui.pinsProxyModel.setFilterWildcard
        )

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
                self, full_path, self.main_window
            )
        except Exception as e:
            self.logger.error(
                f"Unable to open param entry window due to Exception: {e} "
            )

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
        qlibrary_abs_path = init_qlibrary_abs_path.split("__init__.py")[0]
        self.QLIBRARY_ROOT = qlibrary_abs_path
        self.QLIBRARY_FOLDERNAME = qlibrary.__name__

        # create model for Qlibrary directory
        dock.library_model = QFileSystemLibraryModel(self.path_imgs)

        dock.library_model.setRootPath(self.QLIBRARY_ROOT)
        # Only show Python source files in the Library pane. Stray
        # demo notebooks, ``__pycache__`` entries, and other artefacts
        # that may live under ``qlibrary/`` (e.g. a user dropping a
        # ``.ipynb`` next to a ``.py``) would otherwise appear in the
        # tree as un-clickable "components". ``setNameFilters`` + the
        # default ``setNameFilterDisables(False)`` hides non-matches
        # entirely rather than greying them out.
        dock.library_model.setNameFilters(["*.py"])
        dock.library_model.setNameFilterDisables(False)

        # QSortFilterProxyModel
        # QSortFilterProxyModel: sorting items, filtering out items, or both.
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
                dock.library_model.index(dock.library_model.rootPath())
            )
        )

        # try empty one if no work
        view.setItemDelegate(LibraryDelegate(self.main_window))
        view.itemDelegate().tool_tip_signal.connect(view.setToolTip)

        view.qlibrary_filepath_signal.connect(
            self._create_new_component_object_from_qlibrary
        )

        # https://stackoverflow.com/questions/16759088/what-is-the-viewport-of-a-tree-widget
        view.viewport().setAttribute(Qt.WA_Hover, True)
        view.viewport().setMouseTracking(True)

        view.resizeColumnToContents(0)

        libraryRootPath = Path(dock.library_model.rootPath()) / "qubits"
        stringLibraryRootPath = str(libraryRootPath)
        view.expand(
            dock.proxy_library_model.mapFromSource(
                dock.library_model.index(stringLibraryRootPath)
            )
        )

        # Add a text changed event to the filter text box
        self.ui.dockLibrary_filter.textChanged.connect(
            self.dockLibrary_filter_onChanged
        )

    def dockLibrary_filter_onChanged(self, text):
        """Text changed event for filter_text_design
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
                dock.library_model.index(dock.library_model.rootPath())
            )
        )

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
        self.qApp.processEvents()  # Process all events, so that if we take screenshot next it won't be partially updated

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
    def axes(self) -> list["matplotlib.plt.Axes"]:
        """Returns the axes."""
        return self.plot_win.canvas.axes

    @property
    def figure(self):
        """Return axis to the figure of the canvas."""
        return self.plot_win.canvas.figure

    @property
    def canvas(self) -> "PlotCanvas":
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

        # Keep the selection across the rebuild. Without this, the
        # workflow "click a component, arrow-key it around, press R,
        # keep arrowing" broke at the R: the replot dropped the
        # highlight and the widget refresh dropped canvas focus, so the
        # user had to re-click the component to continue. If the
        # selected component no longer exists (deleted then rebuilt),
        # clear the stale selection instead.
        name = self.selected_component
        if name is not None:
            if self.design is not None and name in self.design.components:
                self.highlight_components([name], show_pins=False)
                self._show_selection_hint(name)
                self._refocus_canvas()
            else:
                self.clear_selection()

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
        self.ui.tableConnectors.model().sourceModel().refresh()

        # Layer list -- unlike the chip/component trees this widget has no
        # polling timer of its own, so without this call it stays empty
        # (or stale) after the first build until set_design() is called
        # again, which usually never happens in a normal session.
        if getattr(self, "layers_window", None) is not None:
            self.layers_window.refresh()

        # Redraw plots
        self.refresh_plot()

    def refresh_plot(self):
        """Redraw only the plot window contents."""
        if self.plot_win is not None:
            self.plot_win.replot()

    def autoscale(self, include_chip: bool = False):
        """Frame the design in the plot window.

        Args:
            include_chip (bool): Frame the whole chip rather than just the
                components. Defaults to False -- a default 9x6mm die around a
                sub-millimetre component leaves it unreadably small, and the
                tutorials assume the chip is ignored.
        """
        self.plot_win.auto_scale(include_chip=include_chip)

    #########################################################
    # COMPONENT FUNCTIONS
    def edit_component(self, name: str):
        """Make the named component active in the component editor widget.

        Args:
            name (str): Component name to load. Must exist in ``design.components``.

        Note:
            This does not rebuild geometry; use ``rebuild()`` if options are changed.
        """
        self._selected_component = name
        self._show_selection_hint(name)
        if self.component_window:
            self.component_window.set_component(name)
        table = getattr(self.ui, "tableComponents", None)
        if table is not None:
            # Keeps the QComponents list dock's row selection in sync with
            # whatever's loaded in the editor, regardless of which of the
            # two triggered this (canvas click, list click, ...). A no-op
            # when called from the list's own click handler, since the row
            # is already selected there.
            table.select_component(name)

    def _show_selection_hint(self, name):
        """Say what is selected and that the arrow keys will move it.

        Nudging is otherwise undiscoverable: nothing on screen suggests the
        arrow keys do anything. Components positioned by their pins say so
        instead of advertising a move that would be refused.

        Args:
            name (str): Selected component, or None to clear the hint.
        """
        label = getattr(self, "statusbar_selection", None)
        if label is None:
            return

        if not name:
            label.setText("")
            return

        movable = False
        if self.design is not None and name in self.design.components:
            options = self.design.components[name].options
            movable = "pos_x" in options and "pos_y" in options

        if movable:
            label.setText(
                f"{name} selected  ·  arrow keys move it (Shift = ×10, Alt = ×0.1)"
            )
        else:
            label.setText(f"{name} selected  ·  positioned by its pins")

    def clear_selection(self):
        """Forget the selected component and clear its hint."""
        self._selected_component = None
        self._show_selection_hint(None)

    @property
    def selected_component(self):
        """Name of the component last opened in the editor, or None.

        Set by :meth:`edit_component`, which the canvas calls on click, so
        clicking a component on the canvas is enough to make it the nudge
        target.
        """
        return getattr(self, "_selected_component", None)

    def _refocus_canvas(self):
        """Give keyboard focus back to the plot canvas after a nudge/rotate.

        ``self.refresh()`` (called after every nudge/rotate so the edit
        panel shows the new value) repopulates the side docks, and one of
        them -- observed: the variables table's ``RightClickView`` --
        ends up with keyboard focus. The next arrow key then navigates
        that table instead of moving the component, which is why "arrows
        work exactly once" was reported. Same re-assertion
        ``_on_pick_release`` does after a click-select.
        """
        canvas = getattr(self, "canvas", None)
        if canvas is not None:
            canvas.setFocus(Qt.OtherFocusReason)

    def nudge_component(self, name: str, dx_mm: float, dy_mm: float) -> bool:
        """Move a component by a displacement in millimetres.

        Positions are unit-bearing strings, so the displacement is converted
        into whatever unit each option already uses -- a design authored in
        microns stays in microns rather than being silently rewritten in mm.

        Only components exposing ``pos_x``/``pos_y`` can be moved. Routes are
        positioned by their pins, so nudging one is meaningless and is
        refused rather than half-applied.

        Args:
            name (str): Component to move.
            dx_mm (float): Displacement along x, in millimetres.
            dy_mm (float): Displacement along y, in millimetres.

        Returns:
            bool: True if the component moved.
        """
        if self.design is None or name not in self.design.components:
            return False

        component = self.design.components[name]
        options = component.options
        if "pos_x" not in options or "pos_y" not in options:
            self.logger.info(
                f"{name} has no pos_x/pos_y to nudge — it is positioned by "
                "its pins or is fixed."
            )
            return False

        new_x = offset_length(options["pos_x"], dx_mm, self.design.parse_value)
        new_y = offset_length(options["pos_y"], dy_mm, self.design.parse_value)
        if new_x is None or new_y is None:
            self.logger.warning(
                f"Could not nudge {name}: pos_x/pos_y are not simple lengths "
                f"({options['pos_x']!r}, {options['pos_y']!r})."
            )
            return False

        options["pos_x"] = new_x
        options["pos_y"] = new_y

        component.rebuild()
        self.refresh()
        # Re-assert the highlight: the rebuild cleared the annotations, and
        # losing the outline mid-nudge makes it unclear what is moving.
        self.highlight_components([name], show_pins=False)
        self._refocus_canvas()
        self.logger.info(f"Nudged {name} to ({new_x}, {new_y})")
        return True

    def rotate_component(self, name: str, delta_deg: float) -> bool:
        """Rotate a component in place by a change in orientation, in degrees.

        Only components exposing ``orientation`` can be rotated. Unlike
        ``pos_x``/``pos_y``, ``orientation`` is stored as a bare number (no
        unit suffix), so the arithmetic here doesn't need offset_length's
        unit-preserving parsing.

        Args:
            name (str): Component to rotate.
            delta_deg (float): Change in orientation, in degrees. Positive
                is counter-clockwise, matching the option's own convention.

        Returns:
            bool: True if the component rotated.
        """
        if self.design is None or name not in self.design.components:
            return False

        component = self.design.components[name]
        options = component.options
        if "orientation" not in options:
            self.logger.info(f"{name} has no orientation to rotate — it is fixed.")
            return False

        try:
            current_deg = float(options["orientation"])
        except (TypeError, ValueError):
            self.logger.warning(
                f"Could not rotate {name}: orientation is not a plain number "
                f"({options['orientation']!r})."
            )
            return False

        new_deg = (current_deg + delta_deg) % 360.0
        # Whole-degree values print as e.g. "90", not "90.0" -- matches how
        # a hand-authored design usually writes this option.
        options["orientation"] = (
            str(int(new_deg)) if new_deg.is_integer() else str(new_deg)
        )

        component.rebuild()
        self.refresh()
        self.highlight_components([name], show_pins=False)
        self._refocus_canvas()
        self.logger.info(f"Rotated {name} to {options['orientation']}°")
        return True

    def rotate_selected(self, delta_deg: float) -> bool:
        """Rotate the currently selected component.

        Args:
            delta_deg (float): Change in orientation, in degrees.

        Returns:
            bool: True if a component rotated.
        """
        name = self.selected_component
        if name is None:
            self.logger.info("Nothing selected — click a component first.")
            return False
        return self.rotate_component(name, delta_deg)

    def nudge_selected(self, dx_mm: float, dy_mm: float) -> bool:
        """Nudge the currently selected component.

        Args:
            dx_mm (float): Displacement along x, in millimetres.
            dy_mm (float): Displacement along y, in millimetres.

        Returns:
            bool: True if a component moved.
        """
        name = self.selected_component
        if name is None:
            self.logger.info("Nothing selected — click a component first.")
            return False
        return self.nudge_component(name, dx_mm, dy_mm)

    def highlight_components(self, component_names: list[str], show_pins: bool = True):
        """Visually highlight components in the plot canvas.

        Args:
            component_names (List[str]): Names to highlight; others remain unhighlighted.
            show_pins (bool): Also draw pin arrows and pin names.
                Defaults to True.
        """
        self.canvas.highlight_components(component_names, show_pins=show_pins)

    def highlight_all_components(self, show_pins: bool = True):
        """Label every component in the design on the canvas.

        Draws each component's bounding box and name, and by default its
        pins. Useful for orienting yourself on a design someone else built,
        or for a labelled screenshot.

        Bound to the "Label all" button on the plot toolbar (shortcut ``L``);
        ``Shift+L`` labels components only, without pins.

        Args:
            show_pins (bool): Also draw pin arrows and pin names. Turn off on
                dense chips, where per-pin labels swamp the component names.
                Defaults to True.

        Returns:
            int: Number of components labelled.
        """
        count = self.canvas.highlight_all_components(show_pins=show_pins)
        self.logger.info(
            f"Labelled {count} component(s)"
            f"{' with pins' if show_pins else ''}. "
            "Any replot or rebuild clears the labels."
        )
        return count

    #: Themes the toolbar toggle flips between. ``load_stylesheet`` also
    #: accepts "qdarkstyle", "default" and an arbitrary .qss path; those stay
    #: on the View > Color theme menu, which remains the full picker.
    #:
    #: THEME_LIGHT is deliberately "metal_light_gray", not "default":
    #: "default" means *no* stylesheet, which follows the OS/Qt native
    #: theme -- on a system with OS-level dark mode that renders dark too,
    #: so toggling into it from metal_dark looked like nothing happened.
    #: metal_light_gray is an actual designed light theme.
    THEME_DARK = "metal_dark"
    THEME_LIGHT = "metal_light_gray"

    def toggle_theme(self, _=None):
        """Flip between the dark and light stylesheet.

        Reads the currently applied stylesheet rather than tracking a
        separate flag, so the button stays correct when the theme is changed
        from the View menu instead.

        Returns:
            str: The stylesheet now applied.
        """
        current = getattr(self, "_stylesheet", self.THEME_DARK)
        new = self.THEME_LIGHT if current == self.THEME_DARK else self.THEME_DARK
        self.load_stylesheet(new)
        self.logger.info(f"Theme: {new}")
        return new

    def clear_highlight(self):
        """Remove any component labels/highlights from the canvas.

        ``clear_annotation`` detaches the artists but does not redraw --
        ``highlight_components`` refreshes at the end of its own run, so the
        clear path has to do it too or the labels stay on screen until
        something else happens to trigger a draw.
        """
        self.canvas.clear_annotation()
        self.canvas.refresh()

    def zoom_on_components(self, components: list[str]):
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
        self.build_log_window = BuildHistoryScrollArea(self.design.build_logs.data())
        self.build_log_window.show()

    def save_file(self):
        """Save file. Called on exit.

        Raises:
            NotImplementedError: Function not written
        """
        print("TODO: Save file - not yet implemented here")
        raise NotImplementedError()
