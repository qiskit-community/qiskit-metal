# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './widgets/build_history/build_history_scroll_area_ui.ui',
# licensing of './widgets/build_history/build_history_scroll_area_ui.ui' applies.
#
# Created: Mon Jun  7 17:21:03 2021
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets


class Ui_BuildHistory(object):

    def setupUi(self, BuildHistory):
        BuildHistory.setObjectName("BuildHistory")
        BuildHistory.resize(1536, 865)
        BuildHistory.setWidgetResizable(True)
        self.display = QtWidgets.QWidget()
        self.display.setGeometry(QtCore.QRect(0, 0, 1534, 863))
        self.display.setObjectName("display")
        self.build_display_vertical_layout = QtWidgets.QVBoxLayout(self.display)
        self.build_display_vertical_layout.setObjectName(
            "build_display_vertical_layout")
        BuildHistory.setWidget(self.display)

        self.retranslateUi(BuildHistory)
        QtCore.QMetaObject.connectSlotsByName(BuildHistory)

    def retranslateUi(self, BuildHistory):
        BuildHistory.setWindowTitle(
            QtWidgets.QApplication.translate(
                "BuildHistory",
                "Build History (click Build History button again to refresh)",
                None, -1))
