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

from typing import TYPE_CHECKING

from PySide2 import QtCore, QtWidgets
from PySide2.QtCore import QModelIndex, Qt
from PySide2.QtGui import QContextMenuEvent
from PySide2.QtWidgets import (QInputDialog, QLineEdit, QMenu, QMessageBox,
                               QTableView, QLabel, QVBoxLayout, QWidget)


class QWidget_PlaceholderText(QWidget):
    """QTableView or Tree with palceholder text if empty.

    This class extends the `QWidget` class.
    """
    __placeholder_text = "The table is empty."

    def __init__(self, placeholder_text: str = None):
        """
        Args:
            placeholder_text (str): Placeholder text..  Defaults to None.
        """
        self._placeholder_text = placeholder_text if placeholder_text else self.__placeholder_text

        self._placeholder_label = QLabel(self._placeholder_text, self)
        self.setup_placeholder_label()

    def setup_placeholder_label(self):
        """QComponents will be displayed here when you create them."""
        self.update_placeholder_text()

        if not self.layout():
            layout = QVBoxLayout()
            self.setLayout(layout)

        self.layout().addWidget(self._placeholder_label)

    def update_placeholder_text(self, text=None):
        """Update the placeholder text to the given string.

        Args:
            text (str): New placeholder text..  Defaults to None.
        """
        if text:
            self._placeholder_text = text

        label = self._placeholder_label
        label.setText(self._placeholder_text)

        # Text
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        # transperant
        label.setAutoFillBackground(False)
        label.setAttribute(Qt.WA_TranslucentBackground)

        # color PlaceholderText
        palette = self.palette()
        # This enum value has been introduced in Qt 5.12
        if hasattr(palette, 'PlaceholderText'):
            placeholder_color = palette.PlaceholderText
        else:
            placeholder_color = palette.WindowText
        color = palette.color(placeholder_color)
        palette.setColor(palette.Text, color)
        palette.setColor(palette.Text, color)
        label.setPalette(palette)

    def show_placeholder_text(self):
        """Show the placeholder text."""
        self._placeholder_label.show()

    def hide_placeholder_text(self):
        """Hide the placeholder text."""
        self._placeholder_label.hide()
