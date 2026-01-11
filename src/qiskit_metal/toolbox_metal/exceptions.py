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

# pylint: disable=invalid-name
# pylint: disable=unused-import
"""Custom Exceptions."""

from sys import prefix


class QiskitMetalExceptions(Exception):
    """Custom Exception super-class. Every Exception raised by qiskit-metal
    should inherit this. Adds the qiskit-metal prefix.

    Args:
        message (str): String describing the error raised from qiskit-metal
    """

    # pylint: disable=super-init-not-called
    def __init__(self, message: str) -> None:
        prefix = "Qiskit Metal - "
        self.args = [prefix + message]


class QLibraryGUIException(QiskitMetalExceptions):
    """Custom Exception for the QLibrary GUI feature
    """


class QiskitMetalDesignError(QiskitMetalExceptions):
    """Custom Exception to indicate User action is needed to correct Design
    Inputs.

    Args:
        message (str): String describing the cause of the error and suggested solution
    """

    def __init__(self, message: str) -> None:
        prefix = "Designer Error: User action required. \n"
        super().__init__(prefix + message)


class IncorrectQtException(Exception):
    """Run PySide2 only.

    Args:
        message (str): String describing the cause of the error and suggested solution
    """

    def __init__(self, message: str) -> None:
        prefix = "You should be using PySide2. \n"
        super().__init__(prefix + message)


class InputError(QiskitMetalExceptions):
    """Custom exception to indicate input errors
    """