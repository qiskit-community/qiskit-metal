# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './widgets/library_new_qcomponent/parameter_entry_scroll_area_ui.ui',
# licensing of './widgets/library_new_qcomponent/parameter_entry_scroll_area_ui.ui' applies.
#
# Created: Wed Jan 27 15:02:20 2021
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_ScrollArea(object):
    def setupUi(self, ScrollArea):
        ScrollArea.setObjectName("ScrollArea")
        ScrollArea.resize(400, 300)
        ScrollArea.setWidgetResizable(True)
        self.parameter_entry_display = QtWidgets.QWidget()
        self.parameter_entry_display.setGeometry(QtCore.QRect(0, 0, 398, 298))
        self.parameter_entry_display.setObjectName("parameter_entry_display")
        self.parameter_entry_vertical_layout = QtWidgets.QVBoxLayout(self.parameter_entry_display)
        self.parameter_entry_vertical_layout.setObjectName("parameter_entry_vertical_layout")
        ScrollArea.setWidget(self.parameter_entry_display)

        self.retranslateUi(ScrollArea)
        QtCore.QMetaObject.connectSlotsByName(ScrollArea)

    def retranslateUi(self, ScrollArea):
        ScrollArea.setWindowTitle(QtWidgets.QApplication.translate("ScrollArea", "ScrollArea", None, -1))

