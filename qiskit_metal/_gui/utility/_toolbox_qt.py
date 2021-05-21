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

import numpy as np
from PySide2 import QtCore, QtWidgets
from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide2.QtGui import QColor, QFont
from PySide2.QtWidgets import QTableView

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
