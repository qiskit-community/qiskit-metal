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

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import QModelIndex, Signal
from PySide2.QtWidgets import QTreeView, QWidget

from qiskit_metal._gui.widgets.qlibrary_display.proxy_model_qlibrary import LibraryFileProxyModel
from qiskit_metal.toolbox_metal.exceptions import QLibraryGUIException


class TreeViewQLibrary(QTreeView):
    """Handles editing a QComponent

    This class extend the `QTreeView`
    """

    qlibrary_rebuild_signal = Signal(str)
    qlibrary_filepath_signal = Signal(str)
    qlibrary_file_dirtied_signal = Signal()

    def __init__(self, parent: QWidget):
        """
        Inits TreeViewQLibrary
        Args:
            parent (QtWidgets.QWidget): parent widget
        """
        QTreeView.__init__(self, parent)
        self.is_dev_mode = False  # Whether MetalGUI is in developer mode
        self.tool_tip_str = "Library of QComponents"

    def set_dev_mode(self, ison: bool):
        """Sets dev mode for self, model, model's source model, and delegate

        Args:
            ison (bool): Whether to set dev mode
        """
        self.is_dev_mode = ison
        self.itemDelegate().is_dev_mode = ison
        self.model().set_dev_mode(ison)
        self.model().sourceModel().set_file_is_dev_mode(ison)

    def raise_dirty_file(self):
        self.qlibrary_file_dirtied_signal.emit()

    def setModel(self, model: QtCore.QAbstractItemModel):
        """Overriding setModel to hook up clean/dirty file signals to model before setting Model

        Args:
            model (QtCore.QAbstractItemModel): Model to be set

        Raises:
            Exception: QLibraryGUIException if model is not LibraryFileProxyModel

        """
        if not isinstance(model, LibraryFileProxyModel):
            raise QLibraryGUIException(
                f"Invalid model. Expected type {LibraryFileProxyModel} but got type {type(model)}"
            )

        source_model = model.sourceModel()
        self.qlibrary_rebuild_signal.connect(source_model.clean_file)

        source_model.file_dirtied_signal.connect(self.update)
        source_model.file_dirtied_signal.connect(self.raise_dirty_file)
        source_model.file_cleaned_signal.connect(self.update)
        super().setModel(model)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        """Overrides inherited mousePressEvent to emit appropriate rebuild or filepath signals
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

        if self.is_dev_mode and index.column() == source_model.REBUILD:
            qis_abs_path = full_path[full_path.index(__name__.split('.')[0]):]
            self.qlibrary_rebuild_signal.emit(qis_abs_path)

        elif index.column() == source_model.FILENAME:
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
