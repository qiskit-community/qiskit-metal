# -*- coding: utf-8 -*-

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
"""
Tree view for Param Entry Window
"""

from typing import TYPE_CHECKING

from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtCore import Qt, QTimer
from PySide2.QtWidgets import QTreeView, QAbstractItemView
from PySide2.QtCore import QAbstractTableModel, QModelIndex, Signal
from .proxy_model_qlibrary import LibraryFileProxyModel


class TreeViewQLibrary(QTreeView):
    """Handles editing a QComponent

    This class extend the `QTreeView`
    """

    qlibrary_rebuild_signal = Signal(str)
    qlibrary_filepath_signal = Signal(str)

    def __init__(self, parent: QtWidgets.QWidget):
        """
        Args:
            parent (QtWidgets.QWidget): parent widget
        """
        QTreeView.__init__(self, parent)
        self.is_dev_mode = False  # Whether MetalGUI is in developer mode

    def set_dev_mode(self, ison: bool):
        """ Sets dev mode for self, model, model's source model, and delegate """
        self.is_dev_mode = ison
        self.itemDelegate().is_dev_mode = ison
        self.model().set_dev_mode(ison)
        self.model().sourceModel().set_file_is_dev_mode(ison)

    def setModel(self, model: QtCore.QAbstractItemModel):
        """ Overriding setModel to hook up clean/dirty file signals to model before setting Model"""
        if not isinstance(model, LibraryFileProxyModel):
            print(
                f"Invalid model. Expected type {LibraryFileProxyModel} but got type {type(model)}")
            raise Exception(
                f"Invalid model. Expected type {LibraryFileProxyModel} but got type {type(model)}")

        source_model = model.sourceModel()
        self.qlibrary_rebuild_signal.connect(source_model.clean_file)

        source_model.file_dirtied_signal.connect(
            self.update
        )
        source_model.file_cleaned_signal.connect(
            self.update
        )
        return super().setModel(model)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        """ Overrides inherited mousePressEvent to emit appropriate rebuild or filepath signals
         based on which columns were clicked, and to allow user to clear any selections
        by clicking off the displayed tree and to, when necessary, """

        index = self.indexAt(event.pos())

        if (index.row() == -1):
            self.clearSelection()
            self.setCurrentIndex(QModelIndex())
            return super().mousePressEvent(event)

        model = self.model()
        source_model = self.model().sourceModel()
        full_path = source_model.filePath(model.mapToSource(index))

        """Sends REBUILD signal is REBUILD column is clicked. Sends FILENAME signal if filename is clicked"""

        if self.is_dev_mode and index.column() == source_model.REBUILD:
            qis_abs_path = full_path[full_path.index(__name__.split('.')[0]):]
            self.qlibrary_rebuild_signal.emit(qis_abs_path)
            print("emitted")

        elif index.column() == source_model.FILENAME:
            if not source_model.isDir(model.mapToSource(index)):
                qis_abs_path = full_path[full_path.index(
                    __name__.split('.')[0]):]
                self.qlibrary_filepath_signal.emit(qis_abs_path)

        return super().mousePressEvent(event)
