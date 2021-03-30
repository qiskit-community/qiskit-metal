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
"""Main edit source code window,
based on pyqode.python: https://github.com/pyQode/pyqode.python
"""
import importlib
import inspect
import logging
import os
import pydoc
import re
import warnings
from typing import TYPE_CHECKING, List, Tuple, Union

import jedi
import PySide2
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtGui import QTextCursor
from PySide2.QtWidgets import QTextEdit

from qiskit_metal._gui.widgets.edit_component.metal_pyqode_folding_panel import MetalPyqodeFoldingPanel

__all__ = [
    'definition_generate_html', 'definition_get_source', 'doc_generate_html',
    'doc_get_object_from_info', 'get_definition_end_position',
    'get_definition_start_position'
]

try:
    from pyqode.python.backend import server
    from pyqode.qt import QtWidgets
    _test_ = QtWidgets.QDialog
except (ImportError, AttributeError) as e:
    print(
        "WARNING: Could not load `pyqode.qt` for PySide2. Installing pyqode.qt from special fork:\n"
        " python -m pip install -e git+https://github.com/jojurgens/pyqode.qt.git@master#egg=pyqode.qt"
    )
    # os.system(
    #     "python -m pip install -e git+https://github.com/jojurgens/pyqode.qt.git@master#egg=pyqode.qt"
    # )
    import shlex
    import subprocess
    cmd = "python -m pip install -e git+https://github.com/jojurgens/pyqode.qt.git@master#egg=pyqode.qt"
    print(f'\n\n*** Installing pyqode.qt for PySide2***\n$ {cmd}')
    scmd = shlex.split(cmd)
    result = subprocess.run(scmd, stdout=subprocess.PIPE, check=False)
    stderr = result.stderr
    stdout = result.stdout
    returncode = result.returncode
    print(f'\n****Exited with {returncode}')
    if stdout:
        print(f'\n****stdout****\n{stdout.decode()}')
    if stderr:
        print(f'\n****stderr****\n{stderr.decode()}')

try:
    from pyqode.core import api, modes, panels
    from pyqode.core.api import TextHelper
    from pyqode.python import modes as pymodes
    from pyqode.python import panels as pypanels
    from pyqode.python import widgets
    from pyqode.python.backend import server
    from pyqode.python.backend.workers import defined_names
    from pyqode.python.folding import PythonFoldDetector

except ImportError as e:
    # If this line fails then the GUI can't start.
    raise ImportError(
        'Error could not load `pyqode`\nPlease install. In a shell, try running: \n'
        '  >> pip install pyqode.python --upgrade \n\n'
        'For more, see https://github.com/pyQode/pyqode.python \n')

if TYPE_CHECKING:
    from ...main_window import MetalGUI, QMainWindowExtension

warnings.filterwarnings("ignore", 'pyqode')


