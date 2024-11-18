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

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class QWidget_PlaceholderText:
    """QTableView or Tree with placeholder text if empty.

    This class acts as a mixin for placeholder text functionality.
    """
    __placeholder_text = "The table is empty."

    def __init__(self, placeholder_text: str = None, parent=None):
        """
        Args:
            placeholder_text (str): Placeholder text. Defaults to None.
            parent: Parent widget.
        """
        self._placeholder_text = placeholder_text if placeholder_text else self.__placeholder_text
        self._placeholder_label = QLabel(self._placeholder_text, parent)
        self.setup_placeholder_label(parent)

    def setup_placeholder_label(self, parent):
        """Set up the placeholder label."""
        # Update placeholder text
        self.update_placeholder_text()

        # Ensure layout is present
        if parent and not parent.layout():
            layout = QVBoxLayout(parent)
            parent.setLayout(layout)

        if parent:
            parent.layout().addWidget(self._placeholder_label)

    def update_placeholder_text(self, text=None):
        """Update the placeholder text to the given string.

        Args:
            text (str): New placeholder text. Defaults to None.
        """
        if text:
            self._placeholder_text = text

        label = self._placeholder_label
        label.setText(self._placeholder_text)

        # Styling
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        label.setAutoFillBackground(False)
        label.setAttribute(Qt.WA_TranslucentBackground)

        # Placeholder text color
        palette = self._placeholder_label.palette()
        color = palette.color(palette.ColorRole.WindowText)  # Correct usage
        palette.setColor(palette.ColorRole.Text, color)
        label.setPalette(palette)

    def show_placeholder_text(self):
        """Show the placeholder text."""
        self._placeholder_label.show()

    def hide_placeholder_text(self):
        """Hide the placeholder text."""
        self._placeholder_label.hide()