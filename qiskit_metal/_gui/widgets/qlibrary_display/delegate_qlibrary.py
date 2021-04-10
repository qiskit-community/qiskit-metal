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
from PySide2.QtWidgets import (
                               QFileSystemModel)

from PySide2.QtWidgets import QItemDelegate
from PySide2.QtCore import QAbstractItemModel, QModelIndex, Qt, QAbstractProxyModel
from PySide2.QtWidgets import (QWidget, QStyleOptionViewItem, QPushButton)
import PySide2
from PySide2.QtGui import QTextDocument
from qiskit_metal._gui.widgets.qlibrary_display.file_model_qlibrary import QFileSystemLibraryModel
USER_COMP_DIR = "user_components"



class LibraryDelegate(QItemDelegate):

    """
    Requires LibraryModel

    """
    def __init__(self,parent=None):
        super().__init__(parent)
        self.source_model_type = QFileSystemLibraryModel
        self.is_dev_mode = False


    # https://www.youtube.com/watch?v=v6clAW6FmcU
    def get_source_model(self, model, source_type):

        while(True):
            # https://stackoverflow.com/questions/50478661/python-isinstance-not-working-as-id-expect
            if model.__class__.__name__ == source_type.__name__:
                return model
            elif isinstance(model, QAbstractProxyModel):
                model = model.sourceModel()
            else:
                raise Exception(f"Unable to find model: "
                                f"\nCurrent Type is: "
                                f"\n{model},  "
                                f"\n Current Expect is:"
                                f"\n{source_type}"
                                f"\n Type(model) is"
                                f"\n{type(model)}"
                                )



    def paint(self, painter:PySide2.QtGui.QPainter, option:PySide2.QtWidgets.QStyleOptionViewItem, index:QModelIndex):
        try:
            if self.is_dev_mode:

                source_model = self.get_source_model(index.model(), self.source_model_type)
                FILENAME = source_model.FILENAME
                REBUILD = source_model.REBUILD

                model = index.model()

                filename = str(model.data(model.sibling(index.row(), FILENAME, index))) # get data of filename

                if source_model.is_file_dirty(filename):
                    if index.column() == FILENAME:

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

                    elif index.column() == REBUILD:
                        if ('.py' in filename):
                            print("REBUILDING COLUM")
                            text = "rebuild"
                            palette = option.palette
                            document = QTextDocument()
                            document.setTextWidth(option.rect.width()) # needed to add Right Alignment:  qt bug : https://bugreports.qt.io/browse/QTBUG-22851
                            text_options = document.defaultTextOption()
                            text_options.setTextDirection(Qt.RightToLeft)
                            document.setDefaultTextOption(text_options) # get right alignment
                            document.setDefaultFont(option.font)
                            document.setHtml(f'<font color={"red"}> <b> {text}</b> </font>')
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

        except Exception as e:
            print("Exception in paint: ", e)