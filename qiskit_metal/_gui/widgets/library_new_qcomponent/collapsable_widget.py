# code from https://stackoverflow.com/questions/52615115/how-to-create-collapsible-box-in-pyqt
from PySide2 import QtCore, QtGui, QtWidgets, QtWidgets
from PySide2.QtWidgets import QHBoxLayout, QVBoxLayout, QPushButton
from PySide2.QtWidgets import QWidget

class CollapsibleWidget(QtWidgets.QWidget):
    def __init__(self, title="", parent=None):
        super(CollapsibleWidget, self).__init__(parent)

        self.toggle_button = QtWidgets.QToolButton(
            text=title, checkable=True, checked=False
        )
        self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        self.toggle_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonTextBesideIcon
        )
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow)
        self.toggle_button.pressed.connect(self.on_pressed)

        self.toggle_animation_group = QtCore.QParallelAnimationGroup(self)

        self.content_area = QtWidgets.QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.content_area.setWidgetResizable(True)
        self.content_area.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding
        )
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)



        lay = QtWidgets.QVBoxLayout()
        self.setLayout(lay)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

        self.toggle_animation_group.addAnimation(
            QtCore.QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation_group.addAnimation(
            QtCore.QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation_group.addAnimation(
            QtCore.QPropertyAnimation(self.content_area, b"maximumHeight")
        )

    def on_pressed(self):
        checked = self.toggle_button.isChecked()

        collapsed_height = (
            self.sizeHint().height() - self.content_area.maximumHeight()
        )
        print("wig lay", self.content_area.widget().layout())
        content_height = self.content_area.widget().layout().sizeHint().height()
        print("content height", content_height)

        for i in range(self.toggle_animation_group.animationCount()):
            animation = self.toggle_animation_group.animationAt(i)
            animation.setDuration(100)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation_group.animationAt(
            self.toggle_animation_group.animationCount() - 1
        )
        content_animation.setDuration(200)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)

        self.toggle_button.setArrowType(
            QtCore.Qt.DownArrow if not checked else QtCore.Qt.RightArrow
        )
        self.toggle_animation_group.setDirection(
            QtCore.QAbstractAnimation.Forward
            if not checked
            else QtCore.QAbstractAnimation.Backward
        )
        self.toggle_animation_group.start()

    def setContent(self, widget):
        self.content_area.setWidget(widget)





        #sub_entry_content_layout






