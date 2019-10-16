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

from inspect import signature
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QTreeView, QDockWidget, QHBoxLayout, QVBoxLayout,\
    QMainWindow, QListWidget, QTextEdit, QTreeWidget, QTreeWidgetItem, QLabel, \
    QLineEdit, QToolBar, QAction, QSlider, QInputDialog, QDialog, QPushButton, QTextEdit, QSizePolicy,\
    QFormLayout, QDialogButtonBox, QGroupBox, QComboBox, QSpinBox
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QTextDocument, QFont

from ...toolbox.utility_functions import display_options
from .trees.metal_parameter import parse_param_from_str
from .trees.amazing_tree_dict import Amazing_Dict_Tree_zkm

from copy import deepcopy


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

    def __init__(self, parent, my_class,
                 WindowTitle=None):
        '''
        Run self.show()
        '''
        super().__init__(parent)

        # Params
        self.my_class = my_class
        self.results = {}
        self.logger = parent.logger

        # Window style
        if not WindowTitle:
            WindowTitle = f'Create Metal Object `{my_class.__name__}`'
        self.setWindowTitle(WindowTitle)
        self.setModal(False)

        # Default options
        from ... import DEFAULT_OPTIONS
        self.options = deepcopy(DEFAULT_OPTIONS[my_class.__name__])

        # Layout
        self.layout = QHBoxLayout()
        self.left_panel = QGroupBox(f"{my_class.__name__}")
        self.right_panel = QGroupBox('Default parameters')
        self.layout.addWidget(self.left_panel, 1.4)  # strech factor
        self.layout.addWidget(self.right_panel)

        self.make_left_panel(self.left_panel)
        self.make_right_panel(self.right_panel)

        # Finalize
        self.resize(700, 450)
        self.setLayout(self.layout)

    def make_left_panel(self, parent):
        self.layout_left = QVBoxLayout()

        if 1:
            my_class = self.my_class

            # Create widgets
            self.doc = QTextEdit(self)
            document = QTextDocument()
            document.setDefaultStyleSheet(self.html_style)
            text = f"""
            <body><b>Class:</b><br><font color='green'>{my_class.__name__}</font> {signature(my_class)}<br>
            <b>Description:</b>
                <pre style="background-color: #EBECE4;"><code>{my_class.__doc__.strip()}</code></pre>
            </body>""".strip().replace('\n', '<br>')
            document.setHtml(text.strip())

            self.doc.setDocument(document)
            self.doc.setReadOnly(True)

            doc = self.doc
            doc.setMinimumSize(QSize(100, 200))
            doc.setAcceptRichText(True)
            doc.setAutoFillBackground(True)
            doc.setStyleSheet("background-color: rgb(250, 250, 250);")
            # doc.setLineWrapMode(QTextEdit.WidgetWidth)
            doc.setLineWrapMode(QTextEdit.NoWrap)
            #doc.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            # doc.setMinimumHeight(50)
            #doc.setBaseSize(100, 50)

            # monoscpaed font
            font = document.defaultFont()
            font.setFamily("monospace")
            document.setDefaultFont(font)

            self.layout_left.addWidget(self.doc)

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


#form = QFormLayout()
        #self.texts_key = ['name'] + my_class.__gui_creation_args__
        #self.texts = []

        # make nicker promit
        # for arg_name in self.texts_key:
        #    item = QTextEdit() if arg_name.startswith('option') else QLineEdit()
        #    form.addRow(QLabel(arg_name), item)
        #    self.texts += [item]
        #    #value, used_ast = parse_param_from_str(text)
        #    #print('value=',value, ' used_ast=',used_ast)
        #    #my_args[arg_name] = value

        # make gneral to handle all arguments here
        #from inspect import signature
        #sig = signature(Metal_Transmon_Pocket)
        # for pname, p in sig.parameters.items():
        #    print(pname, p.empty, p.default, p.kind)

        #form.addRow(QLabel("Country:"), QComboBox())
        #form.addRow(QLabel("Age:"), QSpinBox())
        #self.form = form
        # self.formGroupBox.setLayout(form)
        # layout1.addWidget(self.formGroupBox)

        # add todialog
        # layout.addLayout(layout1)
        # self.setLayout(layout)

        # self.ok = QPushButton("Ok")
        # self.cancel = QPushButton("cancel")
        # layout2.addWidget(self.cancel)
        # layout2.addWidget(self.ok)
        # # Add button signal to greetings slot
        # self.ok.clicked.connect(self.on_ok)
        # self.cancel.clicked.connect(self.on_cancel)

    # def _get_data(self):
        # self.result_values = []
        # for i, t in enumerate(self.texts):
        #     if isinstance(t, QTextEdit):
        #         text = t.toPlainText() # QTextEdit
        #     else:
        #         text = t.text() # QLineEdit
        #     value, used_ast = parse_param_from_str(text)
        #     if value == '':
        #         value = None
        #     #print('value=', value, ' used_ast=',used_ast)
        #     self.result_values  += [value]
        #     self.results[self.texts_key[i]] = value
