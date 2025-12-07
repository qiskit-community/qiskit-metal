# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './endcap_hfss_ui.ui',
# licensing of './endcap_hfss_ui.ui' applies.
#
# Created: Sat Jun 19 22:02:30 2021
#      by: pyside6-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide6 import QtCore, QtGui, QtWidgets


class Ui_mainWindow(object):

    def setupUi(self, mainWindow):
        mainWindow.setObjectName("mainWindow")
        mainWindow.resize(400, 530)
        self.centralwidget = QtWidgets.QWidget(mainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(10, 10, 271, 20))
        self.label.setObjectName("label")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(130, 450, 131, 32))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.renderButton = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.renderButton.setObjectName("renderButton")
        self.verticalLayout.addWidget(self.renderButton)
        self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self.tableWidget.setGeometry(QtCore.QRect(10, 30, 381, 421))
        self.tableWidget.setSizeAdjustPolicy(
            QtWidgets.QAbstractScrollArea.AdjustIgnored)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        mainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar()
        self.menubar.setGeometry(QtCore.QRect(0, 0, 400, 22))
        self.menubar.setObjectName("menubar")
        mainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(mainWindow)
        self.statusbar.setObjectName("statusbar")
        mainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(mainWindow)
        QtCore.QObject.connect(self.renderButton, QtCore.SIGNAL("clicked()"),
                               mainWindow.render_everything)
        QtCore.QMetaObject.connectSlotsByName(mainWindow)

    def retranslateUi(self, mainWindow):
        mainWindow.setWindowTitle(
            QtWidgets.QApplication.translate("mainWindow", "HFSS Endcaps", None,
                                             -1))
        self.label.setText(
            QtWidgets.QApplication.translate(
                "mainWindow", "Select endcap type for unconnected pins:", None,
                -1))
        self.renderButton.setText(
            QtWidgets.QApplication.translate("mainWindow", "Render", None, -1))
