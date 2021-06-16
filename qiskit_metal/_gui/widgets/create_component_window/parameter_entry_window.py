# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# pylint: disable-msg=too-many-return-statements
# pylint: disable-msg=no-else-return
# pylint: disable-msg=inconsistent-return-statements
# pylint: disable-msg=attribute-defined-outside-init
# pylint: disable-msg=broad-except
# pylint: disable-msg=import-outside-toplevel
# pylint: disable-msg=relative-beyond-top-level
# pylint: disable-msg=import-error
# pylint: disable-msg=too-few-public-methods
# pylint: disable-msg=too-many-instance-attributes
# pylint: disable-msg=invalid-name
# pylint: disable-msg=no-name-in-module
"""
Parameter Entry Window for displaying parameters for QComponent instantiation from GUI's
QLibrary tab
"""

import copy
import importlib
import inspect
import os
import random
from collections import OrderedDict, Callable
from inspect import signature
from pathlib import Path
from typing import TYPE_CHECKING, Union, Type

import numpy as np
from PySide2 import QtGui, QtWidgets
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QDockWidget, QWidget
from PySide2.QtWidgets import (QMainWindow, QMessageBox)

from qiskit_metal import designs
from qiskit_metal.toolbox_python.attr_dict import Dict
from .model_view.tree_delegate_param_entry import ParamDelegate
from .model_view.tree_model_param_entry import TreeModelParamEntry, LeafNode, Node
from .parameter_entry_window_ui import Ui_MainWindow

if TYPE_CHECKING:
    from ...main_window import MetalGUI


