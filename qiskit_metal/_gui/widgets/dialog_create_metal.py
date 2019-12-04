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
'''
Handle params for Creating an an object

@date: 2019
@author: Zlatko K Minev
'''

from pathlib import Path
import inspect
from inspect import signature, getfile

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QTreeView, QDockWidget, QHBoxLayout, QVBoxLayout,\
    QMainWindow, QListWidget, QTextEdit, QTreeWidget, QTreeWidgetItem, QLabel, \
    QLineEdit, QToolBar, QAction, QSlider, QInputDialog, QDialog, QPushButton, QTextEdit, QSizePolicy,\
    QFormLayout, QDialogButtonBox, QGroupBox, QComboBox, QSpinBox, QTabWidget
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QTextDocument, QFont

from ... import logger
from ...toolbox_python.utility_functions import display_options
from .trees.metal_parameter import parse_param_from_str
from .trees.amazing_tree_dict import Amazing_Dict_Tree_zkm

from copy import deepcopy

try:
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import get_lexer_by_name
except ImportError as e:
    logger.error('Could not load pygments; error = {e}')
    highlight = None
    HtmlFormatter = None
    get_lexer_by_name = None

try:
    import docutils
except ImportError as e:
    logger.error('Could not load docutils; error = {e}')
    docutils = None




