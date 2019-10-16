# -*- coding: utf-8 -*-
"""
Created 2019
@author: Zlatko K. Minev
"""

#import ast
#import numpy as np

from PyQt5 import QtGui #QtCore, QtWidgets
#from PyQt5.QtCore import Qt, QDir
#from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem, QIntValidator
#from PyQt5.QtWidgets import QApplication, QWidget, QTreeView, QDockWidget
#from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QMainWindow, QListWidget
#from PyQt5.QtWidgets import QTextEdit, QTreeWidget, QTreeWidgetItem, QLineEdit
#from PyQt5.QtWidgets import QToolBar, QAction, QSlider, QInputDialog, QMessageBox
#from PyQt5.QtWidgets import QLabel

#from .... import logger
#from ..._handle_qt_messages import catch_exception_slot_pyqt, do_debug
from .amazing_tree_dict import Amazing_Dict_Tree_zkm


class Tree_Default_Options(Amazing_Dict_Tree_zkm):

    def __init__(self, parent,
                content_dict=None,
                gui=None,
                **kwargs):
        """[Handles all the dictionary of all default objects
        can edit and expand and view]

        Arguments:
            parent {[type]} -- [description]

        Keyword Arguments:
            content_dict {[type]} -- [description] (default: {None})
            headers {list} -- [description] (default: {["Property", "Value"]})
            num_columns {int} -- [description] (default: {2})
            nameme {str} -- [description] (default: {'Root dictionary'})
        """
        self.gui = gui # used to call remake all
        super().__init__(parent, content_dict = content_dict,
                nameme='DEFAULT_OPTIONS dictionary',
                logger=gui.logger, **kwargs)

    def style_item_dict(self, parent, key, value, parent_key_list, item):
        """Style the row item in the case of dict

        Arguments:
            parent {[type]} -- [description]
            key {[type]} -- [description]
            value {[type]} -- [description]
            parent_key_list {[type]} -- [description]
            item {[type]} -- [description]
        """
        super().style_item_dict(parent, key, value, parent_key_list, item)

        def style_me(color):
            item.setBackground(0,  QtGui.QColor(color))
        if len(parent_key_list) < 1:
            if key.startswith('draw_'):
                style_me('#c6e6d7')
            elif key.startswith('Metal_'):
                if '.' in key:
                    style_me('#DAE4EF')
                else:
                    style_me('#c6d5e6')
            elif key.startswith('Circuit_'):
                style_me('#e6d7c6')
            elif key.startswith('easy'):
                style_me('#c6d5e6')
