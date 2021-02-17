from PySide2 import QtWidgets
from PySide2.QtCore import QEventLoop, Qt, QTimer, Slot, QModelIndex, QSortFilterProxyModel, QRegExp
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (QApplication, QDockWidget, QFileDialog,
                               QInputDialog, QLabel, QLineEdit, QMainWindow,
                               QMessageBox, QFileSystemModel)
import typing


class LibraryFileProxyModel(QSortFilterProxyModel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # finds all files that
        # (Aren't hidden (begin w/ .), don't begin with __init__, don't begin with _template, etc. AND end in .py)  OR (don't begin with __pycache__ and don't have a '.' in the name)
        # (QComponent files) OR (Directories)
        self.accepted_files__regex = r"(^((?!\.))(?!__init__)(?!_template)(?!__pycache__).*\.py)|(?!__pycache__)(^([^.]+)$)"
        self.setFilterRegExp(self.accepted_files__regex)

    def filterAcceptsColumn(self, source_column: int,
                            source_parent: QModelIndex) -> bool:
        if source_column > 0:  # Won't show Size, Kind, Date Modified, etc. for QFileSystemModel
            return False
        return True
