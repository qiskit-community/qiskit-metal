# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'component_widget_ui.ui'
#
# Created by: PyQt5 UI code generator 5.14.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ComponentWidget(object):
    def setupUi(self, ComponentWidget):
        ComponentWidget.setObjectName("ComponentWidget")
        ComponentWidget.resize(465, 420)
        ComponentWidget.setTabPosition(QtWidgets.QTabWidget.North)
        self.tabOptions = QtWidgets.QWidget()
        self.tabOptions.setObjectName("tabOptions")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.tabOptions)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.labelComponentName = QtWidgets.QLineEdit(self.tabOptions)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.labelComponentName.setFont(font)
        self.labelComponentName.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.labelComponentName.setAutoFillBackground(False)
        self.labelComponentName.setFrame(False)
        self.labelComponentName.setReadOnly(True)
        self.labelComponentName.setClearButtonEnabled(False)
        self.labelComponentName.setObjectName("labelComponentName")
        self.horizontalLayout.addWidget(self.labelComponentName)
        self.labelComponentName_old = QtWidgets.QLabel(self.tabOptions)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.labelComponentName_old.sizePolicy().hasHeightForWidth())
        self.labelComponentName_old.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.labelComponentName_old.setFont(font)
        self.labelComponentName_old.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.labelComponentName_old.setObjectName("labelComponentName_old")
        self.horizontalLayout.addWidget(self.labelComponentName_old)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.tableView = QtWidgets.QTableView(self.tabOptions)
        self.tableView.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.tableView.setFrameShadow(QtWidgets.QFrame.Plain)
        self.tableView.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.tableView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tableView.setShowGrid(False)
        self.tableView.setObjectName("tableView")
        self.verticalLayout.addWidget(self.tableView)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/options"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        ComponentWidget.addTab(self.tabOptions, icon, "")
        self.tabHelp = QtWidgets.QWidget()
        self.tabHelp.setObjectName("tabHelp")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.tabHelp)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.textHelp = QtWidgets.QTextEdit(self.tabHelp)
        self.textHelp.setObjectName("textHelp")
        self.verticalLayout_2.addWidget(self.textHelp)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/help"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        ComponentWidget.addTab(self.tabHelp, icon1, "")
        self.tabSource = QtWidgets.QWidget()
        self.tabSource.setObjectName("tabSource")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.tabSource)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.btn_edit_src = QtWidgets.QPushButton(self.tabSource)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.btn_edit_src.setFont(font)
        self.btn_edit_src.setAutoFillBackground(False)
        self.btn_edit_src.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgb(61, 217, 245), stop:1 rgb(240, 53, 218));\n"
"border-style: solid;\n"
"border-radius:30px;\n"
"font-weight: bold;\n"
"color: rgb(255, 255, 255);")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/save"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btn_edit_src.setIcon(icon2)
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
        self.btn_edit_src.clicked.connect(ComponentWidget.edit_source)
        QtCore.QMetaObject.connectSlotsByName(ComponentWidget)

    def retranslateUi(self, ComponentWidget):
        _translate = QtCore.QCoreApplication.translate
        ComponentWidget.setWindowTitle(_translate("ComponentWidget", "Edit a component"))
        self.labelComponentName.setPlaceholderText(_translate("ComponentWidget", "Select component from design panel to edit its options here"))
        self.labelComponentName_old.setText(_translate("ComponentWidget", "Component Name"))
        ComponentWidget.setTabText(ComponentWidget.indexOf(self.tabOptions), _translate("ComponentWidget", "Options"))
        ComponentWidget.setTabToolTip(ComponentWidget.indexOf(self.tabOptions), _translate("ComponentWidget", "Edit the make options"))
        self.textHelp.setHtml(_translate("ComponentWidget", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.SF NS Text\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:14pt;\">Help about a component will be displayed here when you select a compoent in the design components dialog. </span></p></body></html>"))
        ComponentWidget.setTabText(ComponentWidget.indexOf(self.tabHelp), _translate("ComponentWidget", "Help"))
        self.btn_edit_src.setText(_translate("ComponentWidget", "Edit Source"))
        self.textSource.setHtml(_translate("ComponentWidget", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.SF NS Text\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:14pt;\">The source code of a coomponent class will be displayed here when you select a compoent in the design components dialog. </span></p></body></html>"))
        self.lineSourcePath.setToolTip(_translate("ComponentWidget", "Source code file path"))
        self.lineSourcePath.setStatusTip(_translate("ComponentWidget", "Source code file path"))
        self.lineSourcePath.setWhatsThis(_translate("ComponentWidget", "Source code file path"))
        self.lineSourcePath.setAccessibleName(_translate("ComponentWidget", "Source code file path"))
        self.lineSourcePath.setAccessibleDescription(_translate("ComponentWidget", "Source code file path"))
        self.lineSourcePath.setText(_translate("ComponentWidget", "Source code file path here"))
        ComponentWidget.setTabText(ComponentWidget.indexOf(self.tabSource), _translate("ComponentWidget", "Source"))
from . import main_window_rc_rc
