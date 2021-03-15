from PySide2.QtWidgets import QItemDelegate
from PySide2.QtCore import QAbstractItemModel, QModelIndex, QTimer, Qt
from PySide2.QtWidgets import (QWidget,QStyleOptionViewItem)

from qiskit_metal._gui.widgets.library_new_qcomponent.model_view.tree_model_param_entry import TreeModelParamEntry


class ParamDelegate(QItemDelegate):
    """
    ParamDelegate for controlling specific UI display (such as QComboBoxes) for the Parameter Entry Window
    """
    pass

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem,
                     index: QModelIndex) -> QWidget:
        """
        Overriding inherited createdEditor class
        Args:
            parent: Parent widget
            option: Style options for the related view
            index: Specific index being edited

        Returns:

        """
        if index.column() == TreeModelParamEntry.TYPE:
            node = index.model().nodeFromIndex(index)
            combo = node.get_type_combobox(parent)  #dicts vs values
            combo.setEditable(True)
            return combo
        else:
            return QItemDelegate.createEditor(self, parent, option, index)

    def setEditorData(self, editor, index: QModelIndex):
        """
        Overriding inherited setEditorData class
        Args:
            editor: Current editor for the data
            index: Current index being modified

        """
        m = index.model()
        d = m.data(index, Qt.DisplayRole)
        text = index.model().data(index, Qt.DisplayRole)
        if index.column() == TreeModelParamEntry.TYPE:
            text = editor.setCurrentText(text)
        else:
            QItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model: QAbstractItemModel, index):
        """
        Overriding inherited setModelData class
        Args:
            editor: Current editor for the data
            model: Current model whose data is being set
            index: Current index being modified

        Returns:

        """
        if index.column() == TreeModelParamEntry.TYPE:
            model.setData(index, editor.getTypeName())
            # get type
            # get corresponding dict entry
            # update type (OrderedDict, str, etc.)  as necessary
            # get value
        else:
            QItemDelegate.setModelData(self, editor, model, index)
