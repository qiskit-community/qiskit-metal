"""
Logging widget

Credits, based on:
    https://stackoverflow.com/questions/28655198/best-way-to-display-logs-in-pyqt
    and thanks to Phil Reinhold

Returns:
    [type] -- [description]
"""
import logging
import random
import html
import collections

from pathlib import Path
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTextEdit, QAction

from ... import config, __version__
from .._handle_qt_messages import catch_exception_slot_pyqt

__all__ = ['Logging_Window_Widget', 'Logging_Hander_for_Log_Widget']


class Logging_Window_Widget(QTextEdit):
    timestamp_len = 19

    def __init__(self, img_path='/'):
        """
        Widget to handle logging. Based on QTextEdit, an advanced WYSIWYG viewer/editor
        supporting rich text formatting using HTML-style tags. It is optimized to handle
        large documents and to respond quickly to user input.
        """
        super().__init__()
        self.img_path = img_path
        self.handlers = [] # handles fo rhte loggers

        # Props of the Widget
        self.setContextMenuPolicy(Qt.ActionsContextMenu)  # local context menu
        self.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.text_format = QtGui.QTextCharFormat()
        self.text_format.setFontFamily('Consolas')
        # self.text_format.setForeground(QtGui.QBrush(QtGui.QColor('')))
        # self.text_format.setBackground(QtGui.QBrush(QtGui.QColor('')))

        # props
        self.tracked_loggers = {}
        self.logged_lines = collections.deque([], config.GUI_CONFIG.logger.num_lines)

        ### layout

        # Debug
        self.debug = QAction('Set level:  Debug', self)
        self.info = QAction('Set level:  Info', self)
        self.warning = QAction('Set level:  Warning', self)
        self.error = QAction('Set level:  Error', self)
        # Debug: Calls
        def make_f(lvl):
            name =  f'set_level_{lvl}'
            setattr(self, name, lambda : print('HG')) # self.set_level(lvl)
            func = getattr(self, name)
            return func

        self.debug.toggled.connect(self.wellcome_message)#make_f(logging.DEBUG))
        self.info.toggled.connect(make_f(logging.INFO))
        self.warning.toggled.connect(make_f(logging.WARNING))
        self.error.toggled.connect(make_f(logging.ERROR))
        # Debug: add menus
        self.addAction(self.debug)
        self.addAction(self.info)
        self.addAction(self.warning)
        self.addAction(self.error)

        self.separator0 = QAction('----------------', self)
        self.separator0.setEnabled(False)
        self.addAction(self.separator0)

        # Other menu buttons
        self.action_show_times = QAction('Display timestamps?', self)
        self.action_show_times.setCheckable(True)
        self.action_show_times.setChecked(False)
        self.action_show_times.toggled.connect(self.rebuild_all_messages)
        self.addAction(self.action_show_times)

        self.actino_scroll_auto = QAction('Autoscroll?', self)
        self.actino_scroll_auto.setCheckable(True)
        self.actino_scroll_auto.setChecked(True)
        self.addAction(self.actino_scroll_auto)

        self.print_action = QAction('Print all tips', self)
        self.print_action.toggled.connect(self.print_all_tips)
        self.addAction(self.print_action)

        self.separator = QAction('----------------', self)
        self.separator.setEnabled(False)
        self.addAction(self.separator)

        self.wellcome_message()

    def wellcome_message(self):
        img_txt = ''
        img_path = Path(self.img_path)/'metal_logo.png'
        if img_path.is_file():
            img_txt = f'<img src="{img_path}" height=80>'
        else:
            print('WARNING: wellcome_message could not locate img_path={img_path}')

        self.log_message(f'''<span class="INFO">{' '*self.timestamp_len}

        <table border="0" width="100%" ID="tableLogo" style="margin: 0px;">
            <tr>
                <td align="center">
                    <h3 align="center"  style="text-align: center; color:#00356B;">
                        Wellcome to Qiskit Metal
                    </h3>
                    v{__version__}
                </td>
                <td>  {img_txt} </td>
            </tr>
        </table>
        </span>
        <b>Tip: </b> {random.choice(config.GUI_CONFIG['tips'])}
        <br>''', format_as_html=2)

    def print_all_tips(self):
        """Prints all availabel tips in the log window
        """
        for tip in config.GUI_CONFIG['tips']:
            self.log_message(f'''<span class="INFO">{' '*self.timestamp_len} {tip} </span>''')

    @catch_exception_slot_pyqt
    def set_level(self, level):
        """Set level on all handelrs

        Arguments:
            level {[logging.level]} -- [eg.., logging.ERROR]
        """
        print(f'Setting level: {level}')
        if self.handlers:
            for handler in self.handlers:
                handler.setLevel(level)


    def add_logger(self, name):
        """Adds a logger to the widget

        Arguments:
            name {[type]} -- [description]
        """
        if name in self.tracked_loggers:
            return

        # Add action
        self.tracked_loggers[name] = QAction('View ' + name, self)
        action = self.tracked_loggers[name]
        action.setCheckable(True)
        action.setChecked(True)  # show the logging messages
        action.triggered.connect(self.rebuild_all_messages)
        self.addAction(action)

        # style
        self.document().setDefaultStyleSheet(config.GUI_CONFIG.logger.style)

    @property
    def get_all_checked(self):
        res = []
        for name, action in self.tracked_loggers.items():
            if action.isChecked():
                res += [name]
        return res

    def rebuild_all_messages(self):
        """
        Rebuild all lines form scratch
        """
        self.clear()
        for name, record in self.logged_lines:
            if name in self.get_all_checked:
                self.log_message(record, not (name is 'Errors'))

    def log_message_to(self, name, record):
        self.logged_lines.append((name, record))
        if name in self.get_all_checked:
            self.log_message(record, not (name is 'Errors'))

    def log_message(self, message, format_as_html=True):
        """Do the actial logging

        Arguments:
            message {[type]} -- [description]

        Keyword Arguments:
            format_as_html {bool} -- [Do format as html or not] (default: {True})
        """
        # set the write positon
        cursor = self.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()   # add a new block, which makes a new line

        # add message
        if format_as_html == True:
            if not self.action_show_times.isChecked():
                # remove the timestamp
                head, body = message.split('<pre>', 1)
                message = head + '<pre>' + body[1+self.timestamp_len:]  # get rid of timestamp
                #print('\n\n\n', message, 'HEAD', head, 'BODY', body, 'FINAL', body[1+self.timestamp_len:])
            #print(f'insertHtml: {message}')
            cursor.insertHtml(message)
        elif format_as_html == 2:
            cursor.insertHtml(message)
        else:
            cursor.insertText(message, self.text_format)

        # make sure that the message is visible and scrolled ot
        if self.actino_scroll_auto.isChecked():
            self.moveCursor(QtGui.QTextCursor.End)
        self.ensureCursorVisible()


