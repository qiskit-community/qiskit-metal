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
"""This is a utility module used for qt."""

from PySide2 import QtCore, QtWidgets
from PySide2.QtCore import QTimer
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QDockWidget

__all__ = ['blend_colors']


def blend_colors(color1: QColor,
                 color2: QColor,
                 r: float = 0.2,
                 alpha=255) -> QColor:
    """Blend two qt colors together.

    Args:
        color1 (QColor): first color
        color2 (QColor): second color
        r (float): ratio
        alpha (int): alpha

    Returns:
        QColor: new color
    """
    color3 = QColor(color1.red() * (1 - r) + color2.red() * r,
                    color1.green() * (1 - r) + color2.green() * r,
                    color1.blue() * (1 - r) + color2.blue() * r, alpha)
    return color3


#------------------------------------------------------------------------------------------

STYLE_HIGHLIGHT = r"""
QWidget {
    outline: 3px solid red;
    border: 3px solid red;
}"""


def doShowHighlighWidget(self: QDockWidget,
                         timeout=1500,
                         STYLE_HIGHLIGHT=STYLE_HIGHLIGHT):
    """Highlight temporarily, raise, show the widget.
    Force resets the style at the component to None after a period. 
    """
    self.setStyleSheet(STYLE_HIGHLIGHT)
    self.show()
    self.raise_()

    def doResetStyle(self: 'QDockWidget'):
        self.setStyleSheet('')

    self.doResetStyle = doResetStyle.__get__(self, type(self))
    # monkey patch class instance:
    # https://stackoverflow.com/questions/28127874/monkey-patching-python-an-instance-method

    QTimer.singleShot(timeout, self.doResetStyle)


### Alternative to doShowHighlighWidget:

# from PySide2.QtWidgets import QFrame, QWidget
# from PySide2 import QtCore
# obj = gui.canvas
# frame = QFrame(obj.parent())
# frame.setGeometry(obj.frameGeometry())
# frame.setFrameShape(QFrame.Box)
# frame.setLineWidth(3)
# frame.show()

# frame.setStyleSheet(r"""
#   border-radius: 10px;
#   outline: 3px solid red;
#   border: 3px solid red;
#   background-color: transparent;
#   border-image:none;
# """)
# ## the folloing make it dissapear altoheger
# # frame.setWindowFlags(QtCore.Qt.FramelessWindowHint)
# # frame.setAttribute(QtCore.Qt.WA_TranslucentBackground)

# # Alternative see: https://stackoverflow.com/questions/58458323/how-to-use-qt-stylesheet-to-customize-only-partial-qwidget-border

#------------------------------------------------------------------------------------------
