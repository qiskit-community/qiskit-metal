"""
This is a utility module used for qt.
"""

import numpy as np
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QTableView

__all__ = ['blend_colors']

def blend_colors(color1: QColor, color2: QColor, r: float = 0.2, alpha=255) -> QColor:
    """Blend two qt colors together

    Arguments:
        color1 (QColor): first color
        color2 (QColor): second color
        r (float): ratio
        alpha (int): alpha

    Returns:
        QColor: new color
    """
    color3 = QColor(
        color1.red() * (1-r) + color2.red()*r,
        color1.green() * (1-r) + color2.green()*r,
        color1.blue() * (1-r) + color2.blue()*r,
        alpha)
    return color3
