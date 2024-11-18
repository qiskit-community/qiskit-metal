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

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QModelIndex, Signal
from PySide6.QtWidgets import QTreeView, QWidget

from qiskit_metal._gui.widgets.qlibrary_display.proxy_model_qlibrary import LibraryFileProxyModel
from qiskit_metal.toolbox_metal.exceptions import QLibraryGUIException


class TreeViewQLibrary(QTreeView):
    """Handles editing a QComponent

    This class extend the `QTreeView`
    """

    qlibrary_filepath_signal = Signal(str)

    def __init__(self, parent: QWidget):
        """
        Inits TreeViewQLibrary
        Args:
            parent (QtWidgets.QWidget): parent widget
        """
        QTreeView.__init__(self, parent)
        self.tool_tip_str = "Library of QComponents.\nClick one to create it."
        self.expanded.connect(self.onExpanded)

    def setModel(self, model: QtCore.QAbstractItemModel):
        """Overriding setModel to ensure only correct QAbstractItemModel subclass is used

        Args:
            model (QtCore.QAbstractItemModel): Model to be set

        Raises:
            Exception: QLibraryGUIException if model is not LibraryFileProxyModel

        """
        if not isinstance(model, LibraryFileProxyModel):
            raise QLibraryGUIException(
                f"Invalid model. Expected type {LibraryFileProxyModel} but got type {type(model)}"
            )

        super().setModel(model)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        """Overrides inherited mousePressEvent to emit appropriate filepath signals
         based on which columns were clicked, and to allow user to clear any selections
        by clicking off the displayed tree.

        Args:
            event (QtGui.QMouseEvent): QMouseEvent triggered by user
        """

        index = self.indexAt(event.pos())

        if index.row() == -1:
            self.clearSelection()
            self.setCurrentIndex(QModelIndex())
            return super().mousePressEvent(event)

        model = self.model()
        source_model = self.model().sourceModel()
        full_path = source_model.filePath(model.mapToSource(index))

        if index.column() == source_model.FILENAME:
            if not source_model.isDir(model.mapToSource(index)):
                qis_abs_path = full_path[full_path.
                                         index(__name__.split('.')[0]):]
                self.qlibrary_filepath_signal.emit(qis_abs_path)

        return super().mousePressEvent(event)

    def setToolTip(self, qcomp_tooltip: str):
        """
        Sets tooltip

        Args:
            qcomp_tooltip (str): Tooltip to be set

        """
        if qcomp_tooltip is None or len(qcomp_tooltip) < 1:
            super().setToolTip(self.tool_tip_str)
        else:
            super().setToolTip(qcomp_tooltip)

    def onExpanded(self, index: QModelIndex):
        """Ensure that when we expand the first column names fit in

        Args:
            index (QModelIndex): [description]
        """
        self.resizeColumnToContents(0)
