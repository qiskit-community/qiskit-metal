# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Ask Zlatko for help on this file"""
from typing import TYPE_CHECKING
from typing import List

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QModelIndex, Qt, QTimer
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import (QInputDialog, QLabel, QLineEdit, QMenu,
                             QMessageBox, QTableView, QVBoxLayout, QAbstractItemView)

from ...utility._handle_qt_messages import catch_exception_slot_pyqt
from ..bases.QWidget_PlaceholderText import QWidget_PlaceholderText

if TYPE_CHECKING:
    from ...main_window import MetalGUI
    from .table_model_all_components import QTableModel_AllComponents


class QTableView_AllComponents(QTableView, QWidget_PlaceholderText):
    """
    Desing components.

    Table model that shows the summary of the components of a design in a table
    with their names, classes, and modules

    Access:
        table = gui.ui.tableComponents
    """

    def __init__(self, parent: QtWidgets.QWidget):
        QTableView.__init__(self, parent)
        QWidget_PlaceholderText.__init__(
            self,  "No QComponents to show.\n\nCreate components from the QLibrary.")
        self.clicked.connect(self.viewClicked)
        self.doubleClicked.connect(self.doDoubleClicked)

        # Handling selection dynamically
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QTableView.SelectRows)

        QTimer.singleShot(100, self.style2)

    def style2(self):
        # Do in the ui file
        self.horizontalHeader().hide()
        self.verticalHeader().show()

        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        selection_model = self.selectionModel()
        selection_model.selectionChanged.connect(self.selection_changed)

    @property
    def design(self):
        return self.model().design

    @property
    def logger(self):
        return self.model().logger

    @property
    def gui(self) -> 'MetalGUI':
        return self.model().gui

    # @catch_exception_slot_pyqt
    def contextMenuEvent(self, event: QContextMenuEvent):
        """
        This event handler, for event event, can be reimplemented
        in a subclass to receive widget context menu events.

        The handler is called when the widget's contextMenuPolicy
        is Qt::DefaultContextMenu.

        The default implementation ignores the context event.
        See the QContextMenuEvent documentation for more details.

        Arguments:
            event {QContextMenuEvent} -- [description]
        """
        self._event = event  # debug

        # TODO: Should we work based on slection or what we have clicked at the moment?
        self.menu = QMenu(self)
        self.menu._d = self.menu.addAction("Delete")
        self.menu._r = self.menu.addAction("Rename")

        self.menu._d.triggered.connect(lambda: self.do_menu_delete(event))
        self.menu._r.triggered.connect(lambda: self.do_menu_rename(event))

        self.menu._action = self.menu.exec_(self.mapToGlobal(event.pos()))

    def get_name_from_event(self, event):
        # get the selected row and column
        row = self.rowAt(event.pos().y())
        #col = self.columnAt(event.pos().x())

        model = self.model()
        index = model.index(row, 0)  # get the name
        name = model.data(index)
        return name, row

    # @catch_exception_slot_pyqt
    def do_menu_delete(self, event):
        """called when the user clicks the context menu delete"""
        name, row = self.get_name_from_event(event)

        if row > -1:
            ret = QMessageBox.question(self, '',
                                       f"Are you sure you want to delete component {name}",
                                       QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self._do_delete(name)

    def _do_delete(self, name: str):
        """do delte a component by name"""
        self.logger.info(f'Deleting {name}')
        self.design.delete_component(name)
        # replot
        self.gui.plot_win.replot()

    def do_menu_rename(self, event):
        """called when the user clicks the context menu rename"""
        name, row = self.get_name_from_event(event)

        if row > -1:
            text, okPressed = QInputDialog.getText(
                self, f"Rename component {name}", f"Rename {name} to:", QLineEdit.Normal, "")
            if okPressed and text != '':
                self.logger.info(f'Renaming {name} to {text}')
                comp_id = self.design.components[name].id
                self.design.rename_component(comp_id, text)

    def viewClicked(self, index: QModelIndex):
        """
        Select a component and set it in the compoient widget when you left click.

        In the init, we had to connect with self.clicked.connect(self.viewClicked)
        """
        if self.gui is None or not index.isValid():
            return

        # get the component name
        # model = clickedIndex.model()  # type: QTableModel_AllComponents
        name = index.sibling(index.row(), 0).data()
        self.logger.debug(f'Selected component {name}')

        gui = self.gui
        gui.edit_component(name)
        gui.ui.dockComponent.show()
        gui.ui.dockComponent.raise_()

    def doDoubleClicked(self, index: QModelIndex):
        """
        SIGNAL: doubleClicked

        This signal is emitted when a mouse button is double-clicked.
        The item the mouse was double-clicked on is specified by index.
        The signal is only emitted when the index is valid.

        Note that single click will also get called.

        """
        if self.gui is None or not index.isValid():
            return

        # name of component
        name = index.sibling(index.row(), 0).data()
        self.gui.canvas.zoom_on_component(name)
        # self.logger.info(f'Double clicked component {name}')

    def rows_to_names(self, rows: List[int]) -> List[str]:
        """Based on user highlighting  rows of components in GUI, return the name of components.

        Args:
            rows (List[int]): User highlighted rows.

        Returns:
            List[str]: List of components that user highlighted.
        """

        def get_name(row): return self.model().data(
            self.model().index(row, 0))  # get the name
        selected_names = [get_name(row) for row in rows]
        return selected_names

    def selection_changed(self, *args):
        """Update by highlighting, the rows which the user selected. 
        """
        rows = set([idx.row() for idx in self.selectedIndexes()])
        selected_names = self.rows_to_names(rows)

        self.logger.debug(f'Highlighting {selected_names}')
        self.gui.highlight_components(selected_names)