class Logging_Hander_for_Log_Widget(logging.Handler):

    def __init__(self, name, parent, log_string=None):
        """
        Class to handle GUI logging.
        Handler instances dispatch logging events to specific destinations.
        For formatting
            https://docs.python.org/3/library/logging.html#logrecord-attributes
            _log_string = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')     # create formatter and add it to the handlers

        Arguments:
            name {[str]} -- [description]
            window {[QWidget]} -- [description]
        """
        super().__init__()

        # Params
        self.name = name
        self.log_panel = parent.logger_window

        # Formatter
        if log_string:
            self._log_string = log_string
        else:
            self._log_string = f'%(asctime).{Logging_Window_Widget.timestamp_len}s %(name)s: %(message)s [%(module)s.%(funcName)s]'
        self._log_formatter = logging.Formatter(self._log_string)
        self.setFormatter(self._log_formatter)

        # Add formatter
        self.log_panel.add_logger(name)
        self.log_panel.handlers += [self]

    def emit(self, record):
        """
        Do whatever it takes to actually log the specified logging record.
        Converts the characters '&', '<' and '>' in string s to HTML-safe sequences.
        Used to display text that might contain such characters in HTML.
        Arguments:
            record {[LogRecord]} -- [description]
        """
        html_record = html.escape(self.format(record))
        html_log_message = '<span class="%s"><pre>%s</pre></span>' % (record.levelname, html_record)
        self.log_panel.log_message_to(self.name, html_log_message)