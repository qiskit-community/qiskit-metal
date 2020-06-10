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

"""Main edit source code window,
based on pyqode.python: https://github.com/pyQode/pyqode.python

@author: Zlatko Minev 2020
"""
import importlib
import logging
import re
from typing import TYPE_CHECKING

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QTextCursor

try:
    from pyqode.python.backend import server
    from pyqode.core import api, modes, panels
    from pyqode.python import modes as pymodes, panels as pypanels, widgets
    from pyqode.python.folding import PythonFoldDetector
    from pyqode.python.backend.workers import defined_names
    # The above uses jedi
    import jedi
    import os

except ImportError as e:
    # TODO: report in a more visible way.
    # Maybe reaise exception.
    # If this line fails then the GUI can't start.
    raise ImportError('Error could not load `pyqode.python`\nPlease install. In a shell, try running: \n'
                      '  >> pip install pyqode.python --upgrade \n\n'
                      'For more, see https://github.com/pyQode/pyqode.python \n')

if TYPE_CHECKING:
    from ...main_window import MetalGUI, QMainWindowExtension

import warnings
warnings.filterwarnings("ignore", 'pyqode')


class MetalSourceEditor(widgets.PyCodeEditBase):
    """
    A source code editor based on pyQode.

    Editor features:
        - syntax highlighting
        - code completion (using jedi)
        - code folding
        - auto indentation
        - auto complete
        - comments mode (ctrl+/)
        - calltips mode
        - linters (pyflakes and pep8) modes + display panel
        - line number panel
        - builtin search and replace panel

    Create with
        gui.component_window.edit_source()

    Access with:
        self = gui.component_window.src_widgets[-1].ui.src_editor

        Note that thtehre can be more than one edit widet open.
        A refernece is kept to all of them in `gui.component_window.src_widgets`
    """
    # TODO: remember previous state, save to config like gui and recall when created
    # save font size too.  remmeber window properties and zoom level
    # TODO: Add error slot handling to all call funcitons below

    # MRO:
    # qiskit_metal._gui.widgets.edit_component.source_editor.MetalSourceEditor,
    # pyqode.python.widgets.code_edit.PyCodeEditBase,
    # pyqode.core.api.code_edit.CodeEdit,
    # PyQt5.QtWidgets.QPlainTextEdit,
    # PyQt5.QtWidgets.QAbstractScrollArea,
    # PyQt5.QtWidgets.QFrame,
    # PyQt5.QtWidgets.QWidget,
    # PyQt5.QtCore.QObject,
    # sip.wrapper,
    # PyQt5.QtGui.QPaintDevice,
    # sip.simplewrapper,
    # object

    def __init__(self, parent, **kwargs):
        # Foe help, see
        # https://github.com/pyQode/pyqode.python/blob/master/examples/custom.py

        super().__init__(parent, **kwargs)

        self.gui = None  # type: MetalGUI
        self.component_class_name = None  # type: str - 'TransmonPocket'
        # type: str - 'qiskit_metal.components.qubits.transmon_pocket'
        self.component_module_name = None
        # type: str - '/Users/zlatko.minev/qiskit_metal/qiskit_metal/components/qubits/transmon_pocket.py'
        self.component_module_path = None

        # starts the default pyqode.python server (which enable the jedi code
        # completion worker).
        self.backend.start(server.__file__)

        # some other modes/panels require the analyser mode, the best is to
        # install it first
        self.modes.append(modes.OutlineMode(defined_names))

        # --- core panels
        self.panels.append(panels.FoldingPanel())
        self.panels.append(panels.LineNumberPanel())
        self.panels.append(panels.CheckerPanel())
        self.panels.append(panels.SearchAndReplacePanel(),
                           panels.SearchAndReplacePanel.Position.BOTTOM)
        self.panels.append(panels.EncodingPanel(), api.Panel.Position.TOP)
        # add a context menu separator between editor's
        # builtin action and the python specific actions
        self.add_separator()

        # --- python specific panels
        self.panels.append(pypanels.QuickDocPanel(), api.Panel.Position.BOTTOM)

        ############################################################################
        #### core modes
        self.modes.append(modes.CaretLineHighlighterMode())
        self.modes.append(modes.CodeCompletionMode())
        self.modes.append(modes.ExtendedSelectionMode())
        self.modes.append(modes.FileWatcherMode())
        self.modes.append(modes.OccurrencesHighlighterMode())
        # self.modes.append(modes.RightMarginMode())
        self.modes.append(modes.SmartBackSpaceMode())
        self.modes.append(modes.SymbolMatcherMode())
        self.modes.append(modes.ZoomMode())

        # ---  python specific modes
        # Help: https://pythonhosted.org/pyqode.python/pyqode.python.modes.html

        # Comments/uncomments a set of lines using Ctrl+/.
        self.modes.append(pymodes.CommentsMode())

        # Shows function calltips.
        # This mode shows function/method call tips in a QToolTip using jedi.Script.call_signatures().
        # https://pythonhosted.org/pyqode.python/pyqode.python.modes.html#calltipsmode
        self.calltips_mode = pymodes.CalltipsMode()
        self.modes.append(self.calltip_mode)

        self.modes.append(pymodes.PyFlakesChecker())
        # self.modes.append(pymodes.PEP8CheckerMode())
        self.modes.append(pymodes.PyAutoCompleteMode())
        self.modes.append(pymodes.PyAutoIndentMode())
        self.modes.append(pymodes.PyIndenterMode())
        self.modes.append(pymodes.PythonSH(self.document()))
        self.syntax_highlighter.fold_detector = PythonFoldDetector()

        # --- handle modifed text in other application
        # self.textChanged.connect(self.check_modified) # user function

        # Options
        # self.file.safe_save  = False

        self.style_me()

    def style_me(self):
        self.setStyleSheet("""
    background-color: #f9f9f9;
    color: #000000;
            """)
        self.zoomIn(3)

    @property
    def logger(self) -> logging.Logger:
        return self.gui.logger

    def reload_file(self):
        encoding = self.file.encoding
        self.file.reload(encoding)
        self.file.reload()
        # self.update()
        self.logger.info('Source file reloaded.')

    def save_file(self):
        # TODO: warning: if the kernel is run as a differnt user, eg.., sudo,
        # then the file persmissions will change but for that user and the file
        # can read only for the base user.
        self.file.save()
        self.logger.info('Source file saved.')

    def open_file(self, filename: str):
        """Open a file

        Args:
            filename (str): [description]

        **Troubleshooting**

            If you get a strange permission error when opening hte file, but it otherwsie sems to more or less work fine
            it is because you probably opened in sudo before and now are not running in sudo.

            If the error is about Jedi:
                PermissionError: [Errno 13] Permission denied: '/Users/zlatko.minevibm.com/Library/Caches/Jedi/CPython-36-33/...

            Then there is an issue with the cache of self.file.
            The solution is to go in manuaally and delete the bad folder.
            I.e., in my case delete this Jedi folder:
                /Users/zlatko.minevibm.com/Library/Caches/Jedi/

            This can be also fixed using:
                import jedi
                jedi.settings.cache_directory

            I have tried to fix this using the permisison code below
        """

        ####################
        # Handle JEDI cache fridge bug: zkm
        # handle firdge possible error with permission of cache folder
        # TODO: may need to test more
        jedipath = jedi.settings.cache_directory
        if os.path.isdir(jedipath):  # dir already exists
            if not os.access(jedipath, os.W_OK):  # check that we have wrtite privs
                jedi.settings.cache_directory += '1'
        ######

        self.file.open(filename)  # , use_cached_encoding=False)

    def reload_module(self):
        if self.component_module_name:
            self.gui.design.reload_component(
                component_module_name=self.component_module_name,
                component_class_name=self.component_class_name)
            self.logger.info(
                f'Reloaded {self.component_class_name} from {self.component_module_name}')

    def rebuild_components(self):
        self.logger.debug('Source file rebuild started.')
        self.save_file()
        # print('saved')
        self.reload_module()
        # print('reloaded')
        # TODO: only rebuild those that have this type
        # for right now i will do all of tehm just for ease
        self.gui.rebuild()
        # print('rebuild')
        self.logger.info('Source file executed rebuild.')

    @property
    def edit_widget(self):
        return self.parent().parent()

    def set_component(self, class_name: str, module_name: str,
                      module_path: str):
        """Main function that set the components to be edited.

        Args:
            class_name (str): [description]
            module_name (str): [description]
            module_path (str): [description]
        """
        self.component_class_name = class_name
        self.component_module_name = module_name
        self.component_module_path = module_path

        self.logger.debug(f'Opening file {module_path}')
        self.open_file(module_path)

        edit_widget = self.edit_widget
        edit_widget.ui.lineSrcPath.setText(module_path)
        edit_widget.setWindowTitle(f'{class_name}: Edit Source')

        self.scroll_to()

    def scroll_to(self, text: str = 'def make('):
        """Scroll to the matched string
        """
        text = self.toPlainText()
        # index = text.find('def make(')
        index = re.search('def\s+make\(', text).start()

        if index:
            cursor = self.textCursor()
            cursor.setPosition(index)
            cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.MoveAnchor)
            self.setTextCursor(cursor)
            # self.ensureCursorVisible()
            self.centerCursor()
