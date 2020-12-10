# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2020.
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

"""
Custom Exceptions

@author: Marco Facchini
@date: 12/2020
"""


class QiskitMetalExceptions(Exception):
    """
    Custom Exception super-class. Every Exception raised by qiskit-metal should inherit this.
    Adds the qiskit-metal prefix

    Attributes:
        message -- string describing the error raised from qiskit-metal
    """
    def __init__(self, message: str) -> None:
        prefix = "Qiskit Metal - "
        self.args = [prefix + message]


class QiskitMetalDesignError(QiskitMetalExceptions):
    """
    Custom Exception to indicate User action is needed to correct Design Inputs

    Attributes:
        message -- string describing the cause of the error and suggested solution
    """
    def __init__(self, message: str) -> None:
        prefix = "Designer Error: User action required. \n"
        super().__init__(prefix + message)
