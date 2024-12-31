# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './component_widget_ui.ui',
# licensing of './component_widget_ui.ui' applies.
#
# Created: Sat Jun 19 22:02:29 2021
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
        self.treeView.setSizeAdjustPolicy(
            QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.treeView.setProperty("showDropIndicator", False)
        self.treeView.setObjectName("treeView")
        self.verticalLayout.addWidget(self.treeView)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/options"), QtGui.QIcon.Normal,
                       QtGui.QIcon.On)
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
        icon1.addPixmap(QtGui.QPixmap(":/help"), QtGui.QIcon.Normal,
                        QtGui.QIcon.On)
        ComponentWidget.addTab(self.tabHelp, icon1, "")
        self.tabSource = QtWidgets.QWidget()
        self.tabSource.setObjectName("tabSource")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.tabSource)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
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
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/_imgs/support.png"),
                        QtGui.QIcon.Normal, QtGui.QIcon.On)
        ComponentWidget.addTab(self.tabSource, icon2, "")

        self.retranslateUi(ComponentWidget)
        ComponentWidget.setCurrentIndex(2)

    def retranslateUi(self, ComponentWidget):
        ComponentWidget.setWindowTitle(
            QtWidgets.QApplication.translate("ComponentWidget",
                                             "Edit a component", None, -1))
        ComponentWidget.setTabText(
            ComponentWidget.indexOf(self.tabOptions),
            QtWidgets.QApplication.translate("ComponentWidget", "Options", None,
                                             -1))
        ComponentWidget.setTabToolTip(
            ComponentWidget.indexOf(self.tabOptions),
            QtWidgets.QApplication.translate("ComponentWidget",
                                             "Edit the make options", None, -1))
        self.textHelp.setHtml(
            QtWidgets.QApplication.translate(
                "ComponentWidget",
                "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
                "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
                "p, li { white-space: pre-wrap; }\n"
                "</style></head><body style=\" font-family:\'.AppleSystemUIFont\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
                "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Arial\'; font-size:14pt;\">Help about a component will be displayed here when you select a component in the design components dialog. </span></p></body></html>",
                None, -1))
        ComponentWidget.setTabText(
            ComponentWidget.indexOf(self.tabHelp),
            QtWidgets.QApplication.translate("ComponentWidget", "Help", None,
                                             -1))
        self.textSource.setHtml(
            QtWidgets.QApplication.translate(
                "ComponentWidget",
                "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
                "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
                "p, li { white-space: pre-wrap; }\n"
                "</style></head><body style=\" font-family:\'.AppleSystemUIFont\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
                "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Arial\'; font-size:14pt;\">The source code of a QComponent class will be displayed here when you select a component in the design components dialog. </span></p></body></html>",
                None, -1))
        self.lineSourcePath.setToolTip(
            QtWidgets.QApplication.translate("ComponentWidget",
                                             "Source code file path", None, -1))
        self.lineSourcePath.setStatusTip(
            QtWidgets.QApplication.translate("ComponentWidget",
                                             "Source code file path", None, -1))
        self.lineSourcePath.setWhatsThis(
            QtWidgets.QApplication.translate("ComponentWidget",
                                             "Source code file path", None, -1))
        self.lineSourcePath.setAccessibleName(
            QtWidgets.QApplication.translate("ComponentWidget",
                                             "Source code file path", None, -1))
        self.lineSourcePath.setAccessibleDescription(
            QtWidgets.QApplication.translate("ComponentWidget",
                                             "Source code file path", None, -1))
        self.lineSourcePath.setText(
            QtWidgets.QApplication.translate("ComponentWidget",
                                             "Source code file path here", None,
                                             -1))
        ComponentWidget.setTabText(
            ComponentWidget.indexOf(self.tabSource),
            QtWidgets.QApplication.translate("ComponentWidget", "Source", None,
                                             -1))


from .widgets.edit_component.tree_view_options import QTreeView_Options
from . import main_window_rc_rc