class ParameterEntryWindow(QMainWindow):
    """Parameter entry window class"""

    def __init__(self,
                 qcomp_class: Type,
                 design: designs.DesignPlanar,
                 parent: QWidget = None,
                 gui: 'MetalGUI' = None):
        """
        Parameter Entry Widget when qcomponent is chosen from GUI's QLibrary
        Args:
            qcomp_class (Type): QComponent to be instantiated
            design (DesignPlanar): Current design being used
            parent (QWidget): Parent widget
            gui (MetalGUI): Metal GUI
        """

        super().__init__(parent)
        self.qcomp_class = qcomp_class
        self._design = design
        self._gui = gui
        self.setWindowTitle("New " + self.qcomp_class.__name__)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.param_dictionary = {}
        # set during generate_model_data as a backup in case tree need be
        # reloaded
        self.reset_param_dictionary = {}

        self.model = TreeModelParamEntry(self,
                                         self.ui.qcomponent_param_tree_view,
                                         design=self._design)

        self.ui.qcomponent_param_tree_view.setModel(self.model)
        self.ui.qcomponent_param_tree_view.setItemDelegate(ParamDelegate(self))

        self.statusBar().hide()

        # should be moved to qt designer
        self.ui.create_qcomp_button.clicked.connect(self.instantiate_qcomponent)
        self.ui.add_k_v_row_button.pressed.connect(self.add_k_v_row)
        self.ui.nest_dictionary_button.pressed.connect(self.add_k_dict_row)
        self.ui.remove_button.pressed.connect(self.delete_row)

    def setup_pew(self):
        """Setup pew"""
        self.generate_model_data()
        self._setup_help()
        self._setup_source()

    @property
    def qcomponent_file_path(self):
        """Get file path to qcomponent
        """
        component = self.qcomp_class
        module = inspect.getmodule(component)
        filepath = inspect.getfile(module)
        # TypeError
        return filepath

    # Exception Handling
    class QComponentParameterEntryExceptionDecorators():
        """
        All exceptions in QComponentParameterEntry should result in a pop-up window.
        This class contains the decorators that control exception handling for all functions
        in QComponentParameterEntry
        """

        @classmethod
        def entry_exception_pop_up_warning(cls, func: Callable):
            """
            Throws up critical QMessageBox with current exception in the event an exception is
            thrown by func

            Args:
                func (Callable): current function causing exceptions - should  be ONLY  qcpe instance methods
                    because decoraters
                assumes arg[0] is a self who has a valid logger

            """

            def wrapper(*args, **kwargs):
                try:

                    return func(*args, **kwargs)
                # if anticipated Exception throw up error window
                except (Exception) as lqce:

                    #cls.log_error(args[0], lqce, func, args, kwargs)
                    args[0].error_pop_up = QMessageBox()

                    error_message = "In function, " + str(
                        func.__name__) + "\n" + str(
                            lqce.__class__.__name__) + ":\n" + str(lqce)

                    # modality set by critical, Don't set Title -- will NOT show
                    # up on MacOs¥
                    args[0].error_pop_up.critical(args[0], "", error_message)

            return wrapper

    @QComponentParameterEntryExceptionDecorators.entry_exception_pop_up_warning
    def _setup_help(self):
        """Called when we need to set a new help"""

        component = self.qcomp_class
        if component is None:
            raise Exception("No Component found.")

        filepath = self.qcomponent_file_path
        doc_class = self.format_docstr(inspect.getdoc(component))
        doc_init = self.format_docstr(inspect.getdoc(component.__init__))

        text = """<body style="color:white;">"""
        text += f'''
        <div class="h1">Summary:</div>
        <table class="table ComponentHeader">
            <tbody>
                <tr> <th>Class</th><td>{component.__name__}</td></tr>
                <tr> <th>Module</th><td>{component.__class__.__module__}</td></tr>
                <tr> <th>Path</th><td style="text-color=#BBBBBB;"> {filepath}</td></tr>
            </tbody>
        </table>
        '''
        text += f'''
            <div class="h1">Class docstring:</div>
            {doc_class}
            <div class="h1">Init docstring:</div>
            {doc_init}
        '''
        text += "</body>"

        my_help = QtWidgets.QTextEdit()
        my_help.setReadOnly(True)
        my_help.setHtml(text)
        self.ui.tab_help.layout().addWidget(my_help)

    # pylint: disable-msg=no-self-use
    @QComponentParameterEntryExceptionDecorators.entry_exception_pop_up_warning
    def format_docstr(self, doc: Union[str, None]) -> str:
        """Format a docstring

        Args:
            doc (Union[str, None]): string to format

        Returns:
            str: formatted string
        """

        if doc is None:
            return ''
        doc = doc.strip()
        text = f"""
    <pre>
    <code class="DocString">{doc}</code>
    </pre>
        """
        return text

    @QComponentParameterEntryExceptionDecorators.entry_exception_pop_up_warning
    def _setup_source(self):
        """Called when we need to set up a new source"""

        filepath = self.qcomponent_file_path

        text_source = QtWidgets.QTextEdit(self.ui.tab_source)
        text_source.setReadOnly(True)

        text_doc = QtGui.QTextDocument(text_source)
        try:  # For source doc
            #import pygments
            from pygments import highlight
            from pygments.formatters import HtmlFormatter
            from pygments.lexers import get_lexer_by_name
        except ImportError as e:
            self._design.logger.error(
                f'Error: Could not load python package \'pygments\'; Error: {e}'
            )
            highlight = None
            HtmlFormatter = None
            get_lexer_by_name = None

        text = Path(filepath).read_text()
        if highlight is None:
            text_doc.setPlainText(text)
        else:
            lexer = get_lexer_by_name("python", stripall=True)
            formatter = HtmlFormatter(linenos='inline')
            self._html_css_lex = formatter.get_style_defs('.highlight')
            text_doc.setDefaultStyleSheet(self._html_css_lex)
            text_html = highlight(text, lexer, formatter)
            text_doc.setHtml(text_html)
        text_source.moveCursor(QtGui.QTextCursor.Start)
        text_source.ensureCursorVisible()
        text_source.setDocument(text_doc)

        self.ui.tab_source.layout().addWidget(text_source)

    @QComponentParameterEntryExceptionDecorators.entry_exception_pop_up_warning
    def add_k_v_row(self):
        """ Add key, value row to parent row based on what row is highlighted in treeview"""
        cur_index = self.ui.qcomponent_param_tree_view.currentIndex()

        key = "fake-param"
        value = "value"
        self.model.add_new_leaf_node(cur_index, key, value)

    @QComponentParameterEntryExceptionDecorators.entry_exception_pop_up_warning
    def add_k_dict_row(self):
        """ Add key, dictionary-value to parent row based on what row is highlighed in treeview"""
        cur_index = self.ui.qcomponent_param_tree_view.currentIndex()

        fake_dict = "fake-dict"
        fakekey = "key"
        fakevalue = "value"
        self.model.add_new_branch_node(cur_index, fake_dict, fakekey, fakevalue)

    @QComponentParameterEntryExceptionDecorators.entry_exception_pop_up_warning
    def delete_row(self):
        """Delete highlight row"""
        cur_index = self.ui.qcomponent_param_tree_view.currentIndex()
        self.model.delete_node(cur_index)

    @QComponentParameterEntryExceptionDecorators.entry_exception_pop_up_warning
    def generate_model_data(self):
        """
        Use QComponent's default_options and parameter (with typing) to populate Param Entry Window
        """

        param_dict = {}
        class_signature = signature(self.qcomp_class.__init__)

        for _, param in class_signature.parameters.items():
            if self.is_param_usable(param):
                if param.default:
                    param_dict[param.name] = param.default
                else:
                    class_name = self.qcomp_class.__name__ if param.name == 'name' else None
                    param_dict[param.name] = create_default_from_type(
                        param.annotation, param_name=class_name)

        try:

            options = self.qcomp_class.get_template_options(self._design)
        except Exception as e:
            self._design.logger.warning(
                f"Could not use template_options for component: {e}")
            if 'default_options' in self.qcomp_class.__dict__:
                options = self.qcomp_class.default_options

        if options is not None:
            copied_options = copy.deepcopy(options)
            param_dict['options'] = copied_options

        self.param_dictionary = param_dict
        self.reset_param_dictionary = copy.deepcopy(param_dict)
        self.model.init_load(param_dict)

    @staticmethod
    def is_param_usable(param):
        """Determines if a given parameter is usable."""
        if_no_default_then_ignore_params = {'options_connection_pads'}

        if (param.name == 'self' or param.name == 'design' or
                param.name == 'kwargs' or param.name == 'args'):
            return False

        if param.name in if_no_default_then_ignore_params:
            return param.default is not None

        return True

    @QComponentParameterEntryExceptionDecorators.entry_exception_pop_up_warning
    def instantiate_qcomponent(self):
        """Instantiate self.qcomp_class"""

        self.traverse_model_to_create_dictionary()

        self.qcomp_class(self._design, **self.current_dict)
        if self._gui is not None:  # for the sake of testing, we won't have gui
            self._gui.refresh()
            self._gui.autoscale()
        self.close()

    @QComponentParameterEntryExceptionDecorators.entry_exception_pop_up_warning
    def traverse_model_to_create_dictionary(self):
        """Traverse model to create parameter entry dictionary given to self.qcomp_class"""
        parameter_dict = {}
        r = self.model.root
        self.recursively_get_params(parameter_dict, r)

        self.current_dict = parameter_dict[""]

    @QComponentParameterEntryExceptionDecorators.entry_exception_pop_up_warning
    def recursively_get_params(self, parent_dict, cur_node):
        """Helper function for traverse_model_to_create_dictionary"""
        try:
            if isinstance(cur_node, LeafNode):
                parent_dict[cur_node.name] = cur_node.get_real_value()
                return

            c_dict = cur_node.get_empty_dictionary()
            parent_dict[cur_node.name] = c_dict
            for child in cur_node.children:

                self.recursively_get_params(c_dict, child[Node.NODE])
        except Exception as e:
            raise Exception(
                f"Unable to add node:{self.model.node_str(cur_node)} to {parent_dict} due to: {e}"
            ) from e


