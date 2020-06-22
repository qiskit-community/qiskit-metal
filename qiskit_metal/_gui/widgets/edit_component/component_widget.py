# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Main module that handles a component  inside the main window.
@author: Zlatko Minev
@date: 2020
"""

import ast
import inspect
from inspect import getfile, signature
from pathlib import Path
from typing import TYPE_CHECKING, Union

import numpy as np
import PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QFileDialog,
                             QLabel, QMainWindow, QMessageBox, QTabWidget)

from .... import logger
from ...component_widget_ui import Ui_ComponentWidget
from ...utility._handle_qt_messages import catch_exception_slot_pyqt
from .source_editor_widget import create_source_edit_widget
# from .table_model_options import QTableModel_Options
from .tree_model_options import QTreeModel_Options

if TYPE_CHECKING:
    from ...main_window import MetalGUI, QMainWindowExtension
    from ....components import QComponent
    from ....designs import QDesign

try:  # For source doc
    import pygments
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import get_lexer_by_name
except ImportError as e:
    logger.error(
        f'Error: Could not load python package \'pygments\'; Error: {e}')
    highlight = None
    HtmlFormatter = None
    get_lexer_by_name = None

# TODO: move to conifg
textHelp_css_style = """
body {
  background-color: #f7f7f7;
  color: #000000;
  text-color : #000000;
}

.ComponentHeader th {
    text-align: left;
    background-color: #EEEEEE;
    padding-right: 10px;
}

.ComponentHeader td {
    text-align: left;
    padding-left: 5px;
    color: brown;
}

.ComponentHeader {
    font-size: 1.5em;
    text-align: left;
    margin-top: 5px;
    margin-bottom: 5px;
    padding-right: 40px;
}

.h1 {
  display: block;
  font-size: large;
  margin-top: 0.67em;
  margin-bottom: 0.67em;
  margin-left: 0;
  margin-right: 0;
  font-weight: bold;
}

/*.DocString {
    font-family: monospace;
}*/
"""


def format_docstr(doc: Union[str, None]) -> str:
    if doc is None:
        return ''
    doc = doc.strip()
    text = f"""
