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

# pylint: disable=protected-access
# pylint: disable=global-statement
# pylint: disable=import-error
"""Math and override functions."""

import numpy as np

__all__ = ['set_decimal_precision', 'dot', 'cross', 'round']

DECIMAL_PRECISION = 10


def set_decimal_precision(value: int):
    """Override the decimal_precision default (10).

    Arguments:
        value: Any integer. If present, decimal part will be truncated (flooring)
    """
    global DECIMAL_PRECISION
    DECIMAL_PRECISION = int(value)


def dot(vector_1: np.array, vector_2: np.array) -> float:
    """Numpy dot product with decimal_precision.

    Arguments:
        vector_1 (np.array): First of the dot product vectors
        vector_2 (np.array): Second of the dot product vectors

    Returns:
        float: Rounded dot product
    """
    return np.round(np.dot(vector_1, vector_2), DECIMAL_PRECISION)


# pylint: disable=redefined-builtin
def round(value) -> float:
    """Numpy rounding with decimal_precision.

    Arguments:
        value: Any numerical type supported by np.round()

    Returns:
        float: Rounded number
    """
    return np.round(value, DECIMAL_PRECISION)


def cross(vector_1: np.array, vector_2: np.array) -> float:
    """Numpy cross product with decimal_precision.

    Arguments:
        vector_1 (np.array): First of the cross product vectors
        vector_2 (np.array): Second of the cross product vectors

    Returns:
        float: Rounded cross product
    """
    return np.round(np.cross(vector_1, vector_2), DECIMAL_PRECISION)
