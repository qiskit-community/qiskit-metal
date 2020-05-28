from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtCore import QPoint, QModelIndex
from PyQt5.QtWidgets import QInputDialog, QLineEdit, QTableView, QMenu, QMessageBox
from PyQt5.QtWidgets import QAbstractItemView

class RightClickView(QTableView):

    """
    Standard QTableView with drop-down context menu upon right-clicking.
    Menu allows for row deletion and renaming a cell.
    """

    def __init__(self, parent):
        """
        Provide access to GUI QMainWindow via parent.
        """
        super().__init__(parent)
        self.gui = parent.parent()
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

    def contextMenuEvent(self, event: QContextMenuEvent):
        """
        Create options for drop-down context menu.
        """
        self.right_click_menu = QMenu(self)
        self.right_click_menu._d = self.right_click_menu.addAction('Delete')
        self.right_click_menu._r = self.right_click_menu.addAction('Rename')
        row_name, index = self.getPosition(event.pos())
        self.right_click_menu._d.triggered.connect(lambda: self.deleteRow(row_name, index.row()))
        self.right_click_menu._r.triggered.connect(lambda: self.renameRow(row_name, index))
        self.right_click_menu.action = self.right_click_menu.exec_(self.mapToGlobal(event.pos()))

    def getPosition(self, clickedIndex: QPoint):
        """
        Obtain location of clicked cell in form of row name and number.
        """
        index = self.indexAt(clickedIndex)
        name = list(self.gui.model._data.keys())[index.row()]
        if index.isValid():
            return name, index
        return None, None

    def deleteRow(self, row_name: str, row_number: int):
        """
        Create message box to confirm row deletion.
        """
        if row_number > -1:
            choice = QMessageBox.question(self, '', f'Are you sure you want to delete {row_name}?',
                                         QMessageBox.Yes | QMessageBox.No)
            if choice == QMessageBox.Yes:
                self.gui.model.removeRows(row_number)

    def renameRow(self, row_name: str, index: QModelIndex):
        """
        Create message box to confirm row renaming and new name.
        """
        if index.row() > -1:
            text, okPressed = QInputDialog.getText(
                self, 'Rename', f'Rename {row_name} to:', QLineEdit.Normal, '')
            if okPressed and (text != ''):
                self.gui.model.setData(index, text)