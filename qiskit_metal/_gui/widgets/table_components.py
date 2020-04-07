from .._handle_qt_messages import catch_exception_slot_pyqt
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QTableView, QInputDialog, QLineEdit
from PyQt5.QtWidgets import (QMenu, QMessageBox)


class TableComponents(QTableView):

    @property
    def design(self):
        return self.model().design

    @property
    def logger(self):
        return self.model().logger

    @property
    def gui(self):
        return self.model().gui

    # @catch_exception_slot_pyqt
    def contextMenuEvent(self, event):
        self._event = event  # debug

        self.menu = QMenu(self)
        self.menu._d = self.menu.addAction("Delete")
        self.menu._r = self.menu.addAction("Rename")

        self.menu._d.triggered.connect(lambda: self.do_menu_delete(event))
        self.menu._r.triggered.connect(lambda: self.do_menu_rename(event))

        self.menu._action = self.menu.exec_(self.mapToGlobal(event.pos()))

    # @catch_exception_slot_pyqt
    def do_menu_delete(self, event):

        # get the selected row and column
        row = self.rowAt(event.pos().y())
        #col = self.columnAt(event.pos().x())

        model = self.model()
        index = model.index(row, 0)  # get the name
        name = model.data(index)

        if row > -1:
            ret = QMessageBox.question(self, '', f"Are you sure you want to delete component {name}",
                                       QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.logger.info(f'Deleting {name}')
                self.design.delete_component(name)

    def do_menu_rename(self, event):

        # get the selected row and column
        row = self.rowAt(event.pos().y())
        #col = self.columnAt(event.pos().x())

        model = self.model()
        index = model.index(row, 0)  # get the name
        name = model.data(index)

        if row > -1:
            text, okPressed = QInputDialog.getText(
                self, f"Rename component {name}", f"Rename {name} to:", QLineEdit.Normal, "")
            if okPressed and text != '':
                self.logger.info(f'Renaming {name} to {text}')
                self.design.rename_component(name, text)
