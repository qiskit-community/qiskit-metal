# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './component_widget_ui.ui',
# licensing of './component_widget_ui.ui' applies.
#
# Created: Wed Feb 10 12:49:05 2021
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_ComponentWidget(object):
    def setupUi(self, ComponentWidget):
        ComponentWidget.setObjectName("ComponentWidget")
        ComponentWidget.resize(539, 475)
        ComponentWidget.setTabPosition(QtWidgets.QTabWidget.West)
        ComponentWidget.setTabShape(QtWidgets.QTabWidget.Triangular)
        ComponentWidget.setMovable(True)
        self.tabOptions = QtWidgets.QWidget()
        self.tabOptions.setObjectName("tabOptions")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.tabOptions)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(-1, -1, -1, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.treeView = QTreeView_Options(self.tabOptions)
        self.treeView.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.treeView.setFrameShadow(QtWidgets.QFrame.Plain)
        self.treeView.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.treeView.setProperty("showDropIndicator", False)
        self.treeView.setObjectName("treeView")
        self.verticalLayout.addWidget(self.treeView)
        self.pushButtonEditSource = QtWidgets.QPushButton(self.tabOptions)
        self.pushButtonEditSource.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(61, 217, 245,0.8), stop:1 rgba(240, 53, 218,0.8));\n"
"border-style: solid;\n"
"border-radius:30px;\n"
"font-weight: bold;\n"
"color: rgb(255, 255, 255);")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/---component"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButtonEditSource.setIcon(icon)
        self.pushButtonEditSource.setObjectName("pushButtonEditSource")
        self.verticalLayout.addWidget(self.pushButtonEditSource)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/options"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        ComponentWidget.addTab(self.tabOptions, icon1, "")
        self.tabHelp = QtWidgets.QWidget()
        self.tabHelp.setObjectName("tabHelp")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.tabHelp)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.textHelp = QtWidgets.QTextEdit(self.tabHelp)
        self.textHelp.setObjectName("textHelp")
        self.verticalLayout_2.addWidget(self.textHelp)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/help"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        ComponentWidget.addTab(self.tabHelp, icon2, "")
        self.tabSource = QtWidgets.QWidget()
        self.tabSource.setObjectName("tabSource")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.tabSource)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.btn_edit_src = QtWidgets.QPushButton(self.tabSource)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setWeight(75)
        font.setBold(True)
        self.btn_edit_src.setFont(font)
        self.btn_edit_src.setAutoFillBackground(False)
        self.btn_edit_src.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgb(61, 217, 245), stop:1 rgb(240, 53, 218));\n"
"border-style: solid;\n"
"border-radius:30px;\n"
"font-weight: bold;\n"
"color: rgb(255, 255, 255);")
        self.btn_edit_src.setIcon(icon)
        self.btn_edit_src.setIconSize(QtCore.QSize(20, 20))
        self.btn_edit_src.setDefault(False)
        self.btn_edit_src.setFlat(False)
        self.btn_edit_src.setObjectName("btn_edit_src")
        self.verticalLayout_3.addWidget(self.btn_edit_src)
        self.textSource = QtWidgets.QTextEdit(self.tabSource)
        self.textSource.setAutoFillBackground(True)
        self.textSource.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.textSource.setObjectName("textSource")
        self.verticalLayout_3.addWidget(self.textSource)
        self.lineSourcePath = QtWidgets.QLineEdit(self.tabSource)
        self.lineSourcePath.setReadOnly(True)
        self.lineSourcePath.setClearButtonEnabled(False)
        self.lineSourcePath.setObjectName("lineSourcePath")
        self.verticalLayout_3.addWidget(self.lineSourcePath)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/_imgs/support.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        ComponentWidget.addTab(self.tabSource, icon3, "")

        self.retranslateUi(ComponentWidget)
        ComponentWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(ComponentWidget)

    def retranslateUi(self, ComponentWidget):
        ComponentWidget.setWindowTitle(QtWidgets.QApplication.translate("ComponentWidget", "Edit a component", None, -1))
        self.pushButtonEditSource.setStatusTip(QtWidgets.QApplication.translate("ComponentWidget", "Edit the QComponent source code in real time and see changes. ", None, -1))
        self.pushButtonEditSource.setWhatsThis(QtWidgets.QApplication.translate("ComponentWidget", "Edit the QComponent source code in real time and see changes. ", None, -1))
        self.pushButtonEditSource.setText(QtWidgets.QApplication.translate("ComponentWidget", "Edit Source", None, -1))
        ComponentWidget.setTabText(ComponentWidget.indexOf(self.tabOptions), QtWidgets.QApplication.translate("ComponentWidget", "Options", None, -1))
        ComponentWidget.setTabToolTip(ComponentWidget.indexOf(self.tabOptions), QtWidgets.QApplication.translate("ComponentWidget", "Edit the make options", None, -1))
        self.textHelp.setHtml(QtWidgets.QApplication.translate("ComponentWidget", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Arial\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:14pt;\">Help about a component will be displayed here when you select a compoent in the design components dialog. </span></p></body></html>", None, -1))
        ComponentWidget.setTabText(ComponentWidget.indexOf(self.tabHelp), QtWidgets.QApplication.translate("ComponentWidget", "Help", None, -1))
        self.btn_edit_src.setText(QtWidgets.QApplication.translate("ComponentWidget", "Edit Source", None, -1))
        self.textSource.setHtml(QtWidgets.QApplication.translate("ComponentWidget", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Arial\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:14pt;\">The source code of a QComponent class will be displayed here when you select a compoent in the design components dialog. </span></p></body></html>", None, -1))
        self.lineSourcePath.setToolTip(QtWidgets.QApplication.translate("ComponentWidget", "Source code file path", None, -1))
        self.lineSourcePath.setStatusTip(QtWidgets.QApplication.translate("ComponentWidget", "Source code file path", None, -1))
        self.lineSourcePath.setWhatsThis(QtWidgets.QApplication.translate("ComponentWidget", "Source code file path", None, -1))
        self.lineSourcePath.setAccessibleName(QtWidgets.QApplication.translate("ComponentWidget", "Source code file path", None, -1))
        self.lineSourcePath.setAccessibleDescription(QtWidgets.QApplication.translate("ComponentWidget", "Source code file path", None, -1))
        self.lineSourcePath.setText(QtWidgets.QApplication.translate("ComponentWidget", "Source code file path here", None, -1))
        ComponentWidget.setTabText(ComponentWidget.indexOf(self.tabSource), QtWidgets.QApplication.translate("ComponentWidget", "Source", None, -1))

from .widgets.edit_component.tree_view_options import QTreeView_Options
from . import main_window_rc_rc
