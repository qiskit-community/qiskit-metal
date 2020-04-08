"""Main module that handles a component  inside the main window.
@author: Zlatko Minev
@date: 2020
"""

from PyQt5 import Qt, QtCore, QtWidgets
import numpy as np
from PyQt5.QtCore import QAbstractTableModel
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QMessageBox, QFileDialog, QTabWidget

from .component_widget_ui import Ui_ComponentWidget

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
    from .main_window import MetalGUI, QMainWindowExtension


class ComponentWidget(QTabWidget):
    """
    This is just a handler (container) for the UI; it a child object of the main gui.

    PyQt5 Signal / Slots Extensions:
        The UI can call up to this class to execeute button clicks for instance
        Extensiosn in qt designer on signals/slots are linked to this class
    """

    def __init__(self, gui: 'MetalGUI', parent:QtWidgets.QWidget):
        # Q Main WIndow
        super().__init__(parent)

        # Parent GUI related
        self.gui = gui
        self.logger = gui.logger
        self.statusbar_label = gui.statusbar_label

        # UI
        self.ui = Ui_ComponentWidget()
        self.ui.setupUi(gui.ui.component_tab)
        #self.ui.component_tab.ui = Ui_ComponentWidget()
        #self.ui.component_tab.ui.setupUi(self.ui.component_tab)

        self.component_name = None # type: str

        self.model = ComponentTableModel(gui, self)
        self.ui.tableView.setModel(self.model)

    @property
    def design(self):
        return self.gui.design

    @property
    def component(self):
        if self.design:
            return self.design.components.get(self.component_name, None)

    def set_component(self, name:str):
        self.component_name = name

        component = self.component
        self.ui.labelComponentName.setText(str(component.name))

        self.force_refresh()

    def force_refresh(self):
        self.model.refresh()











class ComponentTableModel(QAbstractTableModel):

    """MVC class
    See https://doc.qt.io/qt-5/qabstracttablemodel.html
    """
    #__timer_interval = 500  # ms

    def __init__(self, gui, parent:ComponentWidget=None):
        super().__init__(parent=parent)
        self.logger = gui.logger
        self.gui = gui
        self._row_count = -1

        #self._create_timer()
        self.columns = ['Name', 'Value']

    @property
    def design(self):
        return self.gui.design

    @property
    def component(self):
        return self.parent().component

    # def _create_timer(self):
    #     """
    #     Refresh the model number of rows, etc. there must be a smarter way?
    #     """
    #     self._timer = QtCore.QTimer(self)
    #     self._timer.start(self.__timer_interval)
    #     self._timer.timeout.connect(self.refresh_auto)

    # def refresh_auto(self):
    #     """
    #     Update row count etc.
    #     """
    #     # We could not do if the widget is hidden - TODO: speed performace?

    #     # TODO: This should probably just be on a global timer for all changes detect
    #     # and then update all accordingly
    #     new_count = self.rowCount()

    #     # if the number of rows have changed
    #     if self._row_count != new_count:
    #         #self.logger.info('Number of components changed')

    #         # When a model is reset it should be considered that all
    #         # information previously retrieved from it is invalid.
    #         # This includes but is not limited to the rowCount() and
    #         # columnCount(), flags(), data retrieved through data(), and roleNames().
    #         # This will loose the current selection.
    #         # TODO: This seems overkill to just change the total number of rows?
    #         self.modelReset.emit()

    #         self._row_count = new_count

    def refresh(self):
        """Force refresh.   Completly rebuild the model."""
        self.modelReset.emit()

    def rowCount(self, parent=None):  # =QtCore.QModelIndex()):
        if self.component is None:
            return 0
        return len(self.component.options) #TODO:

    def columnCount(self, parent=None):  # =QtCore.QModelIndex()):
        return 2

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """ Set the headers to be displayed. """

        if (role != QtCore.Qt.DisplayRole) or (self.component is None):
            return None

        if orientation == QtCore.Qt.Horizontal:
            if section < self.columnCount():
                return self.columns[section]

    def flags(self, index):
        """ Set the item flags at the given index. Seems like we're
            implementing this function just to see how it's done, as we
            manually adjust each tableView to have NoEditTriggers.
        """
        # https://doc.qt.io/qt-5/qt.html#ItemFlag-enum

        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled

        return QtCore.Qt.ItemFlags(QAbstractTableModel.flags(self, index) |
                                   QtCore.Qt.ItemIsSelectable)  # ItemIsEditable

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """ Depending on the index and role given, return data. If not
            returning data, return None (PySide equivalent of QT's
            "invalid QVariant").
        """

        if not index.isValid():
            return
        # if not 0 <= index.row() < self.rowCount():
        #    return None

        if self.component is None:
            return

        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            column = index.column()
            data = self.component.options
            if column == 0:
                data = list(data.keys())
            elif column == 1:
                data = list(data.values())
            return str(data[row])
