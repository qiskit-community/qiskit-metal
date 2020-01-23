# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'component_widget_ui.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ComponentWidget(object):
    def setupUi(self, ComponentWidget):
        ComponentWidget.setObjectName("ComponentWidget")
        ComponentWidget.resize(465, 420)
        ComponentWidget.setTabShape(QtWidgets.QTabWidget.Rounded)
        ComponentWidget.setElideMode(QtCore.Qt.ElideRight)
        self.tabOptions = QtWidgets.QWidget()
        self.tabOptions.setObjectName("tabOptions")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.tabOptions)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.labelComponentName = QtWidgets.QLabel(self.tabOptions)
        self.labelComponentName.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.labelComponentName.setObjectName("labelComponentName")
        self.horizontalLayout.addWidget(self.labelComponentName)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.tableView = QtWidgets.QTableView(self.tabOptions)
        self.tableView.setAlternatingRowColors(True)
        self.tableView.setSortingEnabled(True)
        self.tableView.setObjectName("tableView")
        self.verticalLayout.addWidget(self.tableView)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/options"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        ComponentWidget.addTab(self.tabOptions, icon, "")
        self.tabHelp = QtWidgets.QWidget()
        self.tabHelp.setObjectName("tabHelp")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.tabHelp)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.textEdit = QtWidgets.QTextEdit(self.tabHelp)
        self.textEdit.setObjectName("textEdit")
        self.verticalLayout_2.addWidget(self.textEdit)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/help"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        ComponentWidget.addTab(self.tabHelp, icon1, "")
        self.tabSource = QtWidgets.QWidget()
        self.tabSource.setObjectName("tabSource")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.tabSource)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.textEdit_2 = QtWidgets.QTextEdit(self.tabSource)
        self.textEdit_2.setObjectName("textEdit_2")
        self.verticalLayout_3.addWidget(self.textEdit_2)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/_imgs/support.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        ComponentWidget.addTab(self.tabSource, icon2, "")

        self.retranslateUi(ComponentWidget)
        ComponentWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(ComponentWidget)

    def retranslateUi(self, ComponentWidget):
        _translate = QtCore.QCoreApplication.translate
        ComponentWidget.setWindowTitle(_translate("ComponentWidget", "TabWidget"))
        self.labelComponentName.setText(_translate("ComponentWidget", "Component"))
        ComponentWidget.setTabText(ComponentWidget.indexOf(self.tabOptions), _translate("ComponentWidget", "Options"))
        ComponentWidget.setTabToolTip(ComponentWidget.indexOf(self.tabOptions), _translate("ComponentWidget", "Edit the make options"))
        self.textEdit.setHtml(_translate("ComponentWidget", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:14pt; font-weight:600;\">Here we display the docstring for a component. </span></p></body></html>"))
        ComponentWidget.setTabText(ComponentWidget.indexOf(self.tabHelp), _translate("ComponentWidget", "Help"))
        ComponentWidget.setTabText(ComponentWidget.indexOf(self.tabSource), _translate("ComponentWidget", "Source"))

from . import main_window_rc_rc