class MetalSourceEditor(widgets.PyCodeEditBase):
    """
    A source code editor based on pyQode.

    This class inherits from the `widgets.PyCodeEditBase` class.

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

        Note that there can be more than one edit widget open.
        A reference is kept to all of them in `gui.component_window.src_widgets`
    """

    # TODO: remember previous state, save to config like gui and recall when created
    # save font size too.  remember window properties and zoom level
    # TODO: Add error slot handling to all call functions below

    # MRO:
    # qiskit_metal._gui.widgets.edit_component.source_editor.MetalSourceEditor,
    # pyqode.python.widgets.code_edit.PyCodeEditBase,
    # pyqode.core.api.code_edit.CodeEdit,
    # PySide2.QtWidgets.QPlainTextEdit,
    # PySide2.QtWidgets.QAbstractScrollArea,
    # PySide2.QtWidgets.QFrame,
    # PySide2.QtWidgets.QWidget,
    # PySide2.QtCore.QObject,
    # sip.wrapper,
    # PySide2.QtGui.QPaintDevice,
    # sip.simplewrapper,
    # object

    def __init__(self, parent, **kwargs):
        """
        Args:
            parent (QWidget): Parent widget
        """
        # Foe help, see
        # https://github.com/pyQode/pyqode.python/blob/master/examples/custom.py

        super().__init__(parent, **kwargs)

        self.gui = None  # type: MetalGUI
        self.component_class_name = None  # type: str - 'TransmonPocket'
        # type: str - 'qiskit_metal.qlibrary.qubits.transmon_pocket'
        self.component_module_name = None
        # type: str - '/Users/zlatko.minev/qiskit_metal/qiskit_metal/qlibrary/qubits/transmon_pocket.py'
        self.component_module_path = None

        # starts the default pyqode.python server (which enable the jedi code
        # completion worker).
        self.backend.start(server.__file__)

        # some other modes/panels require the analyser mode, the best is to
        # install it first
        self.modes.append(modes.OutlineMode(defined_names))

        # --- core panels
        # in pyqode/core/panels/folding.py there is:
        #   if os.environ['QT_API'].lower() not in PYQT5_API

        self.panels.append(MetalPyqodeFoldingPanel())
        self.panels.append(panels.LineNumberPanel())
        self.panels.append(panels.CheckerPanel())
        self.panels.append(panels.SearchAndReplacePanel(),
                           panels.SearchAndReplacePanel.Position.BOTTOM)
        self.panels.append(panels.EncodingPanel(), api.Panel.Position.TOP)
        # add a context menu separator between editor's
        # builtin action and the python specific actions
        self.add_separator()

        # --- python specific panels
        self.quick_doc_panel = pypanels.QuickDocPanel()
        self.panels.append(self.quick_doc_panel, api.Panel.Position.BOTTOM)

        ############################################################################
        # core modes
        self.modes.append(modes.CaretLineHighlighterMode())
        self.code_completion_mode = modes.CodeCompletionMode()
        self.modes.append(self.code_completion_mode)
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
        self.calltips_mode.tooltipDisplayRequested.connect(self.calltip_called)
        self.modes.append(self.calltips_mode)

        self.modes.append(pymodes.PyFlakesChecker())
        # self.modes.append(pymodes.PEP8CheckerMode())
        self.auto_complete_mode = pymodes.PyAutoCompleteMode()
        self.modes.append(self.auto_complete_mode)
        self.modes.append(pymodes.PyAutoIndentMode())
        self.modes.append(pymodes.PyIndenterMode())
        self.modes.append(pymodes.PythonSH(self.document()))
        self.syntax_highlighter.fold_detector = PythonFoldDetector()

        # --- handle modifed text in other application
        # self.textChanged.connect(self.check_modified) # user function

        # Options
        # self.file.safe_save  = False

        self.script = jedi.Script('')  # get overwritten in set

        self.style_me()

    def style_me(self):
        """Style the editor"""
        self.setStyleSheet("""
    background-color: #f9f9f9;
    color: #000000;
            """)
        self.zoomIn(3)

    @property
    def logger(self) -> logging.Logger:
        """Returns the logger"""
        return self.gui.logger

    def reload_file(self):
        """Reload the file"""
        encoding = self.file.encoding
        self.file.reload(encoding)
        self.file.reload()
        # self.update()
        self.logger.info('Source file reloaded.')

    def save_file(self):
        """Save the file"""
        # TODO: warning: if the kernel is run as a differnt user, eg.., sudo,
        # then the file persmissions will change but for that user and the file
        # can read only for the base user.
        self.file.save()
        self.logger.info('Source file saved.')

    def open_file(self, filename: str):
        """Open a file

        Args:
            filename (str): file to open

        **Troubleshooting**

            If you get a strange permission error when opening hte file, but it otherwise seems to more or less work fine
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

            I have tried to fix this using the permission code below
        """

        ####################
        # Handle JEDI cache fridge bug: zkm
        # handle firdge possible error with permission of cache folder
        # TODO: may need to test more
        jedipath = jedi.settings.cache_directory
        if os.path.isdir(jedipath):  # dir already exists
            if not os.access(jedipath,
                             os.W_OK):  # check that we have wrtite privs
                jedi.settings.cache_directory += '1'
        ######

        self.file.open(filename)  # , use_cached_encoding=False)

    def reload_module(self):
        """Reload the module"""
        if self.component_module_name:
            self.gui.design.reload_component(
                component_module_name=self.component_module_name,
                component_class_name=self.component_class_name)
            self.logger.info(
                f'Reloaded {self.component_class_name} from {self.component_module_name}'
            )

    def rebuild_components(self):
        """Rebuild the component"""
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

    def hide_help(self):
        """Hide the RHS sideebdar"""
        splitter = self.edit_widget.ui.splitter

        sizes = splitter.sizes()
        total = sum(sizes)

        if sizes[-1] < 1:  # hidden, now show
            # restore size
            spliter_size = self.__last_splitter_size if \
                            hasattr(self, '__last_splitter_size') else 400
            if total < spliter_size + 50:
                spliter_size = int(total / 2)
            splitter.setSizes([total - spliter_size,
                               spliter_size])  # hide the right side

        else:
            self.__last_splitter_size = sizes[-1]  # save for toggle
            splitter.setSizes([total, 0])  # hide the right side

    @property
    def edit_widget(self):
        """Returns the great-great-grandparent of the widget"""
        return self.parent().parent().parent().parent()

    def set_component(self, class_name: str, module_name: str,
                      module_path: str):
        """Main function that set the components to be edited.

        Args:
            class_name (str): The name of the class
            module_name (str): The name of the module
            module_path (str): The path to the module
        """
        self.component_class_name = class_name
        self.component_module_name = module_name
        self.component_module_path = module_path

        self.logger.debug(f'Opening file {module_path}')
        self.open_file(module_path)

        edit_widget = self.edit_widget
        win_title = f'Edit Source: {class_name}'
        edit_widget.setWindowTitle(win_title)
        edit_widget.dock_widget.setWindowTitle(win_title)
        edit_widget.ui.lineSrcPath.hide()  # wasted space
        edit_widget.statusBar().showMessage(str(module_path))
        # edit_widget.ui.lineSrcPath.setText(module_path)

        # Must be utf-8
        self.script = jedi.Script(self.toPlainText(), path=self.file.path)

        self.scroll_to()

    def scroll_to(self, text: str = 'def make('):
        """Scroll to the matched string.

        Args:
            text (str): Test to scroll to.  Defaults to 'def make('.
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

    def get_word_under_cursor(self) -> Tuple[PySide2.QtGui.QTextCursor, dict]:
        """Returns the cursor to select word udner it and info.

        Returns:
            tuple: PySide2.QtGui.QTextCursor, dict
        """
        tc = TextHelper(self).word_under_cursor(
            select_whole_word=True)  # type: PySide2.QtGui.QTextCursor
        word_info = {
            'code': self.toPlainText(),
            'line': tc.blockNumber(),
            'column': tc.columnNumber(),
            'path': self.file.path,
            'encoding': self.file.encoding
        }
        # print(word_info)
        return tc, word_info

    def get_definitions_under_cursor(self,
                                     offset=0
                                    ) -> List['jedi.api.classes.Definition']:
        """Get jedi

        Args:
            offset (int): Columns offset, such as -1.  Defaults to 0.

        Returns:
            list: Definitions under the cursor, or an empty list

        Raises:
            ValueError: Jedi couldn't find it
        """
        _, word_info = self.get_word_under_cursor()
        p = word_info

        self.script = jedi.Script(p['code'],
                                  line=1 + p['line'],
                                  column=p['column'] + offset,
                                  path=p['path'],
                                  encoding=p['encoding'])

        try:
            name_defns = self.script.infer(line=1 + word_info['line'],
                                           column=word_info['column'] + offset)
        except ValueError:
            print('Jedi did not find')
            name_defns = []

        return name_defns

    def set_help_doc(self, definitions: List['jedi.api.classes.Definition']):
        """Sets the help docs

        Args:
            definitions (List['jedi.api.classes.Definition']): Help defintions
        """
        if len(definitions) < 1:
            return

        if len(definitions) > 2:  # just take the first 2
            definitions = definitions[:2]

        csss = []
        text = ''
        for defn in definitions:
            # can check is .in_builtin_module() == True and not do
            if defn.full_name not in ['builtins.NoneType']:
                # For each found definition give the full docs.
                newtext, css = definition_generate_html(defn)
                text += newtext + '<br><br>'
                csss += [css]

        if len(csss) > 0:
            textEdit = self.edit_widget.ui.textEditHelp  # type: QTextEdit
            textEdit.document().setDefaultStyleSheet(csss[0])
            textEdit.setHtml(text)
            textEdit.moveCursor(QtGui.QTextCursor.Start)

    def set_doc_from_word_under_cursor(self, offset=0):
        """Set the doc based on the word under the cursor

        Args:
            offset (int): the offset.  Defaults to 0.
        """
        self.definitions = self.get_definitions_under_cursor(offset=offset)
        self.set_help_doc(self.definitions)

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent):
        """Double click leads to jedi inspection"""
        if event.button() == QtCore.Qt.LeftButton:
            self.set_doc_from_word_under_cursor(offset=0)

    def calltip_called(self, info: dict):
        """When a call tip is requested

        Args:
            info (dict): Dictionary of information

        Example Dictionary:

            .. code-block:: python

                {'call.module.name': 'shapely.geometry.geo',
                'call.call_name': 'box',
                'call.params': ['param minx', 'param miny', 'param maxx', 'param maxy', 'param ccw=True'],
                'call.index': 0,
                'call.bracket_start': [115, 12]}

        """
        self.set_doc_from_word_under_cursor(offset=-1)

        # Old method, before jedi
        #     # Get the object form the info dict
        #     obj = doc_get_object_from_info(info)
        #     text = doc_generate_html(obj)


css_base = """
  p {
      line-height: 1em;   /* within paragraph */
      margin-bottom: 1em; /* between paragraphs */
      padding-left: 0.25em;
  }
  .docstring{
    padding-left: 0.25em;
  }
  .myheading{
      font-weight:bold;
      color:#038000;
  }
  """


def definition_generate_html(defn: 'jedi.api.classes.Definition'):
    """Generate HTML definition

    Args:
        defn (jedi.api.classes.Definition): The jedit definition

    Returns:
        tuple: test, css
    """
    signatures = defn.get_signatures()
    doc_text = defn.docstring()
    doc_text = doc_text.replace(
        defn.name, f'<span style="color: #0900ff">{defn.name}</span>', 1)

    source_code, source_html, html_css_lex = definition_get_source(defn)

    css = css_base + html_css_lex

    text = \
f"""
<h4 class="myheading">Documentation</h4>
<pre class="docstring">{doc_text}</pre>

