# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './elements_ui.ui',
# licensing of './elements_ui.ui' applies.
#
# Created: Thu Jun 30 16:30:20 2022
#      by: pyside6-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide6 import QtCore, QtGui, QtWidgets


class Ui_ElementsWindow(object):

    def setupUi(self, ElementsWindow):
        ElementsWindow.setObjectName("ElementsWindow")
        ElementsWindow.resize(841, 623)
        self.centralwidget = QtWidgets.QWidget(ElementsWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSizeConstraint(
            QtWidgets.QLayout.SetDefaultConstraint)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btn_refresh = QtWidgets.QPushButton(self.centralwidget)
        self.btn_refresh.setCursor(QtCore.Qt.ClosedHandCursor)
        self.btn_refresh.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/refresh"), QtGui.QIcon.Normal,
                       QtGui.QIcon.Off)
        self.btn_refresh.setIcon(icon)
        self.btn_refresh.setIconSize(QtCore.QSize(20, 20))
        self.btn_refresh.setAutoDefault(False)
        self.btn_refresh.setDefault(False)
        self.btn_refresh.setFlat(True)
        self.btn_refresh.setObjectName("btn_refresh")
        self.horizontalLayout.addWidget(self.btn_refresh)
        self.label = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                           QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setLegacyWeight(75)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing |
                                QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.combo_element_type = QtWidgets.QComboBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                           QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.combo_element_type.sizePolicy().hasHeightForWidth())
        self.combo_element_type.setSizePolicy(sizePolicy)
        self.combo_element_type.setCurrentText("")
        self.combo_element_type.setSizeAdjustPolicy(
            QtWidgets.QComboBox.AdjustToContents)
        self.combo_element_type.setObjectName("combo_element_type")
        self.horizontalLayout.addWidget(self.combo_element_type)
        self.line = QtWidgets.QFrame(self.centralwidget)
        self.line.setFrameShape(QtWidgets.QFrame.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.horizontalLayout.addWidget(self.line)
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setLegacyWeight(75)
        font.setBold(True)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout.addWidget(self.lineEdit)
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout.addWidget(self.label_4)
        self.lineEdit_2 = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.horizontalLayout.addWidget(self.lineEdit_2)
        self.line_2 = QtWidgets.QFrame(self.centralwidget)
        self.line_2.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.horizontalLayout.addWidget(self.line_2)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.tableElements = QtWidgets.QTableView(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.tableElements.sizePolicy().hasHeightForWidth())
        self.tableElements.setSizePolicy(sizePolicy)
        self.tableElements.setProperty("showDropIndicator", False)
        self.tableElements.setDragDropOverwriteMode(False)
        self.tableElements.setAlternatingRowColors(True)
        self.tableElements.setSortingEnabled(False)
        self.tableElements.setObjectName("tableElements")
        self.verticalLayout.addWidget(self.tableElements)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        ElementsWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar()
        self.menubar.setGeometry(QtCore.QRect(0, 0, 841, 24))
        self.menubar.setObjectName("menubar")
        ElementsWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(ElementsWindow)
        self.statusbar.setEnabled(True)
        self.statusbar.setObjectName("statusbar")
        ElementsWindow.setStatusBar(self.statusbar)

        self.retranslateUi(ElementsWindow)
        QtCore.QObject.connect(self.combo_element_type,
                               QtCore.SIGNAL("currentIndexChanged(QString)"),
                               ElementsWindow.combo_element_type)
        QtCore.QObject.connect(self.btn_refresh, QtCore.SIGNAL("clicked()"),
                               ElementsWindow.force_refresh)
        QtCore.QMetaObject.connectSlotsByName(ElementsWindow)

    def retranslateUi(self, ElementsWindow):
        ElementsWindow.setWindowTitle(
            QtWidgets.QApplication.translate("ElementsWindow", "MainWindow",
                                             None, -1))
        self.btn_refresh.setToolTip(
            QtWidgets.QApplication.translate("ElementsWindow",
                                             "Force refresh the table ", None,
                                             -1))
        self.btn_refresh.setStatusTip(
            QtWidgets.QApplication.translate("ElementsWindow",
                                             "Force refresh the table ", None,
                                             -1))
        self.btn_refresh.setWhatsThis(
            QtWidgets.QApplication.translate("ElementsWindow",
                                             "Force refresh the table ", None,
                                             -1))
        self.btn_refresh.setAccessibleDescription(
            QtWidgets.QApplication.translate("ElementsWindow",
                                             "Force refresh the table ", None,
                                             -1))
        self.label.setText(
            QtWidgets.QApplication.translate("ElementsWindow",
                                             "QGeometry type: ", None, -1))
        self.combo_element_type.setToolTip(
            QtWidgets.QApplication.translate(
                "ElementsWindow",
                "<html><head/><body><p>Select the element table you wish to view</p></body></html>",
                None, -1))
        self.label_3.setText(
            QtWidgets.QApplication.translate("ElementsWindow", "  Filter:  ",
                                             None, -1))
        self.label_2.setText(
            QtWidgets.QApplication.translate("ElementsWindow", "Component: ",
                                             None, -1))
        self.label_4.setText(
            QtWidgets.QApplication.translate("ElementsWindow", "  Layer:  ",
                                             None, -1))


from qiskit_metal._gui import main_window_rc_rc
