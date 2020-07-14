"""Main module that handles the elements window inside the main window.
@author: Zlatko Minev
@date: 2020
"""

from typing import TYPE_CHECKING

import numpy as np
from PyQt5 import Qt, QtCore, QtWidgets
from PyQt5.QtCore import QAbstractTableModel, QModelIndex
from PyQt5.QtWidgets import (QApplication, QFileDialog, QLabel, QMainWindow,
                             QMessageBox)

from .elements_ui import Ui_ElementsWindow

if TYPE_CHECKING:
    # https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
    from .main_window import MetalGUI, QMainWindowExtension


class ElementsWindow(QMainWindow):
    """
    This is just a handler (container) for the UI; it a child object of the main gui.

    Extends the `QMainWindow` class

    PyQt5 Signal / Slots Extensions:
        The UI can call up to this class to execeute button clicks for instance
        Extensiosn in qt designer on signals/slots are linked to this class
    """

    def __init__(self, gui: 'MetalGUI', parent_window: 'QMainWindowExtension'):
        """
        Args:
            gui (MetalGUI): the GUI
            parent_window (QMainWindowExtension): Parent window
        """
        # Q Main Window
        super().__init__(parent_window)

        # Parent GUI related
        self.gui = gui
        self.logger = gui.logger
        self.statusbar_label = gui.statusbar_label

        # UI
        self.ui = Ui_ElementsWindow()
        self.ui.setupUi(self)

        self.statusBar().hide()

        self.model = ElementTableModel(gui, self)
        self.ui.tableElements.setModel(self.model)

    @property
    def design(self):
        """Returns the design"""
        return self.gui.design

    def combo_element_type(self, new_type: str):
        """Change to the given type

        Args:
            new_type (str): Type to change to
        """
        self.logger.info(f'Changed elemtn table type to: {new_type}')
        self.model.set_type(new_type)

    def force_refresh(self):
        """Force a refresh"""
        self.model.refresh()


class ElementTableModel(QAbstractTableModel):

    """MVC class
    See https://doc.qt.io/qt-5/qabstracttablemodel.html

    The class extends the `QAbstractTableModel` class.

    Can be accessed with:
        .. code-block:: python

            t = gui.elements_win.tableElements
            model = t.model()
            index = model.index(1,0)
            model.data(index)

    """
    __timer_interval = 500  # ms

    def __init__(self, gui, parent=None, element_type='poly'):
        super().__init__(parent=parent)
        """
        Args:
            gui (MetalGUI): The GUI
            parent (QMainWindowExtension): Parent window (Default: None)
            element_type (str): the elment type (Default: 'poly')
        """
        self.logger = gui.logger
        self.gui = gui
        self._row_count = -1
        self.type = element_type

        self._create_timer()

    @property
    def design(self):
        """Returns the design"""
        return self.gui.design

    @property
    def qgeometry(self):
        """Returns the qgeometry"""
        if self.design:
            return self.design.qgeometry

    @property
    def tables(self):
        """Returns all the tables"""
        if self.design:
            return self.design.qgeometry.tables

    @property
    def table(self):
        """Returns all the tables of the type specified in the constructor"""
        if self.design:
            return self.design.qgeometry.tables[self.type]

    def _create_timer(self):
        """
        Refresh the model number of rows, etc. there must be a smarter way?
        """
        self._timer = QtCore.QTimer(self)
        self._timer.start(self.__timer_interval)
        self._timer.timeout.connect(self.refresh_auto)

    def set_type(self, element_type: str):
        self.type = element_type
        self.refresh()

    def refresh(self):
        """Force refresh.   Completly rebuild the model."""
        self.modelReset.emit()

    def refresh_auto(self):
        """
        Update row count etc.
        """
        # We could not do if the widget is hidden - TODO: speed performace?

        # TODO: This should probably just be on a global timer for all changes detect
        # and then update all accordingly
        new_count = self.rowCount()

        # if the number of rows have changed
        if self._row_count != new_count:
            #self.logger.info('Number of components changed')

            # When a model is reset it should be considered that all
            # information previously retrieved from it is invalid.
            # This includes but is not limited to the rowCount() and
            # columnCount(), flags(), data retrieved through data(), and roleNames().
            # This will loose the current selection.
            # TODO: This seems overkill to just change the total number of rows?
            self.modelReset.emit()

            self._row_count = new_count

    def rowCount(self, parent: QModelIndex = None):
        """Counts all the rows

        Args:
            parent (QModelIndex): Unused (Default: None)

        Returns:
            int: the number of rows
        """
        if self.table is None:
            return 0
        return self.table.shape[0]

    def columnCount(self, parent: QModelIndex = None):
        """Counts all the columns

        Args:
            parent (QModelIndex): Unused (Default: None)

        Returns:
            int: the number of columns
        """
        if self.table is None:
            return 0
        return self.table.shape[1]

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """ Set the headers to be displayed.

        Args:
            section (int): section number
            orientation (Qt orientation): section orientation
            role (Qt display role): display role (Default: DisplayRole)

        Returns:
            str: the header data, or None if not found
        """

        if (role != QtCore.Qt.DisplayRole) or (self.table is None):
            return None

        if orientation == QtCore.Qt.Horizontal:
            if section < self.columnCount():
                return str(self.table.columns[section])

    def flags(self, index: QModelIndex):
        """ Set the item flags at the given index. Seems like we're
        implementing this function just to see how it's done, as we
        manually adjust each tableView to have NoEditTriggers.

        Args:
            index (QModelIndex): the index

        Returns:
            Qt flags: Flags from Qt
        """
        # https://doc.qt.io/qt-5/qt.html#ItemFlag-enum

        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled

        return QtCore.Qt.ItemFlags(QAbstractTableModel.flags(self, index) |
                                   QtCore.Qt.ItemIsSelectable)  # ItemIsEditable

    def data(self, index: QModelIndex, role=QtCore.Qt.DisplayRole):
        """ Depending on the index and role given, return data. If not
        returning data, return None (PySide equivalent of QT's
        "invalid QVariant").

        Returns:
            str: data
        """

        if not index.isValid():
            return
        # if not 0 <= index.row() < self.rowCount():
        #    return None

        if self.table is None:
            return

        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            column = index.column()
            return str(self.table.iloc[row, column])
