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

from PySide2 import QtCore, QtGui
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QToolBar
import time


class QToolBarExpanding(QToolBar):
    """`QToolBarExpanding` class extends the `QToolBar` class.

    Example:
        ```toolbar = gui.ui.toolBarView```

    Args:
        QToolbar (QToolbar): QToolbar
    """

    def expand_me(self):
        """Expand the toolbar."""
        if self.orientation() == Qt.Vertical:
            tool_style = Qt.ToolButtonTextBesideIcon
            align = Qt.AlignLeft | Qt.AlignVCenter
        else:  # Qt.Horizontal
            tool_style = Qt.ToolButtonTextUnderIcon
            align = Qt.AlignHCenter | Qt.AlignTop

        # show icons and text
        self.setToolButtonStyle(tool_style)

        # align icons and text
        layout = self.layout()
        layout.setAlignment(align)
        layout.setSpacing(layout.spacing())
        for i in range(layout.count()):
            tool = layout.itemAt(i)
            tool.setAlignment(align)
            # https://doc.qt.io/qt-5/qlayoutitem.html#setAlignment

    def contract_me(self):
        """Contract the toolbar."""
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)

    def enterEvent(self, evt: QtCore.QEvent) -> None:
        """enterEvent() is called when the mouse enters the widget's screen
        space. (This excludes screen space owned by any of the widget's
        children.)

        Args:
            evt (QtCore.QEvent): QtCore event
        """
        # should ideally have a timeout thread
        # print('-> Enter')
        self.expand_me()

        super().enterEvent(evt)

    def leaveEvent(self, evt: QtCore.QEvent) -> None:
        """leaveEvent() is called when the mouse leaves the widget's screen
        space. If the mouse enters a child widget it will not cause a
        leaveEvent().

        Args:
            evt (QtCore.QEvent): QtCore event
        """
        # print('<- EXIT')
        # this adds a 0.25sec delay before contracting the widget if mouse accidentally leaves
        time.sleep(0.25)
        self.contract_me()
        super().leaveEvent(evt)
