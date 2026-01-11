# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './widgets/create_component_window/parameter_entry_window_ui.ui',
# licensing of './widgets/create_component_window/parameter_entry_window_ui.ui' applies.
#
# Created: Sat Jun 19 22:02:30 2021
#      by: pyside6-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(753, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.explanatory_label = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                           QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(
            self.explanatory_label.sizePolicy().hasHeightForWidth())
        self.explanatory_label.setSizePolicy(sizePolicy)
        self.explanatory_label.setObjectName("explanatory_label")
        self.verticalLayout_2.addWidget(self.explanatory_label)
        self.widget = QtWidgets.QWidget(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                           QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(20)
        sizePolicy.setHeightForWidth(
            self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setObjectName("widget")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.edit_box = QtWidgets.QWidget(self.widget)
        self.edit_box.setObjectName("edit_box")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.edit_box)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.widget_3 = QtWidgets.QWidget(self.edit_box)
        self.widget_3.setObjectName("widget_3")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.widget_3)
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.add_k_v_row_button = QtWidgets.QPushButton(self.widget_3)
        self.add_k_v_row_button.setObjectName("add_k_v_row_button")
        self.horizontalLayout_5.addWidget(self.add_k_v_row_button)
        self.nest_dictionary_button = QtWidgets.QPushButton(self.widget_3)
        self.nest_dictionary_button.setObjectName("nest_dictionary_button")
        self.horizontalLayout_5.addWidget(self.nest_dictionary_button)
        self.remove_button = QtWidgets.QPushButton(self.widget_3)
        self.remove_button.setObjectName("remove_button")
        self.horizontalLayout_5.addWidget(self.remove_button)
        self.verticalLayout_4.addWidget(self.widget_3)
        self.qcomponent_param_tree_view = TreeViewParamEntry(self.edit_box)
        self.qcomponent_param_tree_view.setObjectName(
            "qcomponent_param_tree_view")
        self.verticalLayout_4.addWidget(self.qcomponent_param_tree_view)
        self.parameter_entry_form = QtWidgets.QWidget(self.edit_box)
        self.parameter_entry_form.setObjectName("parameter_entry_form")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.parameter_entry_form)
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.verticalLayout_4.addWidget(self.parameter_entry_form)
        self.create_qcomp_button = QtWidgets.QPushButton(self.edit_box)
        self.create_qcomp_button.setObjectName("create_qcomp_button")
        self.verticalLayout_4.addWidget(self.create_qcomp_button)
        self.horizontalLayout_4.addWidget(self.edit_box)
        self.help_box = QtWidgets.QWidget(self.widget)
        self.help_box.setObjectName("help_box")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.help_box)
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.help_button_holder = QtWidgets.QWidget(self.help_box)
        self.help_button_holder.setObjectName("help_button_holder")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.help_button_holder)
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.verticalLayout_5.addWidget(self.help_button_holder)
        self.help_tab_tabWidget = QtWidgets.QTabWidget(self.help_box)
        self.help_tab_tabWidget.setObjectName("help_tab_tabWidget")
        self.tab_source = QtWidgets.QWidget()
        self.tab_source.setObjectName("tab_source")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.tab_source)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.help_tab_tabWidget.addTab(self.tab_source, "")
        self.tab_help = QtWidgets.QWidget()
        self.tab_help.setObjectName("tab_help")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout(self.tab_help)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.help_tab_tabWidget.addTab(self.tab_help, "")
        self.verticalLayout_5.addWidget(self.help_tab_tabWidget)
        self.horizontalLayout_4.addWidget(self.help_box)
        self.verticalLayout_2.addWidget(self.widget)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.help_tab_tabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(
            QtWidgets.QApplication.translate("MainWindow", "MainWindow", None,
                                             -1))
        self.explanatory_label.setText(
            QtWidgets.QApplication.translate("MainWindow",
                                             "Options to create with", None,
                                             -1))
        self.add_k_v_row_button.setText(
            QtWidgets.QApplication.translate("MainWindow", "Add Row", None, -1))
        self.nest_dictionary_button.setText(
            QtWidgets.QApplication.translate("MainWindow", "Nest Dictionary",
                                             None, -1))
        self.remove_button.setText(
            QtWidgets.QApplication.translate("MainWindow", "Remove", None, -1))
        self.create_qcomp_button.setText(
            QtWidgets.QApplication.translate("MainWindow", "Create", None, -1))
        self.help_tab_tabWidget.setTabText(
            self.help_tab_tabWidget.indexOf(self.tab_source),
            QtWidgets.QApplication.translate("MainWindow", "Source", None, -1))
        self.help_tab_tabWidget.setTabText(
            self.help_tab_tabWidget.indexOf(self.tab_help),
            QtWidgets.QApplication.translate("MainWindow", "Help", None, -1))


from qiskit_metal._gui.widgets.create_component_window.model_view.tree_view_param_entry import TreeViewParamEntry
