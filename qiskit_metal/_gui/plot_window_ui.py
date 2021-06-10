# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './plot_window_ui.ui',
# licensing of './plot_window_ui.ui' applies.
#
# Created: Mon Jun  7 17:21:01 2021
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets


class Ui_MainWindowPlot(object):

    def setupUi(self, MainWindowPlot):
        MainWindowPlot.setObjectName("MainWindowPlot")
        MainWindowPlot.resize(800, 600)
        MainWindowPlot.setIconSize(QtCore.QSize(24, 24))
        self.centralwidget = QtWidgets.QWidget(MainWindowPlot)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        MainWindowPlot.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar()
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        MainWindowPlot.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindowPlot)
        self.statusbar.setEnabled(True)
        self.statusbar.setObjectName("statusbar")
        MainWindowPlot.setStatusBar(self.statusbar)
        self.toolBar = QToolBarExpanding(MainWindowPlot)
        self.toolBar.setIconSize(QtCore.QSize(20, 20))
        self.toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.toolBar.setObjectName("toolBar")
        MainWindowPlot.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.actionPan = QtWidgets.QAction(MainWindowPlot)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/plot/pan"), QtGui.QIcon.Normal,
                       QtGui.QIcon.On)
        self.actionPan.setIcon(icon)
        self.actionPan.setObjectName("actionPan")
        self.actionZoom = QtWidgets.QAction(MainWindowPlot)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/plot/zoom"), QtGui.QIcon.Normal,
                        QtGui.QIcon.Off)
        self.actionZoom.setIcon(icon1)
        self.actionZoom.setObjectName("actionZoom")
        self.actionConnectors = QtWidgets.QAction(MainWindowPlot)
        self.actionConnectors.setCheckable(True)
        self.actionConnectors.setChecked(False)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/connectors"), QtGui.QIcon.Normal,
                        QtGui.QIcon.Off)
        self.actionConnectors.setIcon(icon2)
        self.actionConnectors.setObjectName("actionConnectors")
        self.actionCoords = QtWidgets.QAction(MainWindowPlot)
        self.actionCoords.setCheckable(True)
        self.actionCoords.setChecked(True)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/plot/point"), QtGui.QIcon.Normal,
                        QtGui.QIcon.Off)
        self.actionCoords.setIcon(icon3)
        self.actionCoords.setObjectName("actionCoords")
        self.actionAuto = QtWidgets.QAction(MainWindowPlot)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/plot/autozoom"), QtGui.QIcon.Normal,
                        QtGui.QIcon.Off)
        self.actionAuto.setIcon(icon4)
        self.actionAuto.setObjectName("actionAuto")
        self.actionReplot = QtWidgets.QAction(MainWindowPlot)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/plot/refresh_plot"),
                        QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionReplot.setIcon(icon5)
        self.actionReplot.setObjectName("actionReplot")
        self.actionRuler = QtWidgets.QAction(MainWindowPlot)
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(":/plot/ruler"), QtGui.QIcon.Normal,
                        QtGui.QIcon.Off)
        self.actionRuler.setIcon(icon6)
        self.actionRuler.setObjectName("actionRuler")
        self.toolBar.addAction(self.actionPan)
        self.toolBar.addAction(self.actionAuto)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionCoords)
        self.toolBar.addAction(self.actionConnectors)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionRuler)

        self.retranslateUi(MainWindowPlot)
        QtCore.QObject.connect(self.actionAuto, QtCore.SIGNAL("triggered()"),
                               MainWindowPlot.auto_scale)
        QtCore.QObject.connect(self.actionConnectors,
                               QtCore.SIGNAL("triggered(bool)"),
                               MainWindowPlot.set_show_pins)
        QtCore.QObject.connect(self.actionCoords,
                               QtCore.SIGNAL("triggered(bool)"),
                               MainWindowPlot.set_position_track)
        QtCore.QObject.connect(self.actionPan, QtCore.SIGNAL("triggered()"),
                               MainWindowPlot.pan)
        QtCore.QObject.connect(self.actionZoom, QtCore.SIGNAL("triggered()"),
                               MainWindowPlot.zoom)
        QtCore.QObject.connect(self.actionReplot, QtCore.SIGNAL("triggered()"),
                               MainWindowPlot.replot)
        QtCore.QMetaObject.connectSlotsByName(MainWindowPlot)

    def retranslateUi(self, MainWindowPlot):
        MainWindowPlot.setWindowTitle(
            QtWidgets.QApplication.translate("MainWindowPlot", "MainWindow",
                                             None, -1))
        self.toolBar.setWindowTitle(
            QtWidgets.QApplication.translate("MainWindowPlot", "toolBar", None,
                                             -1))
        self.actionPan.setText(
            QtWidgets.QApplication.translate("MainWindowPlot", "Help", None,
                                             -1))
        self.actionPan.setShortcut(
            QtWidgets.QApplication.translate("MainWindowPlot", "P", None, -1))
        self.actionZoom.setText(
            QtWidgets.QApplication.translate("MainWindowPlot", "Zoom", None,
                                             -1))
        self.actionZoom.setToolTip(
            QtWidgets.QApplication.translate("MainWindowPlot", "Zoom control",
                                             None, -1))
        self.actionZoom.setShortcut(
            QtWidgets.QApplication.translate("MainWindowPlot", "Z", None, -1))
        self.actionConnectors.setText(
            QtWidgets.QApplication.translate("MainWindowPlot", "Pins", None,
                                             -1))
        self.actionConnectors.setToolTip(
            QtWidgets.QApplication.translate(
                "MainWindowPlot",
                "Show connector pins for selected qcomponents", None, -1))
        self.actionConnectors.setShortcut(
            QtWidgets.QApplication.translate("MainWindowPlot", "C", None, -1))
        self.actionCoords.setText(
            QtWidgets.QApplication.translate("MainWindowPlot", "Get point",
                                             None, -1))
        self.actionCoords.setToolTip(
            QtWidgets.QApplication.translate(
                "MainWindowPlot",
                "Click for position --- Enable this to click on the plot and log the (x,y) position",
                None, -1))
        self.actionCoords.setShortcut(
            QtWidgets.QApplication.translate("MainWindowPlot", "P", None, -1))
        self.actionAuto.setText(
            QtWidgets.QApplication.translate("MainWindowPlot", "Autoscale",
                                             None, -1))
        self.actionAuto.setToolTip(
            QtWidgets.QApplication.translate("MainWindowPlot", "Auto Zoom",
                                             None, -1))
        self.actionAuto.setShortcut(
            QtWidgets.QApplication.translate("MainWindowPlot", "A", None, -1))
        self.actionReplot.setText(
            QtWidgets.QApplication.translate("MainWindowPlot", "Replot", None,
                                             -1))
        self.actionReplot.setShortcut(
            QtWidgets.QApplication.translate("MainWindowPlot", "Ctrl+R", None,
                                             -1))
        self.actionRuler.setText(
            QtWidgets.QApplication.translate("MainWindowPlot", "Ruler", None,
                                             -1))
        self.actionRuler.setToolTip(
            QtWidgets.QApplication.translate("MainWindowPlot",
                                             "Activate the ruler", None, -1))


from .widgets.bases.expanding_toolbar import QToolBarExpanding
from . import main_window_rc_rc
