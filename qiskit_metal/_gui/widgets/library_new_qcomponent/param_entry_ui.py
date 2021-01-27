# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './widgets/library_new_qcomponent/param_entry_ui.ui',
# licensing of './widgets/library_new_qcomponent/param_entry_ui.ui' applies.
#
# Created: Wed Jan 27 15:02:20 2021
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_dict_entry_widget(object):
    def setupUi(self, dict_entry_widget):
        dict_entry_widget.setObjectName("dict_entry_widget")
        dict_entry_widget.resize(1536, 850)
        self.horizontalLayout = QtWidgets.QHBoxLayout(dict_entry_widget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.param_name = QtWidgets.QLineEdit(dict_entry_widget)
        self.param_name.setObjectName("param_name")
        self.horizontalLayout.addWidget(self.param_name)
        self.equals = QtWidgets.QLabel(dict_entry_widget)
        self.equals.setObjectName("equals")
        self.horizontalLayout.addWidget(self.equals)
        self.param_value = QtWidgets.QLineEdit(dict_entry_widget)
        self.param_value.setObjectName("param_value")
        self.horizontalLayout.addWidget(self.param_value)

        self.retranslateUi(dict_entry_widget)
        QtCore.QMetaObject.connectSlotsByName(dict_entry_widget)

    def retranslateUi(self, dict_entry_widget):
        dict_entry_widget.setWindowTitle(QtWidgets.QApplication.translate("dict_entry_widget", "Form", None, -1))
        self.equals.setText(QtWidgets.QApplication.translate("dict_entry_widget", "=", None, -1))

