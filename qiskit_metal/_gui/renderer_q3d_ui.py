# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './renderer_q3d_ui.ui',
# licensing of './renderer_q3d_ui.ui' applies.
#
# Created: Mon Jun  7 17:21:01 2021
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(651, 544)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.instructionsLabel = QtWidgets.QLabel(self.centralwidget)
        self.instructionsLabel.setGeometry(QtCore.QRect(20, 10, 201, 16))
        self.instructionsLabel.setObjectName("instructionsLabel")
        self.horizontalLayoutWidget_2 = QtWidgets.QWidget(self.centralwidget)
        self.horizontalLayoutWidget_2.setGeometry(QtCore.QRect(
            10, 470, 301, 32))
        self.horizontalLayoutWidget_2.setObjectName("horizontalLayoutWidget_2")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(
            self.horizontalLayoutWidget_2)
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.refreshButton = QtWidgets.QPushButton(
            self.horizontalLayoutWidget_2)
        self.refreshButton.setObjectName("refreshButton")
        self.horizontalLayout_4.addWidget(self.refreshButton)
        self.selectAllButton = QtWidgets.QPushButton(
            self.horizontalLayoutWidget_2)
        self.selectAllButton.setObjectName("selectAllButton")
        self.horizontalLayout_4.addWidget(self.selectAllButton)
        self.deselectAllButton = QtWidgets.QPushButton(
            self.horizontalLayoutWidget_2)
        self.deselectAllButton.setObjectName("deselectAllButton")
        self.horizontalLayout_4.addWidget(self.deselectAllButton)
        self.listView = QtWidgets.QListView(self.centralwidget)
        self.listView.setGeometry(QtCore.QRect(10, 31, 301, 431))
        self.listView.setObjectName("listView")
        self.treeView = QTreeView_Base(self.centralwidget)
        self.treeView.setGeometry(QtCore.QRect(325, 30, 311, 431))
        self.treeView.setRootIsDecorated(False)
        self.treeView.setObjectName("treeView")
        self.instructionsLabel_2 = QtWidgets.QLabel(self.centralwidget)
        self.instructionsLabel_2.setGeometry(QtCore.QRect(380, 10, 201, 16))
        self.instructionsLabel_2.setAlignment(QtCore.Qt.AlignCenter)
        self.instructionsLabel_2.setObjectName("instructionsLabel_2")
        self.horizontalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(370, 470, 231, 32))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(
            self.horizontalLayoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.confirmButton = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.confirmButton.setObjectName("confirmButton")
        self.horizontalLayout.addWidget(self.confirmButton)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar()
        self.menubar.setGeometry(QtCore.QRect(0, 0, 651, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QObject.connect(self.selectAllButton, QtCore.SIGNAL("clicked()"),
                               MainWindow.select_all)
        QtCore.QObject.connect(self.deselectAllButton,
                               QtCore.SIGNAL("clicked()"),
                               MainWindow.deselect_all)
        QtCore.QObject.connect(self.refreshButton, QtCore.SIGNAL("clicked()"),
                               MainWindow.refresh)
        QtCore.QObject.connect(self.confirmButton, QtCore.SIGNAL("clicked()"),
                               MainWindow.choose_checked_components)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(
            QtWidgets.QApplication.translate("MainWindow", "Q3D Renderer", None,
                                             -1))
        self.instructionsLabel.setText(
            QtWidgets.QApplication.translate("MainWindow",
                                             "Check off components to export:",
                                             None, -1))
        self.refreshButton.setText(
            QtWidgets.QApplication.translate("MainWindow", "Refresh List", None,
                                             -1))
        self.selectAllButton.setText(
            QtWidgets.QApplication.translate("MainWindow", "Select All", None,
                                             -1))
        self.deselectAllButton.setText(
            QtWidgets.QApplication.translate("MainWindow", "Deselect All", None,
                                             -1))
        self.instructionsLabel_2.setText(
            QtWidgets.QApplication.translate("MainWindow", "Renderer options",
                                             None, -1))
        self.confirmButton.setText(
            QtWidgets.QApplication.translate("MainWindow", "Confirm Selection",
                                             None, -1))


from .tree_view_base import QTreeView_Base
from . import main_window_rc_rc
