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
"""This is a utility module used to handle qt error messages on slots and
etc."""

import inspect
import logging
import traceback
import types
from functools import wraps

from PySide6 import QtCore
from PySide6.QtCore import Slot

from qiskit_metal import logger

__all__ = ['slot_catch_error', 'do_debug']

#######################################################################################
# Core handler


def _qt_message_handler(mode, context, message):
    """The message handler is a function that prints out debug messages,
    warnings, critical and fatal error messages. The Qt library (debug mode)
    contains hundreds of warning messages that are printed when internal errors
    (usually invalid function arguments) occur. Qt built in release mode also
    contains such warnings unless QT_NO_WARNING_OUTPUT and/or
    QT_NO_DEBUG_OUTPUT have been set during compilation. If you implement your
    own message handler, you get total control of these messages.

    The default message handler prints the message to the standard output under X11
    or to the debugger under Windows. If it is a fatal message, the application
    aborts immediately.

    For more info, see https://doc.qt.io/qt-5/qtglobal.html#qInstallMessageHandler

    Args:
        mode (QtCore mode): the mode
        context (context): the context
        message (str): the message
    """

    if message.startswith(
            'QSocketNotifier: Multiple socket notifiers for same socket'):
        pass  # Caused by running %gui qt multiple times
    else:
        if mode == QtCore.QtMsgType.QtInfoMsg:
            mode = 'INFO'
        elif mode == QtCore.QtMsgType.QtWarningMsg:
            mode = 'WARNING'
        elif mode == QtCore.QtMsgType.QtCriticalMsg:
            mode = 'CRITICAL'
        elif mode == QtCore.QtMsgType.QtFatalMsg:
            mode = 'FATAL'
        else:
            mode = 'DEBUG'
        # logger.log(
        #     getattr(logging, 'CRITICAL'), 'line: %d, func: %s(), file: %s' %
        #     (context.line, context.function, context.file) + '  %s: %s\n' %
        #     (mode, message))

        # Log basic message details
        base_message = f"{mode}: {message}"

        # Include context if available
        if context.file and context.function:
            base_message += (
                f" (File: {context.file}, Line: {context.line}, Function: {context.function})"
            )
        else:
            base_message += " (No context available from Qt)"

        # Capture Python traceback for additional details
        python_traceback = "".join(traceback.format_stack(limit=10))

        # Log the message with the Python traceback
        logger.log(
            getattr(logging, mode, logging.DEBUG),
            f"{base_message}\nPython Traceback (most recent call last):\n{python_traceback}"
        )


#######################################################################################
# Auxilary handlers - mostly for debug purposes


def do_debug(msg, name='info'):
    """Utility function used to print debug statements from PySide6 Socket
    calls A bit of a cludge.

    Args:
        msg (str): Message to print or log to user
        name (str): info wran, debug, etc.  Defaults to 'info'.
    """

    # if 0:
    #     # This just gives the qt main loop traceback. Not useful.
    #     callers = []
    #     for i in range(1, 20):
    #         try:
    #             stack = inspect.stack()[i]
    #             callers += [f'{stack.function}[{stack.lineno}]']
    #         except Exception as e:  # pylint: disable=broad-except
    #             print("Exception during do_debug exception handling: " +
    #                   e.__repr__())
    #     callers = reversed(callers)
    #     callers = '\n'.join(callers)
    #     msg = callers + "\n" + str(msg) + '\n'

    getattr(logger, name)(msg)


def slot_catch_error(*args, catch=Exception, on_exception_emit=None):
    """This is a decorator for Slots where an exception in user code is caught,
    printed and a optional qtSignal with signature qtSignal(Exception, str) is
    emitted when that happens.

    Based on:
        https://stackoverflow.com/questions/18740884/preventing-pyqt-to-silence-exceptions-occurring-in-slots

    Args:
        args (arguments):  any valid types for the Slot.
        catch (Exception):  Type of the exception to catch.  Defaults to Exception.
        on_exception_emit (str):  name of a qtSignal to be emitted.
    """

    if len(args) == 0 or isinstance(args[0], types.FunctionType):
        args = []

    @Slot(*args)
    def slot_decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):  # pylint: disable=unused-argument

            try:
                func(*args)

            except catch as e:  # pylint: disable=invalid-name,broad-except

                message = traceback.format_exc()
                message += '\n\nERROR in call by Metal GUI (see traceback above)\n'\
                    + f"\n{' module   :':12s} {wrapper.__module__}" \
                    + f"\n{' function :':12s} {wrapper.__qualname__}" \
                    + f"\n{' err msg  :':12s} {e.__repr__()}"\
                    + f"\n{' args; kws:':12s} {args}; {kwargs}" \

                do_debug(message, name='error')

                if on_exception_emit is not None:
                    # args[0] is instance of bound signal
                    qt_signal = getattr(args[0], on_exception_emit)
                    qt_signal.emit(e, wrapper.__name__)

        return wrapper

    return slot_decorator
