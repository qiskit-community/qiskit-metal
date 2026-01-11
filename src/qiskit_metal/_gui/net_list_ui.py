# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './net_list_ui.ui',
# licensing of './net_list_ui.ui' applies.
#
# Created: Wed May 25 09:29:27 2022
#      by: pyside6-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide6 import QtCore, QtGui, QtWidgets


class Ui_NetListWindow(object):

    def setupUi(self, NetListWindow):
        NetListWindow.setObjectName("NetListWindow")
        NetListWindow.resize(841, 623)
        self.centralwidget = QtWidgets.QWidget(NetListWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.tableElements = QtWidgets.QTableView(self.centralwidget)
        self.tableElements.setProperty("showDropIndicator", False)
        self.tableElements.setDragDropOverwriteMode(False)
        self.tableElements.setAlternatingRowColors(True)
        self.tableElements.setObjectName("tableElements")
        self.verticalLayout.addWidget(self.tableElements)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        NetListWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar()
        self.menubar.setGeometry(QtCore.QRect(0, 0, 841, 24))
        self.menubar.setObjectName("menubar")
        NetListWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(NetListWindow)
        self.statusbar.setObjectName("statusbar")
        NetListWindow.setStatusBar(self.statusbar)

        self.retranslateUi(NetListWindow)
        QtCore.QMetaObject.connectSlotsByName(NetListWindow)

    def retranslateUi(self, NetListWindow):
        NetListWindow.setWindowTitle(
            QtWidgets.QApplication.translate("NetListWindow", "MainWindow",
                                             None, -1))
