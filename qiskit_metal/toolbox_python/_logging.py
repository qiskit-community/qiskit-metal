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
"""File contains some config definitions.

Mostly internal.
"""

import logging, collections
from typing import List

__all__ = ['setup_logger', 'LogStore']


def setup_logger(logger_name,
                 log_format,
                 log_datefmt,
                 level_stream=logging.INFO,
                 level_base=logging.DEBUG,
                 force_set=False,
                 capture_warnings=None,
                 propagate=False,
                 create_stream=True) -> logging.Logger:
    """Setup the logger to work with jupyter and command line.

    `level_stream` and `level_base`:
    You can set a different logging level for each logging handler, however you have
    to set the logger's level to the "lowest".

    Integrates logging with the warnings module.

    Args:
        logger_name (str): Name of the log.
        log_format (format): Format of the log.
        log_datefmt (format): Format of the date.
        level_stream (log level): Log level of the stream.  Defaults to logging.INFO.
        level_base (log level): Log level of the base.  Defaults to logging.DEBUG.
        force_set (bool): True to force.  Defaults to False.
        capture_warnings (bool): True to capture warnings.  Defaults to None.
        propagate (bool): True to propagate.  Defaults to False.
        create_stream (bool): True to create the stream.  Defaults to True.

    Returns:
        logging.Logger: The logger

    To see the logging levels you can use:

    .. code-block:: python

        print(logger)
        print(logger.zkm_c_handler)
        print(gui._log_handler)
    """

    logger = logging.getLogger(logger_name)  # singleton

    if force_set or not len(logger.handlers):

        logger.setLevel(level_base)

        # Used to integrate logging with the warnings module.
        # Warnings issued by the warnings module will be redirected to the logging system.
        # Specifically, a warning will be formatted using warnings.formatwarning() and the resulting
        # string logged to a logger named 'py.warnings' with a severity of WARNING.
        if capture_warnings is not None:
            logging.captureWarnings(capture_warnings)

        # Jupyter notebooks already has a stream handler on the default log.
        # Do not propage upstream to the root logger.
        # https://stackoverflow.com/questions/31403679/python-logging-module-duplicated-console-output-ipython-notebook-qtconsole
        logger.propagate = propagate

        if create_stream:
            # Sends logging output to streams such as sys.stdout,
            # sys.stderr or any file-like object
            c_handler = logging.StreamHandler()

            # Format. Unlike the root logger, a custom logger can't be configured
            # using basicConfig().
            c_format = logging.Formatter(log_format, datefmt=log_datefmt)
            c_handler.setFormatter(c_format)

            # Add Hanlder with format and set level
            logger.addHandler(c_handler)
            c_handler.setLevel(level_stream)

            # save references for ease
            logger.zkm_c_handler = c_handler
            logger.zkm_c_format = c_format

    return logger


class LogStore(collections.deque):
    """Wrapper over collections.deque that ensures most recently added items
    (which should be strings) are at the "front" of the queue (i.e. left of the
    array).

    Each QDesign instantiation has a LogStore object used to keep track
    of logs for the Build History display.
    """

    def __init__(self,
                 title: str,
                 log_limit: int,
                 _previous_builds: List[str] = [],
                 *args,
                 **kwargs):
        super().__init__(maxlen=log_limit, *args, **kwargs)
        self._title = title
        for i in _previous_builds:
            self.appendleft(i)
        self._next_available_index = 0

    def data(self):
        #returns COPY of data
        return list(self)

    def add(self, log: str):
        self.appendleft(log)

    def add_success(self, log: str):
        self.appendleft(log)

    def add_error(self, log: str):
        self.appendleft(
            "ERROR " + log
        )  #used to differentiate error strings from success strings where logs are displayed

    @property
    def title(self):
        """The title is an easy way to differentiate between multiple instances
        of LogStore, each with different data."""
        return self._title
