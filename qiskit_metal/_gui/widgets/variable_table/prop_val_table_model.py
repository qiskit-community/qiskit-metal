from PyQt5 import Qt, QtGui, QtCore
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from .add_delete_table import Ui_MainWindow


class PropValTable(QAbstractTableModel):
    
    """
    Design variables table model that shows variable name and dimension,
    both with and without units.
    """
    
    __refreshtime = 500 # 0.5 second refresh time
    
    def __init__(self, design=None, gui=None):
        super().__init__()
        self._design = design
        self._gui = gui
        # self._data = data
        self._rowCount = -1
        self._start_timer()

    def set_design(self, design):
        self._design = design
        self.modelReset.emit()
        #refresh table or something if needed

    @property
    def design(self):
        return self._design

    @property
    def _data(self)->dict:
        if self._design:
            return self._design.variables
        
    def _start_timer(self):
        """
        Start and continuously refresh timer in background to keep
        the total number of rows up to date.
        """
        self.timer = QtCore.QTimer(self)
        self.timer.start(self.__refreshtime)
        self.timer.timeout.connect(self.auto_refresh)
        
    def auto_refresh(self):
        newRowCount = self.rowCount(self)
        if self._rowCount != newRowCount:
            self.modelReset.emit()
            self._rowCount = newRowCount
        
    def rowCount(self, index: QModelIndex) -> int:
        if self._design:
            return len(self._data)
        else:
            return 0
    
    def columnCount(self, index: QModelIndex) -> int:
        return 3
    
    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.DisplayRole):
        """
        Return data for corresponding index and role.
        """
        r = index.row()
        c = index.column()
        if role == Qt.DisplayRole:
            if c == 0:
                return list(self._data.keys())[r]
            if c == 1:
                return self._data[list(self._data.keys())[r]]
            return self.design.parse_value(self._data[list(self._data.keys())[r]])

        # double clicking
        elif role == Qt.EditRole:
            return self.data(index, Qt.DisplayRole)

        elif (role == Qt.FontRole) and (c == 0):
            font = QFont()
            font.setBold(True)
            return font
    
    def setData(self, index: QModelIndex, value: str, role: Qt.ItemDataRole = Qt.EditRole):
        """
        Modify either key or value (Property or Value) of dictionary depending on what
        the user selected manually on the table.
        """
        r = index.row()
        c = index.column()
        if value:
            if c == 0:
                # TODO: LRU Cache for speed?
                oldkey = list(self._data.keys())[r]
                if value != oldkey:
                    self.design.rename_variable(oldkey, value)
            elif c == 1:
                self._data[list(self._data.keys())[r]] = value
            self._gui.rebuild()
            
    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = Qt.DisplayRole) -> str:
        """
        Set the headers to be displayed.
        """
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section == 0:
                    return 'Property'
                if section == 1:
                    return 'Value'
                return 'Number'
            return str(section + 1)
        
    def removeRows(self, row: int, count: int = 1, parent = QModelIndex()):
        """
        Delete highlighted rows.
        """
        self.beginRemoveRows(parent, row, row + count - 1)
        lst = list(self._data.keys())
        for k in range(row + count - 1, row - 1, -1):
            del self._data[lst[k]]
        self.endRemoveRows()
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """
        Determine how user may interact with each cell in the table.
        """
        if index.column() < 2:
            return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
    
    def add_row(self, key: str, val: str):
        self._data[key] = val