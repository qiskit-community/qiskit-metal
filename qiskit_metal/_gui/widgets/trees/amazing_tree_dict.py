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
@date: 2019-09-26
@author: Zlatko K. Minev
"""

from qiskit_metal._gui._handle_qt_messages import catch_exception_slot_pyqt

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem, QIntValidator
from PyQt5.QtWidgets import QApplication, QWidget, QTreeView, QDockWidget
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QMainWindow, QListWidget
from PyQt5.QtWidgets import QTextEdit, QTreeWidget, QTreeWidgetItem, QLineEdit
from PyQt5.QtWidgets import QToolBar, QAction, QSlider, QInputDialog, QMessageBox
from PyQt5.QtWidgets import QLabel, QSizePolicy

from .... import Dict, logger
from .metal_parameter import Parameter_Zlatko


def get_nested_dict_item(dic, key_list, level=0):
    """
    EXAMPLE USE
    ---------------------
    myDict = Dict(aa=Dict(x1={'dda':34},y1='Y',z='10um'),
          bb=Dict(x2=5,y2='YYYsdg',z='100um'))
    key_list = ['aa', 'x1', 'dda']
    [get_dict_item](myDict, key_list)

    returns 34
    """
    if not key_list:  # get the root
        return dic

    if level < len(key_list)-1:
        return get_nested_dict_item(dic[key_list[level]], key_list, level+1)
    else:
        return dic[key_list[level]]


def pop_nested_dict_item(dic, key_list, level=0):
    """
    EXAMPLE USE
        ---------------------
    myDict = Dict(aa=Dict(x1={'dda':34},y1='Y',z='10um'),
          bb=Dict(x2=5,y2='YYYsdg',z='100um'))
    key_list = ['aa', 'x1', 'dda']
    pop_nested_dict_item(myDict, key_list)

    returns 34
    """
    if not key_list:  # get the root
        print("ERRROR TRYING TO POP ROOT")

    if level < len(key_list)-1:
        return pop_nested_dict_item(dic[key_list[level]], key_list, level+1)
    else:
        dic.pop(key_list[level])


class Amazing_Dict_Tree_zkm(QTreeWidget):

    def __init__(self, parent,
                 content_dict=None,
                 headers=["Property", "Value"],
                 num_columns=2,
                 nameme='Root dictionary',
                 logger=None,
                 *args, **kwargs):
        """
        Implements a view of a nested dictionary with write options.
        Not updated automatically when user changes dict, since there are no
        signals emitted. (This could be implemented as a binding on Dict.)

        Properties:
         dict : content of main dictionary

        Workings:
            each items in the tree has a `name` that is used to itteratte through the dictionary
            and to access and to write to it.
            Asusmed QTreeItems have _parent

        Notes on creation inside parent (and layout basics):
            This should go inside a layout. The layout will automatically reparent
            the widgets. Note: Widgets in a layout are children of the widget on which
            the layout is installed, not of the layout itself. Widgets can only have
            other widgets as parent, not layouts.

        # Todo: add remove item (enabled or not)
        # TODO: add add item to dict


        Exampl independnat use::
        ========================
        ```

            parent = QDialog()
            parent._layout = QVBoxLayout(parent)
            parent.setLayout(parent._layout)
            parent.show()

            myDict = Dict(aa=Dict(x1={'dda':34},y1='Y',z='10um'),
                        bb=Dict(x2=5,y2='YYYsdg',z='100um'),
                        cc=5,
                        options=Dict(w1=13))

            tree = parent.tree = Amazing_Dict_Tree_zkm(parent, myDict)
            parent.layout().addWidget(parent.tree)
        ```
        """
        super().__init__(parent, *args, **kwargs)

        self._parent = parent
        self.dict = content_dict
        #self.items = {}
        self.name = 'root'  # for internal tracking, could be done differently
        self.nameme = nameme  # name used in options menu
        self.menu_allow_delete = True
        self.logger = logger

        self.setColumnCount(num_columns)  # can obtain by self.columnCount()
        if headers:
            self.setHeaderLabels(headers)
            # self.setHeaderItem(QTreeWidgetItem(headers))

        # Menu
        self.setup_menu()

        self.expanded.connect(self.on_expanded)
        # self.itemDoubleClicked.connect(self.dblclick)
        self.style_base()

        self.rebuild()

    def change_content_dict(self, content_dict):
        """change_content_dict

        Arguments:
            content_dict {[Dict]} -- [new dict]
        """
        self.dict = content_dict
        self.rebuild()

    def setup_menu(self):
        """
        Overwrite with pass to disable
        """
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)

    @catch_exception_slot_pyqt()
    def open_menu(self, position, execme=True):
        """
        Create and Handle context menu when right click is applied
        """
        selected = self.selectedIndexes()
        # self.selected = selected  # debug
        if len(selected) > 0:
            item = self.itemFromIndex(selected[0])
            item_key = item.key
            item_key_list = item.parent_key_list + [item_key]
            item_value = self.get_dict_item(item_key_list)

            menu = QtWidgets.QMenu(self)
            if isinstance(item_value, dict):
                #print('We selected a dicitonary: item_key_list=', item_key_list)
                dict_to_add = item_key_list
                _dict_item = item
            else:
                if len(item_key_list) > 0:
                    dict_to_add = item_key_list[:-1]
                else:
                    dict_to_add = []
                    print('ERROR: should not be here, out of index. ')
                _dict_item = item._parent
                #print('We DID NOT select a dicitonary: item_key_list=', item_key_list, ";  dict_to_add=",dict_to_add)
            if dict_to_add:
                nameme = '.'.join(dict_to_add)
            else:
                nameme = self.nameme

            # MENU ITEMS
            menu.labelme = menu.addAction('For `' + nameme + "`")
            menu.add_float = menu.addAction(" - add float item")
            menu.add_string = menu.addAction(" - add string item")
            menu.add_dict = menu.addAction(" - add dictionary item")
            menu.addSeparator()
            menu.action_delete = menu.addAction("Delete this item")

            # MENU ACTIONS
            menu.action_delete.setEnabled(self.menu_allow_delete)
            menu.action_delete.triggered.connect(
                self._menu_del_item(item, item_key_list))

            # Handle adding new variables - define new function to return to handle it  # TODO move outsid ehtris cope
            def menu_action_add_item(kind='dictionary'):

                @catch_exception_slot_pyqt()
                def return_add_item(x):
                    # Get name of new key
                    text_key, okPressed = QInputDialog.getText(
                        self, f"Name of new {kind} to add?", "Choose name:", QLineEdit.Normal, "")
                    if okPressed and text_key != '':
                        #print('new dictionary:', text, item_key_list, self.get_dict_item(dict_to_add))

                        # Get value of new key
                        if kind is 'dictionary':
                            new_obj = Dict()  # maybe asteval here
                        elif kind is 'string':
                            text, okPressed = QInputDialog.getText(
                                self, f"Choose value of {kind} to add?", "Choose value:", QLineEdit.Normal, "")
                            if okPressed:
                                new_obj = text
                            else:
                                return
                        elif kind is 'float':
                            text, okPressed = QInputDialog.getText(
                                self, f"Choose value of {kind} to add?", "Choose value:", QLineEdit.Normal, "0.0")
                            if okPressed and text != '':
                                new_obj = float(text)
                            else:
                                return

                        # now assign
                        dic = self.get_dict_item(dict_to_add)
                        dic[text_key] = new_obj
                        if dict_to_add:  # not root
                            # QTreeWidgetItem correspondoing to the dicitonary we want to edit
                            # recreate remake dictionary
                            self.on_expanded(self.indexFromItem(_dict_item))
                        else:  # root
                            self.rebuild()

                return return_add_item

            # assign to buttons
            menu.add_float.triggered.connect(menu_action_add_item('float'))
            menu.add_string.triggered.connect(menu_action_add_item('string'))
            menu.add_dict.triggered.connect(menu_action_add_item('dictionary'))

            if execme:
                menu.exec_(self.viewport().mapToGlobal(position))
            return menu

    def _menu_del_item(self, item, item_key_list):

        @catch_exception_slot_pyqt()
        def _menu_del_item_internal(x):
            #print('_menu_del_item_internal', item_key_list, item)
            self.pop_dict_item(item_key_list)
            self.item = item
            root = self.invisibleRootItem()
            (item.parent() or root).removeChild(item)

        return _menu_del_item_internal

    def _on_edit_return(self, parent):
        """
        On return of editing a qline with with Zlatko_params
         what do do, such as redraw all objects

        Creates a funciton for this
        """
        def __on_edit_return__():
            # recreate remake dictionary
            self.on_expanded(self.indexFromItem(parent))
        return __on_edit_return__

    @catch_exception_slot_pyqt()
    def on_expanded(self, expand_model_index):
        """
        Handles the expansion of a tree item.
        Adds new items dynamically.
        """
        # Debug
        # self._expand_model_index = expand_model_index # debug
        # logger.info('on_expanded: item %s %s %s %s', expand_model_index, expand_model_index.row(),
        #      expand_model_index.data(), expand_model_index.parent())

        item = self.itemFromIndex(expand_model_index)  # get QTreeWidgetItem that was expanded
        if item:  # make sure not None
            # if not hasattr(item, '__ignore_expand__'): # quick clude if we dont want to handle dict this way for metal objects for instance
            # Clear children
            item.takeChildren()

            # Add new items
            item_key_list = item.parent_key_list + [item.key]
            item_dict = self.get_dict_item(item_key_list)
            #logger.info('calling populate_expandable')
            self.populate_expandable(item_dict, item, item_key_list)

            # Resize colun width of the first column to fit
            self.resizeColumnToContents(0)

    def get_dict_item(self, item_key_list):
        return get_nested_dict_item(self.dict, item_key_list)

    def pop_dict_item(self, item_key_list):
        pop_nested_dict_item(self.dict, item_key_list)

    def rebuild(self):
        #logger.debug(f'Populating {self.__class__.__name__}')
        self.setUpdatesEnabled(False)
        try:
            self.clear()
            self.style()
            self.populate_expandable(content=self.dict, parent=None, parent_key_list=[])
            # self.expanded.emit(QtCore.QModelIndex())
        finally:
            self.setUpdatesEnabled(True)

    def resolve_parent_key_list(self, obj):
        if obj.name is 'root':
            return []
        else:
            return self.resolve_parent_key_list(obj._parent) + [obj.name]

    def style_item_dict(self, parent, key, value, parent_key_list, item):
        """
        Style item in the case of dict
        """
        font = QtGui.QFont()
        font.setBold(True)
        item.setFont(0, font)

    def handle_item_dict(self, parent, key, value, parent_key_list):
        item = QTreeWidgetItem(parent, [key, '...'])
        item._parent = parent
        item.key = key
        item.parent_key_list = parent_key_list

        item.setChildIndicatorPolicy(item.ShowIndicator)
        self.style_item_dict(parent, key, value, parent_key_list, item)
        return item

    def handle_item_other_custom(self, parent, key, value, parent_key_list, item):

        if Parameter_Zlatko.I_can_handle_this_type(value):
            item.widgetz = Parameter_Zlatko(self.dict,
                                            parent_key_list + [key],
                                            value,
                                            on_return=self._on_edit_return(parent),
                                            logger=self.logger)
            self.setItemWidget(item, 1, item.widgetz)  # place the QLineEdit

        elif isinstance(value, list) or isinstance(value, tuple):
            item.setData(1, 0, f'{str(value)}')
        elif value is None:
            pass
        else:
            logger.debug(
                f'Unhandled param: parent_key_list={parent_key_list} key={key}; value={value}')

    def handle_item_other(self, parent, key, value, parent_key_list):
        item = QTreeWidgetItem(parent, [key, str(value)])
        item._parent = parent
        item.key = key
        item.parent_key_list = parent_key_list
        self.handle_item_other_custom(parent, key, value, parent_key_list, item)
        return item

    def handle_item(self, parent, key, value, parent_key_list):
        if isinstance(value, dict):
            self.handle_item_dict(parent, key, value, parent_key_list)
        else:  # str, int, list, etc.
            self.handle_item_other(parent, key, value, parent_key_list)

    def populate_dict(self, content, parent, parent_key_list):
        """
        Populate the contents of a dicitonary

        Assumes that all dicitonaries are childern of dicitonaries

        the name of the dict is parent_key_list[-]
        parent_key_list contains list of keys to get down the self.dict to this dicitonary
        """
        #logger.info(' populate_dict %s' %(content.keys()))
        #parent_key_list = self.resolve_parent_key_list(parent)
        #print('parent_key_list', parent_key_list)
        if not parent:
            parent = self.invisibleRootItem()  # root item

        for key, value in content.items():
            #logger.info(' KEY =  %s' %(key))
            self.handle_item(parent, key, value, parent_key_list)

    def populate_expandable(self, content, parent, parent_key_list):
        """Assumes that it is the child of a QTreeWidgetItem that has been given an expandle
        option.

        Arguments:
            content {[type]} -- [description]
            parent {[type]} -- [description]
            parent_key_list {[type]} -- [description]
        """
        if isinstance(content, dict):
            self.populate_dict(content, parent, parent_key_list)
        else:
            print("ERRROR IN AMAZING TREE: populate_expandable got a non dict")

    def populate_expand(self, item):
        pass

    def style_base(self):
        """
        Base widget style.
        """
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
