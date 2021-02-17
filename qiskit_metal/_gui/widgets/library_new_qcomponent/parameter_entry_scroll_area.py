from PySide2.QtWidgets import QPushButton
from PySide2.QtWidgets import (QScrollArea, QVBoxLayout, QLabel, QWidget,
                               QHBoxLayout, QLineEdit, QLayout, QComboBox,
                               QMessageBox, QSizePolicy, QMainWindow,
                               QDockWidget)
from PySide2.QtCore import Qt
from PySide2.QtCore import QDir
from addict.addict import Dict
from .collapsable_widget import CollapsibleWidget
from collections import OrderedDict
import numpy as np
from .parameter_entry_scroll_area_ui import Ui_ScrollArea
from inspect import signature
import inspect
from collections import Callable
import os
from ....designs.design_base import QDesign
import importlib
import builtins
import logging
import traceback
import json
from .qlibrary_exceptions import PEDASetupException, InvalidParameterEntryException, InvalidFilePathException, LibraryQComponentException, MissingClassException

from typing import Dict as typeDict


class ParameterEntryScrollArea(QScrollArea, Ui_ScrollArea):


    def __init__(self,
                 QLIBRARY_FOLDERNAME: str,
                 abs_file_path: str,
                 design: QDesign,
                 parent=None,
                 *args,
                 **kwargs):
        super(ParameterEntryScrollArea, self).__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.resize(1000, 500)  # TODO figure out a better way to do this
        self.QLIBRARY_FOLDERNAME = QLIBRARY_FOLDERNAME
        self.abs_file_path = abs_file_path
        self.design = design

        self.setAttribute(
            Qt.WA_DeleteOnClose
        )  # delete this ParameterEntryScrollArea when it closes

    def setup_pesa(self):
        self.QLIBRARY_FOLDERNAME = self.QLIBRARY_FOLDERNAME
        self.abs_file_path = self.abs_file_path
        self.design = self.design

        self.parameter_values = []

        self.imported_class = self.get_class_from_abs_file_path(
            self.abs_file_path)

        if self.imported_class is not None:
            self.get_window_title_from_imported_class
            self.display_class_parameter_entries(self.imported_class)

    class QLibraryExceptionDecorator(object):

        @classmethod
        def log_error(cls, log_owner, exception, wrapper, args, kwargs):
            message = traceback.format_exc()
            message += '\n\nERROR in PEDA\n' \
                       + f"\n{' module   :':12s} {wrapper.__module__}" \
                       + f"\n{' function :':12s} {wrapper.__qualname__}" \
                       + f"\n{' err msg  :':12s} {exception.__repr__()}" \
                       + f"\n{' args; kws:':12s} {args}; {kwargs}" \
                       + "\nTill now I always got by on my own........ (I never really cared until I met you)"
            log_owner.logger.error(message)

        # Does NOT handle chained exceptions
        """
        Should wrap ONLY  PEDA instance methods because it assumes args[0] is a self who has a valid logger
        """

        @classmethod
        def entry_exception_pop_up_warning(cls, func: Callable):

            def wrapper(*args, **kwargs):
                # args[0] is PEDA object
                try:
                    return func(*args, **kwargs)
                # if anticipated Exception throw up error window
                except (Exception) as lqce:
                    cls.log_error(args[0], lqce, func, args, kwargs)
                    args[0].error_pop_up = QMessageBox()
                    error_message = "In function, " + str(func.__name__) + str(
                        lqce.__class__.__name__) + ":\n" + str(lqce)
                    args[0].error_pop_up.critical(
                        args[0], "", error_message
                    )  #modality set by critical, Don't set Title -- will NOT show up on MacOs

            return wrapper

        @classmethod
        def init_peda_pop_up_warning(cls, func: Callable):

            def wrapper(*args, **kwargs):
                # args[0] is PEDA object
                try:
                    return func(*args, **kwargs)
                # if anticipated Exception throw up error window
                except (Exception) as lqce:
                    cls.log_error(args[0], lqce, func, args, kwargs)
                    args[0].error_pop_up = QMessageBox()
                    error_message = " Sorry. There has been an issue create the parameter input form for this QComponent. ERROR:"
                    error_message = "In function, " + str(
                        func.__name__) + ", ERROR: " + str(
                            lqce.__class__.__name__
                        ) + error_message + ":\n" + str(lqce)
                    args[0].error_pop_up.critical(
                        args[0], "", error_message
                    )  #modality set by critical, Don't set Title -- will NOT show up on MacOs :(

            return wrapper

    @property
    def logger(self) -> logging.Logger:
        """The Qiskit Metal Logger

        Returns:
            logging.Logger: logger
        """
        return self.design.logger  #steal design's logging

    ## Parameter-Entry Qt Display Custom Classes

    class EntryWidget(QWidget):

        def __init__(self, parent_layout):
            super().__init__()
            self.parent_layout = parent_layout

    class NormalEntryWidget(EntryWidget):

        def __init__(self, parent_layout: QLayout, arg_name: str, arg_type,
                     arg_default):
            super().__init__(parent_layout)  # add self to parent layout
            self.arg_name = arg_name
            self.arg_type = arg_type
            self.arg_default = arg_default

            self.entry_widget_hori_layout = QHBoxLayout()
            self.setLayout(self.entry_widget_hori_layout)

            self.name_label = QLabel(arg_name)
            self.entry_widget_hori_layout.addWidget(self.name_label)

            self.value_edit = QLineEdit()
            self.entry_widget_hori_layout.addWidget(self.value_edit)

    class DictionaryEntryWidget(EntryWidget):

        def __init__(self, parent_layout, arg_name, arg_type, arg_default):
            #TODO arg name can be None thus QLinedEdit
            super().__init__(parent_layout)
            self.arg_type = arg_type
            self.arg_name = arg_name
            self.arg_default = arg_default

            self.parent_layout.setStretchFactor(self, 4)

            self.entry_layout = QHBoxLayout()
            self.setLayout(self.entry_layout)

            self.name_label = QLabel(self.arg_name)
            self.entry_layout.addWidget(self.name_label)

            self.entry_collapsable = CollapsibleWidget()
            self.entry_layout.addWidget(self.entry_collapsable)

            self.entry_collapsable_content_widget = QWidget()
            self.entry_collapsable.setContent(
                self.entry_collapsable_content_widget)

            self.entry_collapsable_layout = QVBoxLayout()
            self.entry_collapsable_content_widget.setLayout(
                self.entry_collapsable_layout)

            self.collapsable_label = QLabel(
                "Please refer to docs to see what key, value pair options are available. "
                "\nNo need to write the ' nor \", your entry will automatically be converted to a string.\n"
                "Do not forget to include dimensions when relevent. Key types are always strings"
            )
            self.entry_collapsable_layout.addWidget(self.collapsable_label)

            self.all_key_value_pairs_entry_widget = QWidget()
            self.entry_collapsable_layout.addWidget(
                self.all_key_value_pairs_entry_widget)

            self.all_key_value_pairs_entry_layout = QVBoxLayout()
            self.all_key_value_pairs_entry_widget.setLayout(
                self.all_key_value_pairs_entry_layout)

            self.add_more_button = QPushButton("+")
            self.all_key_value_pairs_entry_layout.addWidget(
                self.add_more_button)

            # "PySide2 handles connections differently than PyQt5 so use QPushButton.pressed to emit signal without args"
            self.add_more_button.pressed.connect(
                lambda cur_layout=self.all_key_value_pairs_entry_layout: self.
                add_key_value_entry(cur_layout))

            self.add_key_value_entry(self.all_key_value_pairs_entry_layout)

        def add_key_value_entry(self, cur_all_key_value_pairs_entry_layout):
            return self.DictionaryEntryBox(cur_all_key_value_pairs_entry_layout)

        class DictionaryEntryBox(QWidget):

            def __init__(self,
                         cur_all_key_value_pairs_entry_layout,
                         parent=None):
                super().__init__(parent)
                cur_all_key_value_pairs_entry_layout.addWidget(self)
                self.nested_dictionary = None
                self.key_value_entry_layout = QHBoxLayout()
                self.setLayout(self.key_value_entry_layout
                              )  #add self to parent layout's parent widget
                self.key_name = QLabel("Key:")
                self.name_o = QLineEdit()
                self.label = QLabel(":")
                self.value_name = QLabel("Value:")
                self.value_o = QLineEdit(
                )  # in event of nesting, self.value_o will then point to sub DictionaryEntryBox
                self.type_name = self.TypeBuiltInComboBox()
                self.remove_button = QPushButton("REMOVE")
                self.nested_dict_button = QPushButton("nest")
                self.key_value_entry_layout.addWidget(self.key_name)
                self.key_value_entry_layout.addWidget(self.name_o)
                self.key_value_entry_layout.addWidget(self.label)
                self.key_value_entry_layout.addWidget(self.value_name)
                self.key_value_entry_layout.addWidget(self.value_o)
                self.key_value_entry_layout.setStretchFactor(
                    self.value_o,
                    6)  # 4x as large as smallest widget in layout imo
                self.key_value_entry_layout.addWidget(self.type_name)
                self.key_value_entry_layout.addWidget(self.remove_button)
                self.key_value_entry_layout.addWidget(self.nested_dict_button)
                self.remove_button.pressed.connect(
                    lambda w=self, ll=cur_all_key_value_pairs_entry_layout: self
                    .delete_widget(w, ll))
                self.nested_dict_button.pressed.connect(self.nest_dictionary)

            class TypeBuiltInComboBox(QComboBox):

                def __init__(self, parent=None):
                    super().__init__(parent)
                    self.addItem("str")
                    self.addItem("float")
                    self.addItem("int")
                    self.addItem("bool")
                    self.npArr = "ndarray"
                    self.addItem(self.npArr)
                    self.customItems = {
                        self.npArr: lambda a: np.array(json.loads(a))
                    }

                def getType(self):
                    if self.currentText() in self.customItems:
                        return self.customItems[self.currentText()]
                    return getattr(builtins, self.currentText())

            class TypeDictComboBox(QComboBox):

                def __init__(self, parent=None):
                    super().__init__(parent)
                    self.dictStr = "dict"
                    self.orderedDict = "OrderedDict"
                    self.types = {
                        self.dictStr: dict,
                        self.orderedDict: OrderedDict
                    }  #hacky but works
                    self.addItem(self.dictStr)
                    self.addItem(self.orderedDict)

                def getType(self):
                    return self.types[self.currentText()]

            class NestedDictionary(CollapsibleWidget):

                def __init__(self, title, parent):
                    super().__init__(parent=parent, title=title)
                    # self.entry_collapsable replaces old value at end of NestedDictionary init

                    self.entry_content = QWidget(
                        self)  # DictionaryEntryBox is parent
                    self.setContent(self.entry_content)

                    self.nested_kv_layout = QVBoxLayout()
                    self.entry_content.setLayout(self.nested_kv_layout)

                    self.add_more_button = QPushButton("+")
                    self.nested_kv_layout.addWidget(self.add_more_button)

                    self.add_more_button.pressed.connect(
                        lambda cur_layout=self.nested_kv_layout: parent.
                        __class__(cur_layout))

                    # replace parent's dictionary value QLineEdit with another DictionaryBoxEntry
                    parent.key_value_entry_layout.removeWidget(
                        parent.value_name)
                    parent.value_name.deleteLater()

                    parent.key_value_entry_layout.replaceWidget(
                        parent.value_o, self)
                    parent.value_o.deleteLater()
                    parent.value_o = parent.__class__(
                        self.nested_kv_layout
                    )  # new value_o is a DEB containing all debs

            def nest_dictionary(self):
                new_type_name = self.TypeDictComboBox()
                self.key_value_entry_layout.replaceWidget(
                    self.type_name, new_type_name)
                self.type_name.deleteLater()
                self.type_name = new_type_name
                self.nested_dictionary = self.NestedDictionary(
                    "nested dictionary", self)

            def delete_widget(self, widg, lay):
                lay.removeWidget(widg)
                widg.deleteLater()

    ## Parameter-Entry Qt Methods
    @QLibraryExceptionDecorator.init_peda_pop_up_warning
    def display_class_parameter_entries(self, cls: Callable):
        class_signature = signature(cls.__init__)

        for _, param in class_signature.parameters.items():
            if param.name != 'self' and param.name != 'design' and param.name != 'kwargs' and param.name != 'args':
                # TODO handle *args
                # TODO handle **kwargs
                entry_type = param.annotation
                cur_name = param.name
                cur_default = param.default

                if (not param.default or param.default is inspect._empty) and (
                        (entry_type is class_signature.empty or
                        entry_type is inspect._empty)
                ):  # ignores args and kwargs since they won't have types
                    raise PEDASetupException(
                        f"If no default values are provided, a type is needed but none is provided for: {cur_name}"
                    )

                else:
                    if entry_type is type({}) or entry_type is Dict:
                        dew = self.DictionaryEntryWidget(
                            self.parameter_entry_vertical_layout, cur_name,
                            entry_type, cur_default)
                        self.parameter_entry_vertical_layout.addWidget(dew)


                    else:
                        new = self.NormalEntryWidget(
                            self.parameter_entry_vertical_layout, cur_name,
                            entry_type, cur_default)
                        self.parameter_entry_vertical_layout.addWidget(new)

        self.make_button = QPushButton("MAKE")
        self.make_button.clicked.connect(self.make_object)
        self.parameter_entry_vertical_layout.addWidget(self.make_button)

    @QLibraryExceptionDecorator.init_peda_pop_up_warning
    def get_window_title_from_imported_class(self):
        self.setWindowTitle(self.imported_class.__name__)

    @QLibraryExceptionDecorator.init_peda_pop_up_warning
    def delete_widget(self, widg, lay):
        lay.removeWidget(widg)
        widg.deleteLater()

    ## Reading User Input and Instantiating Component Methods
    # https://stackoverflow.com/questions/452969/does-python-have-an-equivalent-to-java-class-forname
    @QLibraryExceptionDecorator.init_peda_pop_up_warning
    def get_class(self, import_statement):
        mymodule = importlib.import_module(import_statement)
        members = inspect.getmembers(mymodule, inspect.isclass)
        class_owner = import_statement.split('.')[-1]
        for memtup in members:
            if len(memtup) > 1:
                if str(memtup[1].__module__).endswith(class_owner):
                    return memtup[1]
        raise MissingClassException(
            f"Unable to find correct module for {class_owner} in {str(members)}"
        )

    @QLibraryExceptionDecorator.init_peda_pop_up_warning
    def get_class_from_abs_file_path(self, abs_file_path):
        if not isinstance(abs_file_path, str):
            raise InvalidFilePathException(
                f"File path must be a string but is currently {abs_file_path} of type: {type(abs_file_path)}"
            )
        qis_abs_path = abs_file_path[abs_file_path.
                                     index(__name__.split('.')[0]):]
        qis_mod_path = qis_abs_path.replace('/', '.')[:-len('.py')]
        qis_mod_path = qis_abs_path.replace('/', '.')[:-len('.py')]
        imported_class = self.get_class(qis_mod_path)
        return imported_class

    #can't wrap this function since it's responsible for closing PESA
    def make_object(self):

        entry_count = self.parameter_entry_vertical_layout.count()
        kwargs = {}
        for index in range(entry_count):
            cur_widget = self.parameter_entry_vertical_layout.itemAt(
                index).widget()
            if isinstance(cur_widget, self.EntryWidget):
                self.argify_entry(cur_widget, kwargs)

        try:  #try-except is used to ensure peda closes if new object fails to be created
            self.imported_class(
                self.design, **kwargs
            )  # * operator simply unpacks the tuple (or any iterable) and passes them as the positional arguments to the function.

            self.close()
        except Exception as e:
            self.design.logger(f"UNABLE TO CREATE CLASS DUE TO: {e}")
            self.close()

    @QLibraryExceptionDecorator.entry_exception_pop_up_warning
    def argify_entry(self, entry: EntryWidget, argdict: dict):
        if not isinstance(entry, self.EntryWidget):
            raise InvalidParameterEntryException(
                f"Expected entry to be of type EntryWidget but is instead of type {str(type(entry))}"
            )
        if isinstance(entry, self.NormalEntryWidget):
            strvalue = entry.value_edit.text()
            if strvalue == "":
                if entry.arg_default is inspect._empty:
                    raise InvalidParameterEntryException(
                        f"No value was entered for {entry.arg_name} but no default value exists in constructor for {self.imported_class}"
                    )
                value = entry.arg_default
            else:
                if entry.arg_type == bool:
                    if strvalue.lower() in "true":
                        value = True
                    else:
                        value = False
                else:
                    value = entry.arg_type(strvalue)
            argdict[entry.arg_name] = value

        elif isinstance(entry, self.DictionaryEntryWidget):
            deb_dict = {}
            self.dictionaryentrybox_to_dictionary(
                entry.all_key_value_pairs_entry_layout, deb_dict)
            argdict[entry.arg_name] = deb_dict
            #argdict[entry.arg_name] = entry.arg_type(deb_dict)

    @QLibraryExceptionDecorator.entry_exception_pop_up_warning
    def dictionaryentrybox_to_dictionary(self, parent_layout, kv_dict):
        # Todo should work for ordered dictionary?
        #get all Debs from layout and add to kv_dict
        kv_count = parent_layout.count()
        for index in range(kv_count):
            cur_widget = parent_layout.itemAt(
                index).widget()  # at least one entry should be + button
            if isinstance(cur_widget,
                          self.DictionaryEntryWidget.DictionaryEntryBox):
                #get keyname:
                keyname = cur_widget.name_o.text()
                if keyname != "":
                    try:
                        keyname = int(
                            keyname)  # some routing requires keys that are ints
                    except:
                        pass
                    #subdictionaries will always be of type dict not of type addict.Dict
                    value_widget = cur_widget.value_o
                    if isinstance(
                            value_widget,
                            self.DictionaryEntryWidget.DictionaryEntryBox):
                        value = cur_widget.type_name.getType()(
                        )  #see whether value widget is OrderedDict or dict
                        self.dictionaryentrybox_to_dictionary(
                            cur_widget.nested_dictionary.nested_kv_layout,
                            value)
                    else:
                        #DictionaryBoxEntries must be of a __builtin__ type
                        strvalue = value_widget.text()
                        if strvalue == "":
                            value = None  # todo perhaps do "" and 0 instead
                        else:
                            cur_type = cur_widget.type_name.getType()
                            if cur_type == bool:
                                if strvalue.lower() in "true":
                                    value = True
                                else:
                                    value = False
                            else:
                                try:
                                    value = cur_type(strvalue)
                                except ValueError as e:
                                    raise InvalidParameterEntryException(
                                        f"The type {cur_type} you chose is not compatible with your input {strvalue}. Error: {e}"
                                    )

                    kv_dict[keyname] = value
