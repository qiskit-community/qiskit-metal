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
@date: 2019
@author: Zlatko K. Minev
"""

__all__ = ['Tree_Metal_Objects']

import shapely

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem, QIntValidator
from PyQt5.QtWidgets import QApplication, QWidget, QTreeView, QDockWidget
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QMainWindow, QListWidget
from PyQt5.QtWidgets import QTextEdit, QTreeWidget, QTreeWidgetItem, QLineEdit
#from PyQt5.QtWidgets import QToolBar, QAction, QSlider, QInputDialog, QMessageBox
#from PyQt5.QtWidgets import QLabel

from .... import logger, is_metal_component
#from .metal_parameter import Parameter_Zlatko
from .amazing_tree_dict import Amazing_Dict_Tree_zkm

class Tree_Metal_Objects(Amazing_Dict_Tree_zkm):

    color_slight = QtGui.QColor('#EEEEEE')
    color_polys = QtGui.QColor('#e6bbad')
    color_named = QtGui.QColor('#CCCC00')

    def __init__(self, parent,
                objects=None,
                gui=None,
                **kwargs):
        """[Handles all the dictionary of all metal objects
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
        super().__init__(parent,
                content_dict = objects,
                num_columns=2,
                nameme='objects dictionary',
                headers=["Object/Property", "Value"],
                logger = gui.logger,
                **kwargs)


    def _on_edit_return(self, parent):
        """
        On return of editing a qline with with Zlatko_params
         what do do, such as redraw all objects

        Creates a funciton for this
        """
        func1 = super()._on_edit_return(parent)
        def func2():
            func1()
            if self.gui:
                self.gui.remake_all()
        return func2

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
        if key.startswith('objects'):
            style_me('#ade6bb')
        elif key.startswith('options'):
            style_me('#add8e6')
        elif key.startswith('hfss_'):
            style_me('#e6add8')

    def populate_expandable(self, content, parent, parent_key_list):
        """Assumes that it is the child of a QTreeWidgetItem that has been given an expandle
        option.

        Arguments:
            content {[type]} -- [description]
            parent {[type]} -- [description]
            parent_key_list {[type]} -- [description]
        """
        #logger.info('metal_objects')
        if is_metal_component(content):
            #logger.info(' METAL OBJ')
            if not parent:
                parent = self.invisibleRootItem()  # root item

            metal_obj = content
            for metal_obj_child_name in metal_obj._gui_param_show:
                metal_obj_child = getattr(metal_obj, metal_obj_child_name)
                new_parent_list = parent_key_list + [metal_obj_child_name]
                if isinstance(metal_obj_child, dict):
                    #print('new_parent_list', new_parent_list, ' metal_obj=', metal_obj,
                    #            ' metal_obj_child_name=', metal_obj_child_name,
                    #            ' metal_obj_child=',metal_obj_child)
                    #self.populate_dict(metal_obj_child, parent, new_parent_list)
                    self.handle_item_dict(parent, metal_obj_child_name,
                        self.get_dict_item(new_parent_list), parent_key_list)
                else:
                    logger.error('.'.join(new_parent_list) + f'from _gui_param_show \
                        is not a dict!!! Unhandled as of now... Use only dicitonaries. ')
        else:
            super().populate_expandable(content, parent, parent_key_list)

    def handle_item_other_custom(self, parent, key, value, parent_key_list, item):
        """Handle non dicitoanry row. Take care of metal objects

        Arguments:
            parent {[type]} -- [description]
            key {[type]} -- [description]
            value {[type]} -- [description]
            parent_key_list {[type]} -- [description]
        """
        if is_metal_component(value):
            #item.__ignore_expand__ = True
            item.setChildIndicatorPolicy(item.ShowIndicator) # expandable

        elif isinstance(value, shapely.geometry.base.BaseGeometry):
            # style
            font = QtGui.QFont()
            font.setPointSize(8)
            item.setData(1, 0, f'GEOM:{type(value)}')
            item.setBackground(0, self.color_polys)
            item.setBackground(1, self.color_slight)
            item.setFont(1, font)
        else:
            super().handle_item_other_custom(parent, key, value, parent_key_list, item)
