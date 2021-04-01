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

from PySide2.QtWidgets import QItemDelegate, QStyle
from PySide2.QtCore import QAbstractItemModel, QModelIndex, QTimer, Qt
from PySide2.QtWidgets import (QWidget, QStyleOptionViewItem, QLabel, QApplication)
import PySide2
from PySide2.QtGui import QTextDocument, QColor
USER_COMP_DIR = "user_components"
class LibraryDelegate(QItemDelegate):
    """

    """
    def __init__(self,parent=None):
        super().__init__(parent)


    def paint(self, painter:PySide2.QtGui.QPainter, option:PySide2.QtWidgets.QStyleOptionViewItem, index:PySide2.QtCore.QModelIndex):
        try:
            if index.column() == 1: # add const instead of 1
                text = "refresh"
                palette = option.palette
                document = QTextDocument()
                document.setDefaultFont(option.font)
                document.setHtml(f"<font color={palette.text().color().name()}>{text}</font>")



                #color = palette.back if option.state and QStyle.State_Selected else QColor(index.model().data(index, Qt.BackgroundColorRole))
                color = palette.base().color()
                painter.save()
                painter.fillRect(option.rect, color)
                print("filled rect")
                painter.translate(option.rect.x(), option.rect.y())
                document.drawContents(painter)
                painter.restore()
                #check that file belongs to user_components
            else:
                QItemDelegate.paint(self, painter, option, index)
        except Exception as e:
            print("Exception in paint: ", e)




