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

"""Table model behind the Pins dock (``tableConnectors`` in the .ui).

Pins live per-component (``component.pins``), there is no design-wide
registry, so this walks every component each refresh and flattens their pins
into rows. Net connectivity itself already has a dedicated view (the Net
List tab, backed by ``design.net_info``); this table's job is just "what
pins exist and are they wired to anything," which is why "Net ID" is enough
context here -- 0 means unconnected.
"""

from PySide6 import QtCore
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QFont

from qiskit_metal._gui.utility._toolbox_qt import qt_alive

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QTableView


class QTableModel_Pins(QAbstractTableModel):
    """Flat (component, pin) list across the whole design.

    Rebuilt on the same polling cadence as ``QTableModel_AllComponents`` --
    pins appear/disappear only when components are built, deleted, or
    renamed, so a change in the total pin count is a cheap, sufficient
    trigger to reload.
    """

    __timer_interval = 500  # ms

    def __init__(self, gui, logger, parent=None, tableView: "QTableView" = None):
        """
        Args:
            gui (MetalGUI): The GUI.
            logger (logger): The logger.
            parent (QWidget): Parent widget. Defaults to None.
            tableView (QTableView): The table view, used to refresh headers/
                columns after a reset. Defaults to None.
        """
        super().__init__(parent=parent)
        self.logger = logger
        self.gui = gui
        self._tableView = tableView
        self.columns = ["Component", "Pin", "Net ID", "Chip"]
        self._rows = []

        self._create_timer()
        self._reload_rows()

    @property
    def design(self):
        """Returns the design."""
        return self.gui.design

    def _create_timer(self):
        """Poll for pin-count changes, like QTableModel_AllComponents does."""
        self._timer = QtCore.QTimer(self)
        self._timer.start(self.__timer_interval)
        self._timer.timeout.connect(self.refresh_auto)

    def _reload_rows(self):
        """Flatten every component's pins into (component, pin_name, pin) rows."""
        rows = []
        design = self.design
        if design is not None:
            for component_name, component in design.components.items():
                for pin_name, pin in component.pins.items():
                    rows.append((component_name, pin_name, pin))
        self._rows = rows

    def refresh(self):
        """Force refresh. Completely rebuilds the row list."""
        self.beginResetModel()
        try:
            self._reload_rows()
        finally:
            self.endResetModel()
        self.update_view()

    def refresh_auto(self):
        """Polled refresh: only rebuild when the pin count actually changed."""
        if not qt_alive(self._tableView):
            # View destroyed under the model: stop polling for good.
            self._timer.stop()
            return
        design = self.design
        new_count = 0
        if design is not None:
            new_count = sum(len(c.pins) for c in design.components.values())

        if new_count != len(self._rows):
            self.refresh()

    def update_view(self):
        """Resize columns to content after a reset; the header starts hidden
        per the .ui and showing it here matches QTableModel_AllComponents."""
        if self._tableView:
            self._tableView.horizontalHeader().show()
            self._tableView.resizeColumnsToContents()

    def rowCount(self, parent: QModelIndex = None):
        """Number of (component, pin) rows."""
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = None):
        """Number of columns."""
        return len(self.columns)

    def headerData(self, section, orientation: Qt.Orientation, role=Qt.DisplayRole):
        """Column headers. The .ui ships with the header hidden by default;
        update_view() shows it once there is something to label."""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section < len(self.columns):
                return self.columns[section]
        elif role == Qt.FontRole and section == 0:
            font = QFont()
            font.setBold(True)
            return font

    def flags(self, index):
        """Read-only, selectable rows -- editing a pin here has no meaning,
        it is derived entirely from the owning component's geometry."""
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemFlags(
            QAbstractTableModel.flags(self, index) | Qt.ItemIsSelectable
        )

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        """Cell contents for the given index/role."""
        if not index.isValid() or index.row() >= len(self._rows):
            return None

        component_name, pin_name, pin = self._rows[index.row()]

        if role == Qt.DisplayRole:
            column = index.column()
            if column == 0:
                return str(component_name)
            elif column == 1:
                return str(pin_name)
            elif column == 2:
                return str(pin.get("net_id", 0))
            elif column == 3:
                return str(pin.get("chip", ""))

        elif role == Qt.FontRole and index.column() == 0:
            font = QFont()
            font.setBold(True)
            return font

        elif role in (Qt.ToolTipRole, Qt.StatusTipRole):
            net_id = pin.get("net_id", 0)
            state = "connected" if net_id else "not connected"
            return f'Pin "{pin_name}" on component "{component_name}" -- {state}.'

        return None
