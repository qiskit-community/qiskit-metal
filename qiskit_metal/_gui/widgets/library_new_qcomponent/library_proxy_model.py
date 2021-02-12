from PySide2 import QtWidgets
from PySide2.QtCore import QEventLoop, Qt, QTimer, Slot, QModelIndex, QSortFilterProxyModel, QRegExp
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (QApplication, QDockWidget, QFileDialog,
                               QInputDialog, QLabel, QLineEdit, QMainWindow,
                               QMessageBox, QFileSystemModel)

class LibraryProxyModel(QSortFilterProxyModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)