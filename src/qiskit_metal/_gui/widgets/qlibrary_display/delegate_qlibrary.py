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

from PySide6.QtCore import QAbstractItemModel, QAbstractProxyModel, QModelIndex, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QItemDelegate, QStyle, QStyleOptionViewItem, QWidget

from qiskit_metal._gui.utility.utils import class_from_abs_file_path
from qiskit_metal._gui.widgets.qlibrary_display.file_model_qlibrary import (
    QFileSystemLibraryModel,
)
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

    def get_source_model(self, model: QAbstractItemModel, source_type: type):
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
                    f"\n{model}"
                )

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
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
        if (
            option.state & QStyle.State_MouseOver
        ):  # if option.state  == QStyle.State_MouseOver: Qt.WA_Hover
            source_model = self.get_source_model(index.model(), self.source_model_type)

            model = index.model()
            full_path = source_model.filePath(model.mapToSource(index))

            try:
                current_class = self.get_class_from_abs_file_path(full_path)
                information = current_class.TOOLTIP
            except Exception:
                # A tooltip must never take the GUI down, so a failed
                # lookup degrades to no tooltip. Narrowed from a bare
                # ``except``, which also swallowed KeyboardInterrupt and
                # SystemExit. Note this is why the resolution bug in
                # issue #1178 stayed invisible for so long.
                information = ""

            self.tool_tip_signal.emit(information)

    def get_class_from_abs_file_path(self, abs_file_path):
        """
        Gets the corresponding class object for the absolute file path to the file containing that
        class definition

        Args:
            abs_file_path (str): absolute file path to the file containing the QComponent class definition

        This used to hold its own copy of the resolution logic, identical
        to the one in ``parameter_entry_window`` -- including the
        substring-slicing bug fixed in issue #1178, which the bare
        ``except`` in ``emit_tool_tip`` silently hid (a failed lookup just
        showed an empty tooltip). Both now share one implementation.
        """
        return class_from_abs_file_path(abs_file_path)
