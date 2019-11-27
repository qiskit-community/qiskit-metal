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
#

"""
Handle params for Creating an an object

@date: 2019
@author: Zlatko K. Minev
"""

import ast
import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem, QIntValidator
from PyQt5.QtWidgets import QApplication, QWidget, QTreeView, QDockWidget
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QMainWindow, QListWidget
from PyQt5.QtWidgets import QTextEdit, QTreeWidget, QTreeWidgetItem, QLineEdit
from PyQt5.QtWidgets import QToolBar, QAction, QSlider, QInputDialog, QMessageBox
from PyQt5.QtWidgets import QLabel

from .... import logger
from ..._handle_qt_messages import catch_exception_slot_pyqt, do_debug

###########################################################################################


class Parameter_Zlatko(QLineEdit):
    '''
    Monkey patch:
        widget.get_obj= get_obj.__get__(widget, widget_class)
    '''

    def __init__(self, _components, names, obj,
                 on_return=None, logger=None):

        super().__init__()

        self._components = _components  # reference to dictionary of atributes
        self.names = names.copy()
        self.name = self.names.pop(-1)
        self.type = type(obj)
        self.logger = logger

        self.update_widget_from_value()
        self.editingFinished.connect(self.update_value_from_widget)
        if on_return:
            self._on_return = on_return
            self.returnPressed.connect(self.act_on_return)
        self.style_widget()

    @staticmethod
    def I_can_handle_this_type(obj):
        if isinstance(obj, str) or isinstance_number(obj) or isinstance(obj, list):
            return True
        else:
            return False

    def style_widget(self):
        self.setStyleSheet(
            """color: #115511; border:0; selection-background-color: darkgray;""")

    def get_obj(self):
        _obj = self._components
        for key in self.names:
            #assert key in _obj
            if isinstance(_obj, dict):
                _obj = _obj[key]
            else:  # assume object
                _obj = getattr(_obj, key)
        return _obj

    def get_obj_str(self):
        return f"objects.{'.'.join(self.names)}.{self.name}"

    def get_value(self):
        '''
        Variable literal value.
        '''
        _obj = self.get_obj()
        return _obj[self.name]

    @catch_exception_slot_pyqt()
    def act_on_return(self):
        if self._on_return:
            # print('act_on_return')
            self.update_value_from_widget()
            self._on_return()

    @catch_exception_slot_pyqt()
    def update_value_from_widget(self):
        """
        Callback on change to update the value of the object item

        Keyword Arguments:
            _print {bool} -- [description] (default: {True})
        """
        _obj = self.get_obj()
        _new_val = str(self.text()).strip()
        _old_val = str(_obj[self.name]).strip()

        if _old_val != _new_val:
            # _obj[self.name] = self.type(_new_val) # type convert to original type - this could actually cause issues
            # TODO: Maybe try and catch error here
            # this wil be more flexible and prevent issue with getting forced to ints for example and then wanting to swtch to floats
            v, used_ast = parse_param_from_str(_new_val)
            _obj[self.name] = v

            msg = f"  {'.'.join(self.names)}.{self.name}=`{_new_val}` old=`{_old_val}` used_ast={used_ast}"
            #do_debug(msg)


    def update_widget_from_value(self):
        self.setText(str(self.get_obj()[self.name]).strip())


def parse_param_from_str(text):
    text = str(text).strip()
    value = text
    used_ast = False
    try:  # crude way to handle list and values
        value = ast.literal_eval(text)
        used_ast = True
    except Exception as exception:
        pass
        # print(exception)
    return value, used_ast


def isinstance_number(obj):
    return any(map(lambda x: isinstance(obj, x),
                   [int, float, np.int, np.float, np.int64, np.float64, np.long, np.integer]))
