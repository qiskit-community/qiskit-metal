# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Created on Tue May 14 17:13:40 2019

@author: Zlatko
"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction

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
