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
Delegate for display of QComponents in Library tab
"""

import importlib
import inspect
import os

from PySide6.QtCore import QAbstractItemModel, QAbstractProxyModel, QModelIndex, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QItemDelegate, QStyle, QStyleOptionViewItem, QWidget

from qiskit_metal._gui.widgets.qlibrary_display.file_model_qlibrary import QFileSystemLibraryModel
from qiskit_metal.toolbox_metal.exceptions import QLibraryGUIException


class LibraryDelegate(QItemDelegate):
    """
    Delegate for QLibrary view
    Requires LibraryModel
    """

    tool_tip_signal = Signal(str)

    def __init__(self, parent: QWidget = None):
        """
         Initializer for LibraryDelegate

        Args:
            parent(QWidget): parent
        """
        super().__init__(parent)
        #  The Delegate may belong to a view using a ProxyModel but even so
        #  the source model for that Proxy Model(s) should be a QFileSystemLibraryModel
        self.source_model_type = QFileSystemLibraryModel

    def get_source_model(self, model: QAbstractItemModel, source_type: type):  # pylint: disable=R0201, no-self-use
        """
        The Delegate may belong to a view using a ProxyModel. However,
        the source model for that Proxy Model(s) should be a QFileSystemLibraryModel
        and is returned by this function

        Args:
            model(QAbstractItemModel): Current model
            source_type(type): Expected source model type
        Returns:
            QFileSystemLibraryModel: Source model
        Raises:
            QLibraryGUIException: If unable to find the source model for the given model
        """
        while True:
            # https://stackoverflow.com/questions/50478661/python-isinstance-not-working-as-id-expect
            if model.__class__.__name__ == source_type.__name__:
                return model
            if isinstance(model, QAbstractProxyModel):
                model = model.sourceModel()
            else:
                raise QLibraryGUIException(
                    f"Unable to find source model: "
                    f"\n Expected Type is:"
                    f"\n{source_type}"
                    f"\n First non-proxy model type found is"
                    f"\n{type(model)} for"
                    f"\n{model}")

    def paint(self, painter: QPainter, option: QStyleOptionViewItem,
              index: QModelIndex):
        """
        Paints the Metal GUI QLibrary.
        If hovering over a file with a tooltip, emits the tooltip signal
        Args:
            painter (QPainter): Current painter
            option (QStyleOptionViewItem): Current option
            index (QModelIndex): Current index of related model
        Emits:
            tool_tip_signal(str): The TOOLTIP for the QComponent being hovered over by the mouse


        """

        self.emit_tool_tip(option, index)
        QItemDelegate.paint(self, painter, option, index)

    def emit_tool_tip(self, option: QStyleOptionViewItem, index: QModelIndex):
        """

        Args:
            option (QStyleOptionViewItem): Contains current style flags
            index (QModelIndex): Index being moused over

        Emits:
           tool_tip_signal(str): The TOOLTIP for the QComponent of the index
        """
        if option.state & QStyle.State_MouseOver:  # if option.state  == QStyle.State_MouseOver: Qt.WA_Hover
            source_model = self.get_source_model(index.model(),
                                                 self.source_model_type)

            model = index.model()
            full_path = source_model.filePath(model.mapToSource(index))

            # try:
            try:
                current_class = self.get_class_from_abs_file_path(full_path)
                information = current_class.TOOLTIP
            except:
                information = ""

            self.tool_tip_signal.emit(information)

    def get_class_from_abs_file_path(self, abs_file_path):
        """
        Gets the corresponding class object for the absolute file path to the file containing that
        class definition

        Args:
            abs_file_path (str): absolute file path to the file containing the QComponent class definition

        getting class from absolute file path -
        https://stackoverflow.com/questions/452969/does-python-have-an-equivalent-to-java-class-forname

        """
        qis_abs_path = abs_file_path[abs_file_path.
                                     index(__name__.split('.')[0]):]

        # Windows users' qis_abs_path may use os.sep or '/' due to PySide's
        # handling of file names
        qis_mod_path = qis_abs_path.replace(os.sep, '.')[:-len('.py')]
        qis_mod_path = qis_mod_path.replace(
            "/", '.')  # users cannot use '/' in filename

        mymodule = importlib.import_module(qis_mod_path)
        members = inspect.getmembers(mymodule, inspect.isclass)
        class_owner = qis_mod_path.split('.')[-1]
        for memtup in members:
            if len(memtup) > 1:
                if str(memtup[1].__module__).endswith(class_owner):
                    return memtup[1]
