# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gds_renderer_ui.ui'
#
# Created by: PyQt5 UI code generator 5.14.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_GDS_Renderer_Window(object):
    def setupUi(self, GDS_Renderer_Window):
        GDS_Renderer_Window.setObjectName("GDS_Renderer_Window")
        GDS_Renderer_Window.resize(707, 581)
        self.centralwidget = QtWidgets.QWidget(GDS_Renderer_Window)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.gridLayout = QtWidgets.QGridLayout(self.tab)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lineEdit = QtWidgets.QLineEdit(self.tab)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout.addWidget(self.lineEdit)
        self.browseButton = QtWidgets.QToolButton(self.tab)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/_imgs/search.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.browseButton.setIcon(icon)
        self.browseButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.browseButton.setAutoRaise(False)
        self.browseButton.setObjectName("browseButton")
        self.horizontalLayout.addWidget(self.browseButton)
        self.exportButton = QtWidgets.QPushButton(self.tab)
        self.exportButton.setObjectName("exportButton")
        self.horizontalLayout.addWidget(self.exportButton)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.tab_2)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.treeView = QtWidgets.QTreeView(self.tab_2)
        self.treeView.setObjectName("treeView")
        self.verticalLayout.addWidget(self.treeView)
        self.tabWidget.addTab(self.tab_2, "")
        self.verticalLayout_2.addWidget(self.tabWidget)
        GDS_Renderer_Window.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(GDS_Renderer_Window)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 707, 22))
        self.menubar.setObjectName("menubar")
        GDS_Renderer_Window.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(GDS_Renderer_Window)
        self.statusbar.setObjectName("statusbar")
        GDS_Renderer_Window.setStatusBar(self.statusbar)

        self.retranslateUi(GDS_Renderer_Window)
        self.tabWidget.setCurrentIndex(0)
        self.browseButton.clicked.connect(GDS_Renderer_Window.browse_files)
        self.exportButton.clicked.connect(GDS_Renderer_Window.export_file)
        QtCore.QMetaObject.connectSlotsByName(GDS_Renderer_Window)

    def retranslateUi(self, GDS_Renderer_Window):
        _translate = QtCore.QCoreApplication.translate
        GDS_Renderer_Window.setWindowTitle(_translate("GDS_Renderer_Window", "GDS_Renderer"))
        self.lineEdit.setPlaceholderText(_translate("GDS_Renderer_Window", "Export GDS to the following location... "))
        self.browseButton.setText(_translate("GDS_Renderer_Window", "Browse"))
        self.exportButton.setText(_translate("GDS_Renderer_Window", "Export"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("GDS_Renderer_Window", "Actions"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("GDS_Renderer_Window", "Options"))
from . import main_window_rc_rc