<hr>
<h4 class="myheading">About</h4>
<p><span class="myheading">Full name:</span> {defn.full_name} &nbsp; (<span class="myheading">Type:</span> {defn.type})</p>
<p><span class="myheading">Module name:</span> {defn.module_name}</p>
<p><span class="myheading">Module path:</span> {defn.module_path}</p>

<hr>
<h4 class="myheading">Source</h4>
{source_html}
"""

    return text, css


def definition_get_source(defn: 'jedi.api.classes.Definition',
                          formatter: HtmlFormatter = None):
    """Get the source code from definition

    Args:
        defn (jedi.api.classes.Definition): The jedit definition
        formatter (HtmlFormatter): The formatter.  Defaults to None.

    Returns:
        tuple: source_code, source_html, html_css_lex
    """
    # only in  > 0.17
    if hasattr(defn, 'get_definition_end_position'):
        end = defn.get_definition_end_position()
        start = defn.get_definition_start_position()
    else:
        end = get_definition_end_position(defn)
        start = get_definition_start_position(defn)

    if end is None or start is None:
        return '', '', ''

    num_lines = end[0] - start[0]

    #### HIGHOGH SOURCE
    lexer = get_lexer_by_name("python", stripall=True)
    if not formatter:
        formatter = HtmlFormatter(linenos='inline')
    html_css_lex = formatter.get_style_defs('.highlight')

    source_code = defn.get_line_code(0, num_lines)
    source_html = highlight(source_code, lexer, formatter)

    return source_code, source_html, html_css_lex


def get_definition_end_position(self):
    """
    The (row, column) of the end of the definition range. Rows start with
    1, columns start with 0.
    :rtype: Optional[Tuple[int, int]]

    Returns:
        int: The end position
    """
    if self._name.tree_name is None:
        return None
    definition = self._name.tree_name.get_definition()
    if definition is None:
        return self._name.tree_name.end_pos
    if self.type in ("function", "class"):
        last_leaf = definition.get_last_leaf()
        if last_leaf.type == "newline":
            return last_leaf.get_previous_leaf().end_pos
        return last_leaf.end_pos
    return definition.end_pos


def get_definition_start_position(self):
    """
    The (row, column) of the start of the definition range. Rows start with
    1, columns start with 0.
    :rtype: Optional[Tuple[int, int]]

    Returns:
        int: The start position
    """
    if self._name.tree_name is None:
        return None
    definition = self._name.tree_name.get_definition()
    if definition is None:
        return self._name.start_pos
    return definition.start_pos


################################################################################################################################
# UNUSED
def doc_generate_html(obj) -> str:
    """Generate formatted fdoc -- UNUSED

    Args:
        obj (object): The object

    Returns:
        str: Generated html

    Raises:
        TypeError: Objcet is the wrong type
        ValueError: Inspectoin failed
    """
    # Generate formatted fdoc
    # Get docstring
    # doc = inspect.getdoc(obj)
    # if doc:
    #     doc = inspect.cleandoc(doc)
    doc = pydoc.HTMLDoc()
    doc_text = doc.docroutine(obj)

    # Get file
    try:
        file = inspect.getfile(obj)
    except TypeError:
        file = ''

    # Get signature
    try:
        signature = inspect.signature(obj)
        signature_full = str(signature)
    except (ValueError, TypeError):
        signature_full = ''

    objtype = str(type(obj))

    ### Get the souruce code
    import linecache
    linecache.clearcache()
    # Clear the cache. Use this function if you no longer need lines from
    # files previously read using getline().
    source = inspect.getsource(obj)  # TODO: format

    text = """
<style type="text/css">
  p {
  line-height: 1em;   /* within paragraph */
  margin-bottom: 1em; /* between paragraphs */
  }
  .signature_type {
    color:#AA2b01;
    font-weight:bold;
  }
  .myheading{
      font-weight:bold;
      color:#AA2b01;
  }
</style>
""" + f"""
{doc_text}

<p><span class="signature_type"> file:</span> {file}</p>

<hr>
<h5 class="myheading">Source code:</h5>
<p>
{source}
</p>
"""

    return text


def doc_get_object_from_info(info: dict) -> object:
    """Get objects from given info

    Args:
        info (dict): The dictionary

    Returns:
        object: The retrieved object
    """

    module_name = info['call.module.name']
    functi_name = info['call.call_name']

    module = importlib.import_module(module_name)
    obj = getattr(module, functi_name)

    return obj
