# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './widgets/variable_table/dialog_popup_ui.ui',
# licensing of './widgets/variable_table/dialog_popup_ui.ui' applies.
#
# Created: Sat Jun 19 22:02:31 2021
#      by: pyside6-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide6 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):

    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.NonModal)
        Dialog.resize(224, 158)
        self.layoutWidget = QtWidgets.QWidget(Dialog)
        self.layoutWidget.setGeometry(QtCore.QRect(20, 30, 179, 101))
        self.layoutWidget.setObjectName("layoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.layoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(self.layoutWidget)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.key_box = QtWidgets.QLineEdit(self.layoutWidget)
        self.key_box.setObjectName("key_box")
        self.gridLayout.addWidget(self.key_box, 0, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.layoutWidget)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.value_box = QtWidgets.QLineEdit(self.layoutWidget)
        self.value_box.setObjectName("value_box")
        self.gridLayout.addWidget(self.value_box, 1, 1, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(self.layoutWidget)
        self.buttonBox.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel |
                                          QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 2)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"),
                               Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"),
                               Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(
            QtWidgets.QApplication.translate("Dialog", "Dialog", None, -1))
        self.label.setText(
            QtWidgets.QApplication.translate("Dialog", "Property", None, -1))
        self.label_2.setText(
            QtWidgets.QApplication.translate("Dialog", "Value", None, -1))
