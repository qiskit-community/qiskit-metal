# -*- coding: utf-8 -*-
"""
Created on Tue May 14 17:13:40 2019

Icon credits:
    Freepik and FlatIcon
    Make Metal:
        https://www.flaticon.com/free-icon/gears_305098
    Delte all Objects:
        no longer used: https://www.flaticon.com/free-icon/clear-button_60994#term=clear&page=1&position=3
        trash icon: https://www.flaticon.com/de/kostenloses-icon/loschen_1214428
    Save:
        https://www.flaticon.com/free-icon/save_174314#term=save%20circular&page=1&position=7
    Freepik:
        <div>Icons made by <a href="https://www.flaticon.com/authors/freepik" title="Freepik">Freepik</a> from <a href="https://www.flaticon.com/"             title="Flaticon">www.flaticon.com</a> is licensed by <a href="http://creativecommons.org/licenses/by/3.0/"             title="Creative Commons BY 3.0" target="_blank">CC 3.0 BY</a></div>
    Open:
        https://www.flaticon.com/free-icon/open-book_234647#term=open%20circular&page=1&position=2
@author: Zlatko
"""
from PyQt5.QtCore import Qt
#from PyQt5 import QtCore, QtGui, QtWidgets
#from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QIcon #, QStandardItemModel, QStandardItem, QIntValidator
#from PyQt5.QtWidgets import QApplication, QWidget, QTreeView, QDockWidget
#from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QMainWindow, QListWidget
#from PyQt5.QtWidgets import QTextEdit, QTreeWidget, QTreeWidgetItem, QLineEdit
from PyQt5.QtWidgets import QAction#, QToolBar, QSlider, QInputDialog, QMessageBox
#from PyQt5.QtWidgets import QLabel

from .._handle_qt_messages import catch_exception_slot_pyqt

def add_toolbar_icon(toolbar, name, icon_path, call_func,
                     tool_tip=None, shortcut=None, menu=None,
                     label = None,
                     style = None):
    """[Helper funciton to make toolbar buttons]

    Arguments:
        toolbar {[type]} -- [description]
        name {[type]} -- [description]
        icon_path {[type]} -- [description]
        call_func {[type]} -- [description]

    Keyword Arguments:
        tool_tip {[str]} -- [description] (default: {None})
        shortcut {[str]} -- [description] (default: {None})
        menu {[QMenu]} -- [description] (default: {None})
        label {[str]} -- [description] (default: {None})
        style {[dict]} -- [description] (default: {None})
    """
    # Maybe use QToolButton

    if tool_tip is None:
        tool_tip = name

    label = label if label else name

    if icon_path:
        # Constructs an action with an icon and some text and parent.
        # If parent is an action group the action will be automatically
        # inserted into the group.
        action = QAction(QIcon(str(icon_path)), label, toolbar)
    else:
        action = QAction(label, toolbar)

    # shorcut
    if shortcut:
        action.setShortcut(shortcut)
        action.setShortcutContext(Qt.WindowShortcut)
        tool_tip += f' (Shortcut: {shortcut})'

    # tooltip
    action.setToolTip(tool_tip)
    action.setStatusTip(tool_tip)

    # call function - wrap to handle exceptions
    call_func_wrapped = catch_exception_slot_pyqt()(call_func)
    action.triggered.connect(call_func_wrapped)

    # Add to toolbar
    toolbar.addAction(action)

    # keep the object reference alive in the parent
    setattr(toolbar, name, action)
    setattr(action, 'call_func_wrapped', call_func_wrapped)

    # Style:
    if style:
        pass

    if menu:
        menu.addAction(action)

    return action
