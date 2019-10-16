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

"""
This is a utility module used to handle pyqt error messages on slots and etc.

@author: Zlatko K. Minev
"""

import types
import inspect
from functools import wraps
from PyQt5.QtCore import pyqtSlot

from PyQt5 import QtCore
from .. import logging, logger

#######################################################################################
# Core handler
###

def _pyqt_message_handler(mode, context, message):
    '''
    The message handler is a function that prints out debug messages,
    warnings, critical and fatal error messages. The Qt library (debug mode)
    contains hundreds of warning messages that are printed when internal errors
    (usually invalid function arguments) occur. Qt built in release mode also
    contains such warnings unless QT_NO_WARNING_OUTPUT and/or QT_NO_DEBUG_OUTPUT
    have been set during compilation. If you implement your own message handler,
     you get total control of these messages.

    The default message handler prints the message to the standard output under X11
    or to the debugger under Windows. If it is a fatal message, the application
    aborts immediately.

    For more info, see https://doc.qt.io/qt-5/qtglobal.html#qInstallMessageHandler
    '''

    if message.startswith('QSocketNotifier: Multiple socket notifiers for same socket'):
        pass  # Caused by running %gui qt multiple times
    else:
        if mode == QtCore.QtInfoMsg:
            mode = 'INFO'
        elif mode == QtCore.QtWarningMsg:
            mode = 'WARNING'
        elif mode == QtCore.QtCriticalMsg:
            mode = 'CRITICAL'
        elif mode == QtCore.QtFatalMsg:
            mode = 'FATAL'
        else:
            mode = 'DEBUG'
        logger.log(getattr(logging, 'CRITICAL'),
                   'line: %d, func: %s(), file: %s' % (context.line, context.function,
                                                       context.file) + '  %s: %s\n' % (mode, message))

#######################################################################################
# Auxilary handlers - mostly for debug purposes
###

def do_debug(msg, name='info'):
    """
    Utility function used to print debug statemetns from PyQt5 Socket calls
    A bit of a cludge

    Arguments:
        msg {[str]} -- [Message to print or log to user]

    Keyword Arguments:
        name {str} -- [info wran, debug, etc. ] (default: {'info'})
    """
    if 0:
        callers = []
        for i in range(1, 20):
            try:
                stack = inspect.stack()[i]
                callers += [f'{stack.function}[{stack.lineno}]']
            except Exception:  # pylint: disable=broad-except
                pass
        callers = reversed(callers)
        callers = '.'.join(callers)
        msg = callers + "\n" + str(msg)+'\n'
    getattr(logger, name)(msg)


def catch_exception_slot_pyqt(*args, catch=Exception, on_exception_emit=None):
    """
    This is a decorator for pyqtSlots where an exception
    in user code is caught, printed and a optional pyqtSignal with
    signature pyqtSignal(Exception, str) is emitted when that happens.

    Based on:
        https://stackoverflow.com/questions/18740884/preventing-pyqt-to-silence-exceptions-occurring-in-slots

    Arguments:
        args :  any valid types for the pyqtSlot
        catch :  Type of the exception to catch, defaults to any exception
        on_exception_emit :  name of a pyqtSignal to be emitted
    """

    if len(args) == 0 or isinstance(args[0], types.FunctionType):
        args = []

    @pyqtSlot(*args)
    def slotdecorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):  # pylint: disable=unused-argument
            try:
                #do_debug(f'func={func} args = {args}')
                #print(f'func={func} args = {args}')
                func(*args)
            except catch as e:  # pylint: disable=invalid-name,broad-except
                do_debug(f"ERROR in pyqtSlot: {wrapper.__name__}:\n"
                         f"Caught exception: {e.__repr__()}", 'error')
                if on_exception_emit is not None:
                    # args[0] is instance of bound signal
                    pyqt_signal = getattr(args[0], on_exception_emit)
                    pyqt_signal.emit(e, wrapper.__name__)
        return wrapper
    return slotdecorator