<pre style="background-color: #EBECE4;">
<code class="DocString">{doc}</code>
</pre>
    """
    return text


def create_QTextDocument(doc: QtWidgets.QTextEdit) -> QtGui.QTextDocument:
    """
    For source doc.

    Access with gui.component_window.src_doc
    """
    document = QtGui.QTextDocument()

    # Style doc
    doc.setDocument(document)

    # Style documents monoscaped font
    font = document.defaultFont()
    if hasattr(QFont, "Monospace"):
        # when not available
        font.setStyleHint(QFont.Monospace)
    else:
        font.setStyleHint(QFont.Courier)
    font.setFamily("Courier")
    document.setDefaultFont(font)

    return document


class ComponentWidget(QTabWidget):
    """
    This is just a handler (container) for the UI; it a child object of the main gui.

    PyQt5 Signal / Slots Extensions:
        The UI can call up to this class to execeute button clicks for instance
        Extensiosn in qt designer on signals/slots are linked to this class

    **Access:**
        gui.component_window
    """

    def __init__(self, gui: 'MetalGUI', parent: QtWidgets.QWidget):
        # Parent is usually a dock component

        super().__init__(parent)

        # Parent GUI related
        self.gui = gui
        self.logger = gui.logger
        self.statusbar_label = gui.statusbar_label

        # UI
        self.ui = Ui_ComponentWidget()
        self.ui.setupUi(self)

        self.component_name = None  # type: str

        # Parameter model and table view
        self.model = QTreeModel_Options(self, gui, self.ui.treeView)
        self.ui.treeView.setModel(self.model)
        self.ui.treeView.setVerticalScrollMode(
            QAbstractItemView.ScrollPerPixel)
        self.ui.treeView.setHorizontalScrollMode(
            QAbstractItemView.ScrollPerPixel)

        # Source Code
        # palette = self.ui.textSource.palette()
        # palette.color(palette.Text).name()
        # palette.setColor(palette.Text, QColor('#000000'))
        # palette.setColor(palette.WindowText, QColor('#000000'))
        # self.ui.textSource.setPalette(palette)
        self.ui.textSource.setStyleSheet("""
    color: #000000;
            """)
        self.src_doc = create_QTextDocument(self.ui.textSource)
        self._html_css_lex = None  # type: pygments.formatters.html.HtmlFormatter
        self.src_widgets = []  # type: List[QtWidgets.QWidget]

        # Help stylesheet
        document = self.ui.textHelp.document()
        document.setDefaultStyleSheet(textHelp_css_style)

        self.fixup_ui()

    def fixup_ui(self):
        """For some reasonthe following i couldnt do in the ui successfully, so doing here.
        """
        # Clicked
        # This signal is emitted when the button is activated (i.e., pressed down then released
        # while the mouse cursor is inside the button), when the shortcut key is typed, or when
        # click() or animateClick() is called. Notably, this signal is not emitted if you call
        #  setDown(), setChecked() or toggle().

        # for some reason i need to clear the stylsheet. must be a bug inthis pyqt versino
        s1 = self.ui.btn_edit_src.styleSheet()
        s2 = self.ui.pushButtonEditSource.styleSheet()
        self.ui.btn_edit_src.setStyleSheet('')
        self.ui.pushButtonEditSource.setStyleSheet('')
        # connect
        self.ui.btn_edit_src.clicked.connect(self.edit_source)
        self.ui.pushButtonEditSource.clicked.connect(self.edit_source)
        # restore stylsheet
        self.ui.btn_edit_src.setStyleSheet(s1)
        self.ui.pushButtonEditSource.setStyleSheet(s2)

    @property
    def design(self):
        return self.gui.design

    @property
    def component(self):
        if self.design:
            return self.design.components[self.component_name]
            # return self.design.components.get(self.component_name, None)

    def set_component(self, name: str):
        """
        Main interface to set the component (by name)
        Arguments:
            name {str} -- if None, then clears
        """
        self.component_name = name

        if name is None:
            # TODO: handle case when name is none: just clear all
            # TODO: handle case where the component is made in jupyter notebook
            self.force_refresh()
            return

        component = self.component

        # Labels
        # ) from {component.__class__.__module__}
        label_text = f"{component.name}   :   {component.__class__.__name__}   :   {component.__class__.__module__}"
        # self.ui.labelComponentName.setText(label_text)
        # self.ui.labelComponentName.setCursorPosition(0)  # Move to left
        self.setWindowTitle(label_text)
        self.parent().setWindowTitle(label_text)

        self._set_source()
        self._set_help()

        self.force_refresh()
        self.ui.treeView.autoresize_columns()  # resize columns

    def force_refresh(self):
        self.model.refresh()

    def _set_help(self):
        """Called when we need to set a new help"""
        # See also
        # from IPython.core import oinspect
        # oinspect.getdoc(SampleClass)
        # from IPython.core.oinspect import Inspector
        # ins = Inspector()
        # ins.pdoc(SampleClass)

        component = self.component
        if component is None:
            return

        filepath = inspect.getfile(component.__class__)
        doc_class = format_docstr(inspect.getdoc(component))
        doc_init = format_docstr(inspect.getdoc(component.__init__))

        text = "<body>"
        text += f'''
        <div class="h1">Summary:</div>
        <table class="table ComponentHeader">
            <tbody>
                <tr> <th>Name</th> <td>{component.name}</td></tr>
                <tr> <th>Class</th><td>{component.__class__.__name__}</td></tr>
                <tr> <th>Module</th><td>{component.__class__.__module__}</td></tr>
                <tr> <th>Path </th> <td style="text-color=#BBBBBB;"> {filepath}</td></tr>
            </tbody>
        </table>
        '''

        # get image
        # if image_path:
        #     text += f'''
        #     <img class="ComponentImage" src="{image_path}"></img>
        #     '''

        text += f'''
            <div class="h1">Class docstring:</div>
            {doc_class}
            <div class="h1">Init docstring:</div>
            {doc_init}
        '''
        text += "</body>"

        self.ui.textHelp.setHtml(text)

    def _set_source(self):
        """Called when we need to set a new help"""
        filepath = getfile(self.component.__class__)
        self.ui.lineSourcePath.setText(filepath)

        document = self.src_doc

        text = Path(filepath).read_text()

        if not (highlight is None):
            lexer = get_lexer_by_name("python", stripall=True)
            formatter = HtmlFormatter(linenos='inline')
            self._html_css_lex = formatter.get_style_defs('.highlight')

            document.setDefaultStyleSheet(self._html_css_lex)
            text_html = highlight(text, lexer, formatter)
            document.setHtml(text_html)

        else:
            document.setPlainText(text)

        textEdit = self.ui.textSource
        textEdit.moveCursor(QtGui.QTextCursor.Start)
        textEdit.ensureCursorVisible()
    # @catch_exception_slot_pyqt()

    def edit_source(self, *args, parent=None):
        """Calls the edit source window
        gui.component_window.edit_source()
        """

        self.logger.debug(f"edit_source: {args}")

        if self.component is not None:
            class_name = self.component.__class__.__name__
            module_name = self.component.__class__.__module__
            module_path = inspect.getfile(self.component.__class__)
            self.src_widgets += [
                create_source_edit_widget(
                    self.gui, class_name, module_name, module_path, parent=parent)
            ]
            self.logger.info('Edit sources window created. '
                             'Please find on your screen.')
        else:
            QtWidgets.QMessageBox.warning(self,
                                          "Missing Selected Component",
                                          "Please first select a component to edit, by clicking "
                                          "one in the desing components menu.")