def create_parameter_entry_window(gui: 'MetalGUI',
                                  abs_file_path: str,
                                  parent=None) -> QtWidgets.QWidget:
    """Creates the spawned window that has the Parameter Entry Window
    """
    cur_class = get_class_from_abs_file_path(abs_file_path)
    if cur_class is None:
        gui.logger.error("Unable to get class from abs file: ", abs_file_path)
        return None

    if not parent:
        parent = gui.main_window  # gui.component_window.ui.tabHelp

    param_window = ParameterEntryWindow(cur_class, gui.design, parent, gui)

    param_window.dock = dockify(param_window, "New " + cur_class.__name__, gui)
    param_window.setup_pew()

    param_window.dock.show()
    param_window.dock.raise_()
    param_window.dock.activateWindow()

    return param_window


def dockify(main_window, docked_title, gui):
    """Dockify the given GUI

    Args:
        gui (MetalGUI): the GUI

    Returns:
        QDockWidget: the widget
    """
    # Dockify
    main_window.dock_widget = QDockWidget(docked_title, gui.main_window)
    dock = main_window.dock_widget
    dock.setWidget(main_window)

    dock.setAllowedAreas(Qt.RightDockWidgetArea)
    dock.setFloating(True)
    dock.resize(1200, 700)

    gui.logger.info("dockified window: " + docked_title)
    return dock


def get_class_from_abs_file_path(abs_file_path: str):
    """
    Gets the corresponding class object for the absolute file path to the file containing that
    class definition

    Args:
        abs_file_path (str): absolute file path to the file containing the QComponent class definition

    getting class from absolute file path -
    https://stackoverflow.com/questions/452969/does-python-have-an-equivalent-to-java-class-forname

    """
    qis_abs_path = abs_file_path[abs_file_path.index(__name__.split('.')[0]):]

    # Windows users' qis_abs_path may use os.sep or '/' due to PySide's
    # handling of file names
    qis_mod_path = qis_abs_path.replace(os.sep, '.')[:-len('.py')]
    qis_mod_path = qis_mod_path.replace("/",
                                        '.')  # users cannot use '/' in filename

    cur_module = importlib.import_module(qis_mod_path)
    members = inspect.getmembers(cur_module, inspect.isclass)
    class_owner = qis_mod_path.split('.')[-1]
    for memtup in members:
        if len(memtup) > 1:
            if str(memtup[1].__module__).endswith(class_owner):
                return memtup[1]


def create_default_from_type(my_t: type, param_name: str = None):
    """
    Create default values for a given type.

    Args:
        my_t (type): argument type.
        param_name (str): default parameter name (will replace "fake-param") for non-dictionary
            types.

    Returns:
        object: a default parameter.
    """
    if param_name is not None:
        return param_name + "-" + str(random.randint(0, 1000))
    if my_t == int:
        return 0
    elif my_t == float:
        return 0.0
    elif my_t == str:
        return "fake-param-" + str(random.randint(0, 1000))
    elif my_t == bool:
        return True
    elif my_t == dict:
        return {
            "fake-param-" + str(random.randint(0, 1000)): "fake-param"
        }  # can't have empty branch nodes
    elif my_t == OrderedDict:
        return OrderedDict({0: "zeroth"})
    elif my_t == Dict:
        return Dict(falseparam1=Dict(falseparam2="false-param",
                                     falseparam3="false-param"))
    elif my_t is None:
        return "fake-param-" + str(random.randint(0, 1000))
    else:
        return np.ndarray(1)
