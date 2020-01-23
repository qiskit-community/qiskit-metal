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

__all__ = ['LoggingWindowWidget', 'LoggingHandlerForLogWidget']


class LoggingWindowWidget(QTextEdit):

    timestamp_len = 19
    _logo = 'metal_logo.png'

    def __init__(self, img_path='/'):
        """
        Widget to handle logging. Based on QTextEdit, an advanced WYSIWYG viewer/editor
        supporting rich text formatting using HTML-style tags. It is optimized to handle
        large documents and to respond quickly to user input.
        """
        super().__init__()

        self.img_path = img_path

        # handles for hte loggers
        self.handlers = []

        # Props of the Widget
        self.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.text_format = QtGui.QTextCharFormat()
        self.text_format.setFontFamily('Consolas')

        # props
        self.tracked_loggers = {}
        self.logged_lines = collections.deque([], config.GUI_CONFIG.logger.num_lines)

        # Menu - setup_menu
        self.debug = None
        self.info = None
        self.warning = None
        self.error = None
        self.separator0 = None
        self.action_show_times = None
        self.actino_scroll_auto = None
        self.action_print_tips = None
        self.separator = None

        self.setup_menu()

    def setup_menu(self):

        # the widget displays its QWidget::actions() as context menu.
        # i.e., local context menu
        self.setContextMenuPolicy(Qt.ActionsContextMenu)

        # Debug
        self.debug = QAction('Filter level:  Debug', self)
        self.info = QAction('Filter level:  Info', self)
        self.warning = QAction('Filter level:  Warning', self)
        self.error = QAction('Filter level:  Error', self)

        # Debug: Calls
        def make_f(lvl):
            name = f'set_level_{lvl}'
            setattr(self, name, lambda: self.set_level(lvl))  # self.set_level(lvl)
            func = getattr(self, name)
            return func

        self.debug.triggered.connect(make_f(logging.DEBUG))  # make_f(logging.DEBUG))
        self.info.triggered.connect(make_f(logging.INFO))
        self.warning.triggered.connect(make_f(logging.WARNING))
        self.error.triggered.connect(make_f(logging.ERROR))

        #self.separator0 = QAction('----------------', self)
        #self.separator0.setEnabled(False)
        #self.addAction(self.separator0)

        # Other menu buttons
        self.action_show_times = QAction('Display timestamps', self)
        self.action_show_times.setCheckable(True)
        self.action_show_times.setChecked(False)
        self.action_show_times.triggered.connect(self.report_all_messages)


        self.actino_scroll_auto = QAction('Autoscroll', self)
        self.actino_scroll_auto.setCheckable(True)
        self.actino_scroll_auto.setChecked(True)

        self.action_print_tips = QAction('Print all tips', self)
        self.action_print_tips.triggered.connect(self.print_all_tips)

        # Add actions to menu
        self.addAction(self.action_print_tips)
        self.addAction(self.action_show_times)
        self.addAction(self.actino_scroll_auto)
        self.addAction(self.debug)
        self.addAction(self.info)
        self.addAction(self.warning)
        self.addAction(self.error)

    def wellcome_message(self):
        img_txt = ''

        # Logo
        img_path = Path(self.img_path)/self._logo
        if img_path.is_file():
            img_txt = f'<img src="{img_path}" height=80>'
        else:
            print('WARNING: wellcome_message could not locate img_path={img_path}')

        # Main message
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
            self.log_message(f'''<span class="INFO">{' '*self.timestamp_len} \u2022 {tip} </span>''')

    def set_level(self, level):
        """Set level on all handelrs

        Arguments:
            level {[logging.level]} -- [eg.., logging.ERROR]
        """
        #print(f'Setting level: {level}')
        if self.handlers:
            for handler in self.handlers:
                handler.setLevel(level)

    def add_logger(self, name):
        """Adds a logger name to the widget.
        Does not actully take in the logger itself.

            - adds name to tracked_loggers, as QAction
            - adds an action to the menu

        Logger is added with
            gui.logger.addHandler(self._log_handler)
        where
            _log_handler is LoggingHandlerForLogWidget

        Arguments:
            name {string} -- Name of logger to be added
        """
        if name in self.tracked_loggers:
            return

        # Add action
        self.tracked_loggers[name] = QAction('View ' + name, self)
        action = self.tracked_loggers[name]
        action.setCheckable(True)
        action.setChecked(True)  # show the logging messages
        action.triggered.connect(self.report_all_messages)
        self.addAction(action)

        # style -- move
        self.document().setDefaultStyleSheet(config.GUI_CONFIG.logger.style)

    @property
    def get_all_checked(self):
        res = []
        for name, action in self.tracked_loggers.items():
            if action.isChecked():
                res += [name]
        return res

    def report_all_messages(self):
        """
        Report all lines form scratch
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
        if format_as_html == True:  # pylint: disable=singleton-comparison

            if not self.action_show_times.isChecked():
                # remove the timestamp -- assumes that this has been formatted
                # with pre tag by LoggingHandlerForLogWidget
                res = message.split('<pre>', 1)
                if len(res) == 2:
                    message = res[0] + '<pre>' + res[1][1+self.timestamp_len:]
                else:
                    pass #    print(f'Warning incorrect: {message}')

            cursor.insertHtml(message)

        elif format_as_html == 2:
            cursor.insertHtml(message)

        else:
            cursor.insertText(message, self.text_format)

        # make sure that the message is visible and scrolled ot
        if self.actino_scroll_auto.isChecked():
            self.moveCursor(QtGui.QTextCursor.End)
        self.ensureCursorVisible()


class LoggingHandlerForLogWidget(logging.Handler):

    def __init__(self, name, parent,
                 log_panel: LoggingWindowWidget, log_string=None):
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
        self.log_panel = parent.ui.log_text

        # Formatter
        if isinstance(log_string, str):
            self._log_string = log_string
        else:
            self._log_string = f'%(asctime).{LoggingWindowWidget.timestamp_len}s %(name)s: %(message)s [%(module)s.%(funcName)s]'
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
        #print(record)
        #self.log_panel.record = record
        #self.log_panel.zz = self

        html_record = html.escape(self.format(record))
        html_log_message = '<span class="%s"><pre>%s</pre></span>' % (
            record.levelname, html_record)
        self.log_panel.log_message_to(self.name, html_log_message)
