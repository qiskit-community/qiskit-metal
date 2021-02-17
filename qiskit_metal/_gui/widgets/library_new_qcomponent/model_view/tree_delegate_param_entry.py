from PySide2.QtWidgets import QItemDelegate

from PySide2 import QtCore
from PySide2.QtGui import QFont, QPainter, QTextDocument, QColor
from PySide2.QtWidgets import QTreeView, QWidget
from PySide2.QtCore import QAbstractItemModel, QModelIndex, QTimer, Qt
import ast
from typing import Union, TYPE_CHECKING
import queue
from PySide2.QtCore import QAbstractItemModel, QModelIndex, QTimer, Qt
from PySide2.QtWidgets import (QAbstractItemView, QApplication, QFileDialog,
                               QWidget, QTreeView, QLabel, QMainWindow,
                               QMessageBox, QTabWidget, QStyle,
                               QStyleOptionViewItem, QTextEdit, QLineEdit)
from PySide2.QtWidgets import QApplication
import builtins
import numpy as np
import json
from qiskit_metal._gui.widgets.library_new_qcomponent.model_view.tree_model_param_entry import TreeModelParamEntry


class ParamDelegate(QItemDelegate):
    pass

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem,
                     index: QModelIndex) -> QWidget:
        if index.column() == TreeModelParamEntry.TYPE:
            node = index.model().nodeFromIndex(index)
            try:
                combo = node.get_type_combobox(parent)  #dicts vs values
            except Exception as e:
                print(e)
            print("combo: ", combo)
            combo.setEditable(True)
            print("ret combo")
            return combo
        else:
            return QItemDelegate.createEditor(self, parent, option, index)

    def setEditorData(self, editor, index: QModelIndex):
        print("hi")
        m = index.model()
        print(m)
        d = m.data(index, Qt.DisplayRole)
        print(d)
        text = index.model().data(index, Qt.DisplayRole)
        if index.column() == TreeModelParamEntry.TYPE:
            text = editor.setCurrentText(text)
        else:
            QItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model: QAbstractItemModel, index):
        if index.column() == TreeModelParamEntry.TYPE:
            model.setData(index, editor.getTypeName())
            # get type
            # get corresponding dict entry
            # update type (OrderedDict, str, etc.)  as necessary
            # get value
        else:
            QItemDelegate.setModelData(self, editor, model, index)

    #   WILL nEeD for values / names

    # def commitAndCloseEditor(self):
    #     editor = self.sender()
    #     if isinstance(editor, (QTextEdit, QLineEdit)):
    #         self.commitData.emit()
    #