class Dialog_create_metal(QDialog):

    html_style = """
table, th, td {
    border: 0px;
    padding: 0px;
}
table, th, td {
    background-color: #eff8ef;
    padding: 0px;
    border: 0px;
    height: 0px;
}
    """

    html_style_connectors = """
/* includes alternating gray and white with on-hover color */

.zkmheading {
    color : #006400;
}
table {
  border-collapse: collapse;
}

table, th, td {
  border: 1px solid black;
}

td, th {
    padding: 5px;
}

th {
    font-size:large;
    text-align:left;
}

tr:nth-child(even) {
    background: #E0E0E0;
}

tr:hover {
    background: silver;
    cursor: pointer;
}
    """

    def __init__(self, parent, my_class,
                 WindowTitle=None):
        '''

        Just gets  adictionary to use to create metal.

        Run self.show()
        '''
        super().__init__(parent)

        # Params
        self.my_class = my_class
        self.results = {}
        self.logger = parent.logger
        self.options = self.get_default_options(my_class)

        # Window style
        if not WindowTitle:
            WindowTitle = f'Create Metal Object `{my_class.__name__}`'
        self.setWindowTitle(WindowTitle)
        self.setModal(False)

        # Layout
        self.layout = QHBoxLayout()
        self.left_panel = QTabWidget() # QGroupBox(f"{my_class.__name__}")
        self.right_panel = QGroupBox('Options to create')
        self.layout.addWidget(self.left_panel, 1.4)  # strech factor
        self.layout.addWidget(self.right_panel)

        self.make_left_panel(self.left_panel)
        self.make_right_panel(self.right_panel)

        # Finalize
        self.resize(900, 600)
        self.setLayout(self.layout)

    def get_default_options(self, cls):
        '''
            Get the object default options
        '''
        from ... import DEFAULT_OPTIONS
        return cls.create_default_options()

    def make_left_panel(self, parent):
        self.layout_left = QVBoxLayout()

        self.tabs = parent
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()

        # Add tabs and layout
        self.tabs.addTab(self.tab1,"Description / Help")
        self.tabs.addTab(self.tab2,"Source Code")
        self.tabs.addTab(self.tab3,"Formatted Docstring")
        self.tabs.addTab(self.tab4,"Connectors")

        self.tab1.layout = QVBoxLayout()
        self.tab2.layout = QVBoxLayout()
        self.tab3.layout = QVBoxLayout()
        self.tab4.layout = QVBoxLayout()

        self.tab1.setLayout(self.tab1.layout)
        self.tab2.setLayout(self.tab2.layout)
        self.tab3.setLayout(self.tab3.layout)
        self.tab4.setLayout(self.tab4.layout)

        # i dont think this really does anything
        for layout in [self.tab1.layout, self.tab2.layout,
                       self.tab3.layout, self.tab4.layout,
                       self.layout_left]:
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

        my_class = self.my_class

        def create_doc():
            # Create widgets
            doc = QTextEdit(self)
            document = QTextDocument()

            # Style doc
            doc.setDocument(document)
            doc.setReadOnly(True)
            doc.setMinimumSize(QSize(100, 200))
            doc.setAcceptRichText(True)
            doc.setAutoFillBackground(True)
            doc.setStyleSheet("background-color: rgb(250, 250, 250);")
            doc.setLineWrapMode(QTextEdit.NoWrap)
            # doc.setLineWrapMode(QTextEdit.WidgetWidth)
            #doc.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            # doc.setMinimumHeight(50)
            #doc.setBaseSize(100, 50)

            # Style documents monoscaped font
            font = document.defaultFont()
            font.setFamily("monospace")
            document.setDefaultFont(font)

            return doc, document


        # TAB 1
        if 1:
            doc, document = create_doc()
            self.doc = doc
            self.document = document

            ### Set the text
            text = inspect.getdoc(my_class)

            icon_path = self.parent()._get_metal_icon_path(my_class)
            icon_text = ''
            if not (icon_path is None):
                icon_text = f'''<b>Icon:</b>
                <img src="{icon_path}"></img><br> '''

            document.setDefaultStyleSheet(self.html_style)
            text = "<body>"\
            f"""<b>Class:</b><br>&nbsp;<span style="font-weight:bold; color:#006400;">{my_class.__name__}</span> {signature(my_class)}<br>
            {icon_text}
            <b>Description:</b>"""\
            f"""<pre style="background-color: #EBECE4;"><code>{text.strip()}</code></pre>
            </body>
            """.strip().replace('\n', '<br>')
            document.setHtml(text.strip())

            self.tab1.layout.addWidget(doc)

        if 1:
            # TAB 2
            doc, document = create_doc()
            self.doc2 = doc
            self.document2 = document

            # Text to go in document
            text = Path(getfile(my_class)).read_text()
            #text = f'<body>{text}</body>'

            if not(highlight is None):
                lexer = get_lexer_by_name("python", stripall=True)
                formatter = HtmlFormatter(linenos='inline')
                self.html_css_lex = formatter.get_style_defs('.highlight')

                document.setDefaultStyleSheet(self.html_css_lex)
                text_html = highlight(text, lexer, formatter)
                document.setHtml(text_html)

            else:
                document.setPlainText(text)

            self.tab2.layout.addWidget(doc)

        if 1:
            # TAB 3
            doc, document = create_doc()
            self.doc3 = doc
            self.document3 = document

            # Text to go in document
            text = inspect.getdoc(my_class)
            document.setPlainText('Doc extension currently not loaded.')
            self.tab3.layout.addWidget(doc)

        if 0: # TAB 3 set text doc
            if not(docutils is None):
                try:
                    from docutils.examples import html_parts
                    res = html_parts(text)

                    document.setDefaultStyleSheet(res['stylesheet'])
                    text_html = str(res['body']).strip()
                    document.setHtml(text_html)

                except Exception as e:
                    document.setPlainText('ERROR generating docstring with docutils.\n'
                                          f'ERROR:\n\n{e}')

            else:
                document.setPlainText('ERROR loading plugin: import docutils failed.\n'
                                      ' Is this package installed?\n'
                                      ' If you would like to use it, please install.\n')

        if 1:
            # TAB 4
            #TODO: Abstract away the connector tab and make usable in other places to see
            doc, document = create_doc()
            self.doc4 = doc
            self.document4 = document

            # Text to go in document
            gui = self.parent() # assume gui
            connectors = gui.design.connectors

            text =  '<h3 class="zkmheading">Available connectors:</h3>\n'+\
                    '<table> <tr><th>Name</th><th>Properties</th></tr>\n'+\
                    '\n'.join([ f"""<tr style="background:{'#F0F0F0' if num % 2 else '#e3e3e3'};">
                                         <td style="font-weight:bold;">{k}</td>
                                         <td>{str(v).strip()}</td>
                                    </tr>""" \
                        for num, (k, v) in enumerate(connectors.items()) ]) +\
                    '</table>'

            document.setDefaultStyleSheet(self.html_style_connectors)
            document.setHtml(text)
            self.tab4.layout.addWidget(doc)

        # Scroll to top
        for doc in [self.doc, self.doc2, self.doc3, self.doc4]:
            cursor = doc.textCursor()
            cursor.setPosition(0)
            doc.setTextCursor(cursor)

        #self.layout_left.addWidget(self.tabs)
        parent.setLayout(self.layout_left)

    def make_right_panel(self, parent):
        self.right_layout = QVBoxLayout()

        if 1:  # Form with name
            self.layout_form = QFormLayout()
            self.form_name = QLineEdit()
            self.label_name = QLabel('Object name:')
            if 1:
                font = QFont()
                font.setBold(True)
                self.label_name.setFont(font)
            self.layout_form.addRow(self.label_name, self.form_name)
            self.right_layout.addLayout(self.layout_form)

        if 1:
            self.lbl = QLabel('Help: Right click an item on the tree dictionary below to pop up menu to create sub-dictionaries or string items.')
            self.lbl.setWordWrap(True)
            self.right_layout.addWidget(self.lbl)

        if 1:  # Tree
            self.tree = Amazing_Dict_Tree_zkm(self, self.options,
                                              nameme='Creation options',
                                              logger=self.logger
                                              )
            self.tree.setMinimumSize(QSize(200, 200))
            self.right_layout.addWidget(self.tree)

        if 1:  # Ok and Cancel
            buttonBox = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
            buttonBox.accepted.connect(self.on_accept)
            buttonBox.rejected.connect(self.on_reject)
            self.buttonBox = buttonBox
            self.right_layout.addWidget(buttonBox)

        parent.setLayout(self.right_layout)

    def _get_data(self):
        self.obj_name = self.form_name.text()
        self.results = {'name': self.obj_name, 'options': self.options}
        return self.results

    def on_accept(self):
        '''Hides the modal dialog and sets the result code to Accepted.'''
        # Handle data here self.edit.text()
        self.accept()
        self._get_data()

    def on_reject(self):
        '''Hides the modal dialog and sets the result code to Rejected.'''
        self.reject()

    def get_params(self):
        '''
        result:0 or 1
        results:dict
        '''
        result = self.exec()
        return result, self.results