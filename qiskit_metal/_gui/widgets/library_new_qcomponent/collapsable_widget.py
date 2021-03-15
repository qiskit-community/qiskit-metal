# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""
QLibrary display in Library tab

@authors: Grace Harper
@date: 2021
"""

from PySide2 import QtCore, QtWidgets


# code from https://stackoverflow.com/questions/52615115/how-to-create-collapsible-box-in-pyqt
class CollapsibleWidget(QtWidgets.QWidget):

    def __init__(self, title="", parent=None):
        """
        Creates a Widget that can collapse and un-collapse at the click of a toggle button

        Args:
            title: Displayed title of the Collapsible Widget
            parent: Collapsed Widget's parent
        """
        super(CollapsibleWidget, self).__init__(parent)

        self.toggle_button = QtWidgets.QToolButton(text=title,
                                                   checkable=True,
                                                   checked=False)

        self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        self.toggle_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow)
        self.toggle_button.pressed.connect(self.on_pressed)

        self.toggle_animation = QtCore.QParallelAnimationGroup(self)

        self.content_area = QtWidgets.QScrollArea(maximumHeight=0,
                                                  minimumHeight=0)
        self.content_area.setWidgetResizable(True)
        self.content_area.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                        QtWidgets.QSizePolicy.MinimumExpanding)
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"minimumHeight"))
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"maximumHeight"))
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self.content_area, b"maximumHeight"))

        self.is_set_up = False

    def on_pressed(self):
        """Toggles Collapsible Widget when toggle arrow is pressed"""
        if not self.is_set_up:
            self.set_up()

        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(
            QtCore.Qt.RightArrow if self.toggle_button.arrowType() ==
            QtCore.Qt.DownArrow else QtCore.Qt.DownArrow)
        self.toggle_animation.setDirection(
            QtCore.QAbstractAnimation.Backward if self.toggle_button.arrowType(
            ) == QtCore.Qt.RightArrow else QtCore.QAbstractAnimation.Forward)

        self.toggle_animation.start()

    def setContent(self, widget):
        """ Set's Collapsible Widget's content"""
        self.content_area.setWidget(widget)

    def set_up(self):
        """ Calculates animation variables and set up animation (collapsing/expanding) for Collapsible Widget"""

        self.collapsed_height = (self.sizeHint().height() -
                                 self.content_area.maximumHeight())
        self.content_height = self.content_area.widget().layout().sizeHint(
        ).height()

        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(self.collapsed_height)
            animation.setEndValue(self.collapsed_height + self.content_height)

        # what does this do
        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1)
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(self.content_height)
        self.is_set_up = True
