# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""
QLibrary display in Library tab

@authors: Grace Harper
@date: 2021
"""

from PySide2.QtWidgets import QPushButton
from PySide2.QtWidgets import (QScrollArea, QVBoxLayout, QLabel, QWidget,
                               QHBoxLayout, QLineEdit, QLayout, QComboBox,
                               QMessageBox)
from PySide2.QtCore import Qt
from addict.addict import Dict
from .collapsable_widget import CollapsibleWidget
from collections import OrderedDict
import numpy as np
from .parameter_entry_scroll_area_ui import Ui_ScrollArea
from inspect import signature
import inspect
from collections import Callable
from ....designs.design_base import QDesign
import importlib
import builtins
import logging
import traceback
import json
from .qlibrary_exceptions import QCPESetupException, InvalidParameterEntryException, InvalidFilePathException, LibraryQComponentException, MissingClassException


class QComponentParameterEntry(QScrollArea, Ui_ScrollArea):
    """
    QComponentParameterEntry is a QScrollArea that pops up when the user chooses a QComponent from the Library. The user
    then enters in all the relevant parameters for that QComponent's init function into the QComponentParameterEntry and
    clicks the QComponentParameterEntry's make function to create the QComponent

    This class inherits from QScrollArea and the custom Ui_ScrollArea

    Create with
        qiskit_metal._gui.widgets.library_new_qcomponent.create_qcomponent_parameter_entry()

    Access with (when applicable)
        gui.qcpe
    """

    def __init__(
        self,
        QLIBRARY_FOLDERNAME: str,
        abs_file_path: str,
        design: QDesign,
        parent=None,
    ):
        """

        Args:
            QLIBRARY_FOLDERNAME: Current directory name for where all QComponent .py files are held - ex: 'qlibrary'
            abs_file_path: absolute file path to current QComponent .py file
            design: current design
            parent: parent widget

        Note: It is possible for critical MessageBoxes to pop open during the init function if one of the called functions fails for some reason

        """
        super(QComponentParameterEntry, self).__init__(parent)
        self.setupUi(self)
        self.resize(1000, 500)
        self.QLIBRARY_FOLDERNAME = QLIBRARY_FOLDERNAME
        self.abs_file_path = abs_file_path
        self.design = design

        self.setAttribute(
            Qt.WA_DeleteOnClose
        )  # delete this QComponentParameterEntry when it closes

        self.parameter_values = []

        self.imported_class = self.get_class_from_abs_file_path(
            self.abs_file_path)

        if self.imported_class is not None:
            self.get_window_title_from_imported_class
            self.display_class_parameter_entries(self.imported_class)

    ## Exception Handling
    class QComponentParameterEntryExceptionDecorators(object):
        """
        All exceptions in QComponentParameterEntry should result in a pop-up window.
        This class contains the decorators that control exception handling for all functions in QComponentParameterEntry
        """

        @classmethod
        def log_error(cls, log_owner, exception: Exception, wrapper: Callable,
                      args, kwargs):
            """
            Log error manually with whatever logger is currently available. Only used by other QComponentParameterEntryExceptionDecorators decorators
            Args:
                log_owner: Owner of current logger
                exception: exception
                wrapper: wrapper function of other QComponentParameterEntryExceptionDecorators decoraters
                args: current args for function causing the exception
                kwargs: current kwargs for function causing the exception

            """
            message = traceback.format_exc()
            message += '\n\nERROR in QCPE\n' \
                       + f"\n{' module   :':12s} {wrapper.__module__}" \
                       + f"\n{' function :':12s} {wrapper.__qualname__}" \
                       + f"\n{' err msg  :':12s} {exception.__repr__()}" \
                       + f"\n{' args; kws:':12s} {args}; {kwargs}" \
                       + "\nTill now I always got by on my own........ (I never really cared until I met you)"
            log_owner.logger.error(message)

        @classmethod
        def entry_exception_pop_up_warning(cls, func: Callable):
            """
            Throws up critical QMessageBox with current exception in the event an exception is thrown by func
            Args:
                func: current function causing exceptions - should  be ONLY  qcpe instance methods because decoraters
                assumes arg[0] is a self who has a valid logger

            """

            def wrapper(*args, **kwargs):
                # args[0] is QCPE object
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
        def init_qcpe_pop_up_warning(cls, func: Callable):
            """
            Throws up critical QMessageBox with current exception in the event an exception is thrown by func during
            initialization of qcpe
            Args:
                func: current function causing exceptions - should  be ONLY  qcpe instance methods because decoraters
                assumes arg[0] is a self who has a valid logger

            """

            def wrapper(*args, **kwargs):
                # args[0] is QCPE object
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

    ## Get Class Methods
    @QComponentParameterEntryExceptionDecorators.init_qcpe_pop_up_warning
    def get_class(self, import_statement):
        """
        Gets the corresponding class object for the import_statement
        Args:
            import_statement: import statement for desired QComponent


        """
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

    @QComponentParameterEntryExceptionDecorators.init_qcpe_pop_up_warning
    def get_class_from_abs_file_path(self, abs_file_path):
        """
        Gets the corresponding class object for the absolute file path to the file containing that class definition
        Args:
            abs_file_path: absolute file path to the file containing the QComponent class definition

        getting class from absolute file path - https://stackoverflow.com/questions/452969/does-python-have-an-equivalent-to-java-class-forname

        """
        if not isinstance(abs_file_path, str):
            raise InvalidFilePathException(
                f"File path must be a string but is currently {abs_file_path} of type: {type(abs_file_path)}"
            )
        qis_abs_path = abs_file_path[abs_file_path.
                                     index(__name__.split('.')[0]):]
        qis_mod_path = qis_abs_path.replace('/', '.')[:-len('.py')]
        imported_class = self.get_class(qis_mod_path)
        return imported_class

    ## Display QCPE Entry Subclasses
    class EntryWidget(QWidget):
        """
        Widget containing QLineEdits used by user for entering parameters
        Most Objects are not supported. Primitives (strs, bools, etc.), ndarray, and dictionaries are supported
        """

        def __init__(self, parent_layout):
            super().__init__()
            self.parent_layout = parent_layout

    class NormalEntryWidget(EntryWidget):
        """
        Entry Widget for parameters that are not dictionaries (and do not belong to dictionaries)
        """

        def __init__(self, parent_layout: QLayout, param_name: str,
                     param_type: type, param_default):
            """

            Args:
                parent_layout: layout owning this NormalEntryWidget
                param_name: parameter name (ex: 'name', 'color', etc.)
                param_type: parameter type (ex: bool, int, etc.)
                param_default: default parameter
            """

            super().__init__(parent_layout)  # add self to parent layout
            self.param_name = param_name
            self.param_type = param_type
            self.param_default = param_default

            self.entry_widget_hori_layout = QHBoxLayout()
            self.setLayout(self.entry_widget_hori_layout)

            self.name_label = QLabel(param_name)
            self.entry_widget_hori_layout.addWidget(self.name_label)

            self.value_edit = QLineEdit()
            self.entry_widget_hori_layout.addWidget(self.value_edit)

    class DictionaryEntryWidget(EntryWidget):
        """
        Entry Widget for dictionaries
        Each DEW contains several DictionaryEntryBox (DEB).
        (Each DictionaryEntryBox is a widget to contain a single key value pair entered by the user).
        While a DEB's key must be either a string or an int, the DEB's displayed value can be a NestedDictionary (allowing for nested dictionary entry).
        (For testing purposes the actual value of the DEB will point to the first DEB in the NestedDictionary)
        A NestedDictionary itself contains multiple DEBs for it's key, value pairs
        Here is an example of the entry structure below:

        #Dictionary Entry Widget:
            - entry level 0 DEB --> key: value,
            - entry level 0 DEB --> key:  Nested Dictionary:
                                            - entry level 1 DEB --> key: value,
                                            - entry level 1 DEB --> key: NestedDictionary:
                                                                            - entry level 2 DEB --> key: value

                                            - entry level 1 DEB --> key: value
            - entry level 0 DEB --> key: value
        """

        def __init__(self, parent_layout, param_name, param_type,
                     param_default):
            """

            Args:
                parent_layout: layout owning this DictionaryEntryWidget
                param_name: parameter name (ex: 'options', etc.)
                param_type: dict # exists for uniformity with NormalEntryWidget
                param_default: default parameter
            """
            super().__init__(parent_layout)
            self.param_type = param_type
            self.param_name = param_name
            self.param_default = param_default

            self.parent_layout.setStretchFactor(self, 4)

            self.entry_layout = QHBoxLayout()
            self.setLayout(self.entry_layout)

            self.name_label = QLabel(self.param_name)
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
                "Do not forget to include dimensions when relevant. Except for OrderedDict, key types are always strings"
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
            """
            DictionaryEntryBoxes contain the actual QLineEdits in which the user will enter parameter information.
            DEBs get added to top-level DictionaryEntryWidget and to NestedDictionary
            A DEBs may use a NestedDictionary as their value
            """

            def __init__(self,
                         cur_all_key_value_pairs_entry_layout,
                         parent=None):
                """

                Args:
                    cur_all_key_value_pairs_entry_layout: layout that DEB will get added to - layout will belong to
                    either a DEB.key_value_entry_layout or a DEW.all_key_value_pairs_entry_layout
                    parent: parent widget
                """
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
                self.type_name = self.TypeBuiltInComboBox(
                )  #if nested will become TypeDictComboBox
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
                """
                Contains all possible types for values in a DEB
                """

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
                """
                Contains all possible DEB types
                """

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
                """
                A NestedDictionary is nested inside a DEB to allow for multi-level key,value entries.
                An ND can add/remove multiple DEBs to it's layout to allow for multiple key,value entries for it's entry level

                #Dictionary Entry Widget:
                    - entry level 0 DEB --> key: value,
                    - entry level 0 DEB --> key:  Nested Dictionary:
                                                    - entry level 1 DEB --> key: value,
                                                    - entry level 1 DEB --> key: NestedDictionary:
                                                                                    - entry level 2 DEB --> key: value

                                                    - entry level 1 DEB --> key: value
                    - entry level 0 DEB --> key: value
                """

                def __init__(self, title, parent):
                    """

                    Args:
                        title: title for the NestedDictionary
                        parent: DEB that will own the NestedDictionary
                    """
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
                """
                Create a new NestedDictionary inside of self (current DEB)

                """
                new_type_name = self.TypeDictComboBox()
                self.key_value_entry_layout.replaceWidget(
                    self.type_name, new_type_name)
                self.type_name.deleteLater()
                self.type_name = new_type_name
                self.nested_dictionary = self.NestedDictionary(
                    "nested dictionary", self)

            def delete_widget(self, widg: QWidget, lay: QLayout):
                """
                Remove widg from  lay and delete widg
                Args:
                    widg: widget to be deleted
                    lay: layout containing widget

                Returns:

                """
                lay.removeWidget(widg)
                widg.deleteLater()

    ## Display QCPE Entry Methods
    @QComponentParameterEntryExceptionDecorators.init_qcpe_pop_up_warning
    def display_class_parameter_entries(self, cls: Callable):
        """
        For each parameter listed in the cls init function (excluding self, design, kwargs, args),
        display_class_parameter_entries adds an EntryWidget to the QCPE display

        Args:
            cls: QComponent the QCPE is for


        """
        class_signature = signature(cls.__init__)

        for _, param in class_signature.parameters.items():
            if param.name != 'self' and param.name != 'design' and param.name != 'kwargs' and param.name != 'args':

                entry_type = param.annotation
                cur_name = param.name
                cur_default = param.default

                if (not param.default or param.default is inspect._empty) and (
                    (entry_type is class_signature.empty or
                     entry_type is inspect._empty)
                ):  # ignores args and kwargs since they won't have types
                    raise QCPESetupException(
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

    @QComponentParameterEntryExceptionDecorators.init_qcpe_pop_up_warning
    def get_window_title_from_imported_class(self):
        """
        Sets QCPE title

        """
        self.setWindowTitle(self.imported_class.__name__)

    @QComponentParameterEntryExceptionDecorators.init_qcpe_pop_up_warning
    def delete_widget(self, widg, lay):
        """
        Remove widg from  lay and delete widg
        Args:
            widg: widget to be deleted
            lay: layout containing widget

        """
        lay.removeWidget(widg)
        widg.deleteLater()

    ## Entry Evaluation Methods
    def make_object(self):
        """
        Creates QComponent using parameters entered by user and closes QCPE.
        Try-except must be handled by make_object (instead of decorater) to ensure qcpe closes
        """

        entry_count = self.parameter_entry_vertical_layout.count()
        kwargs = {}
        for index in range(entry_count):
            cur_widget = self.parameter_entry_vertical_layout.itemAt(
                index).widget()
            if isinstance(cur_widget, self.EntryWidget):
                self.argify_entry(cur_widget, kwargs)

        try:  #try-except is used to ensure qcpe closes if new object fails to be created
            self.imported_class(
                self.design, **kwargs
            )  # * operator simply unpacks the tuple (or any iterable) and passes them as the positional arguments to the function.

            self.close()
        except Exception as e:
            self.design.logger(f"UNABLE TO CREATE CLASS DUE TO: {e}")
            self.close()

    @QComponentParameterEntryExceptionDecorators.entry_exception_pop_up_warning
    def argify_entry(self, entry: EntryWidget, param_dict: dict):
        """
        Collect user-entered parameters and adds them to param_dict, which will be used to create the QComponent
        Args:
            entry: current EntryWidget
            param_dict: dictionary that will contain all the parameters needed to instantiate the QComponent

        Returns:

        """
        if not isinstance(entry, self.EntryWidget):
            raise InvalidParameterEntryException(
                f"Expected entry to be of type EntryWidget but is instead of type {str(type(entry))}"
            )
        if isinstance(entry, self.NormalEntryWidget):
            strvalue = entry.value_edit.text()
            if strvalue == "":
                if entry.param_default is inspect._empty:
                    raise InvalidParameterEntryException(
                        f"No value was entered for {entry.param_name} but no default value exists in constructor for {self.imported_class}"
                    )
                value = entry.param_default
            else:
                if entry.param_type == bool:
                    if strvalue.lower() in "true":
                        value = True
                    else:
                        value = False
                else:
                    value = entry.param_type(strvalue)
            param_dict[entry.param_name] = value

        elif isinstance(entry, self.DictionaryEntryWidget):
            deb_dict = {}
            self.dictionaryentrybox_to_dictionary(
                entry.all_key_value_pairs_entry_layout, deb_dict)
            param_dict[entry.param_name] = deb_dict
            #param_dict[entry.param_name] = entry.param_type(deb_dict)

    @QComponentParameterEntryExceptionDecorators.entry_exception_pop_up_warning
    def dictionaryentrybox_to_dictionary(self, parent_layout: QLayout,
                                         kv_dict: dict):
        """
        Converts user-entered parameter DEBs into dictionaries
        Args:
            parent_layout: DEW/ND layout owning the DEBs
            kv_dict: the dictionary representation of the DEW/NDs

        """
        #get all Debs from layout and add to kv_dict
        kv_count = parent_layout.count()
        for index in range(kv_count):
            cur_widget = parent_layout.itemAt(
                index).widget()  # at least one entry should be + button
            if isinstance(cur_widget,
                          self.DictionaryEntryWidget.DictionaryEntryBox):
                keyname = cur_widget.name_o.text()
                if keyname != "":
                    if isinstance(kv_dict, OrderedDict):
                        try:
                            keyname = int(
                                keyname
                            )  # some routing requires keys that are ints
                        except:
                            pass

                    #subdictionaries will always be of type dict not of type addict.Dict
                    value_widget = cur_widget.value_o
                    if isinstance(
                            value_widget,
                            self.DictionaryEntryWidget.DictionaryEntryBox):

                        value = cur_widget.type_name.getType()()

                        self.dictionaryentrybox_to_dictionary(
                            cur_widget.nested_dictionary.nested_kv_layout,
                            value)
                    else:
                        strvalue = value_widget.text()
                        if strvalue == "":
                            value = None
                        else:
                            cur_type = cur_widget.type_name.getType()
                            if cur_type == bool:
                                if strvalue.lower() in "true":
                                    value = True
                                elif strvalue.lower() in "false":
                                    value = False
                                else:
                                    raise InvalidParameterEntryException(
                                        f"The type {cur_type} you chose is not compatible with your input {strvalue}."
                                    )
                            else:
                                try:
                                    value = cur_type(strvalue)
                                except ValueError as e:
                                    raise InvalidParameterEntryException(
                                        f"The type {cur_type} you chose is not compatible with your input {strvalue}. Error: {e}"
                                    )

                    kv_dict[keyname] = value
