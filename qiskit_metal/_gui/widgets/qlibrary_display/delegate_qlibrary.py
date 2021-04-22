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

from PySide2.QtWidgets import QItemDelegate, QWidget, QStyleOptionViewItem
from PySide2.QtCore import QAbstractProxyModel, QModelIndex, Qt, QAbstractItemModel
from PySide2.QtGui import QTextDocument, QPainter
from qiskit_metal._gui.widgets.qlibrary_display.file_model_qlibrary import QFileSystemLibraryModel
from qiskit_metal.toolbox_metal.exceptions import QLibraryGUIException

USER_COMP_DIR = "user_components"


class LibraryDelegate(QItemDelegate):
    """
    Delegate for QLibrary view
    Requires LibraryModel
    """

    def __init__(self, parent: QWidget = None):
        """
        source_model_type - The Delegate may belong to a view using a ProxyModel.
        However, the source model for that Proxy Model(s) should be a QFileSystemLibraryModel
        is_dev_mode - Whether the MetalGUI is in Developer Mode or not

        Args:
            parent: parent

        """
        super().__init__(parent)
        self.source_model_type = QFileSystemLibraryModel
        self.is_dev_mode = False

    def get_source_model(self, model: QAbstractItemModel, source_type: type):  # pylint: disable=R0201, no-self-use
        """
        The Delegate may belong to a view using a ProxyModel. However,
        the source model for that Proxy Model(s) should be a QFileSystemLibraryModel
        and is returned by this function


        Args:
            model: Current model
            source_type: Expected source model type

        Returns: source model : QFileSystemLibraryModel

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
        Displays dirty files in red with corresponding rebuild buttons
        if in developer mode (is_dev_mode). Otherwise, renders normally
        Args:
            painter: QPainter
            option: QStyleOptionViewItem
            index: QModelIndex



        """
        if self.is_dev_mode:
            source_model = self.get_source_model(index.model(),
                                                 self.source_model_type)

            model = index.model()

            # get data of filename
            filename = str(
                model.data(
                    model.sibling(index.row(), source_model.FILENAME, index)))

            if source_model.is_file_dirty(filename):
                if index.column() == source_model.FILENAME:

                    text = filename
                    palette = option.palette
                    document = QTextDocument()
                    document.setDefaultFont(option.font)
                    document.setHtml(f"<font color={'red'}>{text}</font>")
                    background_color = palette.base().color()
                    painter.save()
                    painter.fillRect(option.rect, background_color)
                    painter.translate(option.rect.x(), option.rect.y())
                    document.drawContents(painter)
                    painter.restore()

                elif index.column() == source_model.REBUILD:
                    if '.py' in filename:
                        text = "rebuild"
                        palette = option.palette
                        document = QTextDocument()
                        # needed to add Right Alignment:  qt bug :
                        # https://bugreports.qt.io/browse/QTBUG-22851
                        document.setTextWidth(option.rect.width())
                        text_options = document.defaultTextOption()
                        text_options.setTextDirection(Qt.RightToLeft)
                        document.setDefaultTextOption(
                            text_options)  # get right alignment
                        document.setDefaultFont(option.font)
                        document.setHtml(
                            f'<font color={"red"}> <b> {text}</b> </font>')
                        background_color = palette.base().color()
                        painter.save()
                        painter.fillRect(option.rect, background_color)
                        painter.translate(option.rect.x(), option.rect.y())
                        document.drawContents(painter)
                        painter.restore()

            else:
                QItemDelegate.paint(self, painter, option, index)

        else:
            QItemDelegate.paint(self, painter, option, index)
