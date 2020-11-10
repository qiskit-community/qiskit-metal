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

# pylint: disable=protected-access

'''
Math and override functions

@author: Marco Facchini (IBM)
@date: 2020-10
'''

import numpy as np

__all__ = ['set_decimal_precision', 'dot', 'cross', 'round']

decimal_precision = 10


def set_decimal_precision(value: int):
    """
    Override the decimal_precision default (10)

    Args:
        value: any integer. If present, decimal part will be truncated (flooring)
    """
    global decimal_precision
    decimal_precision = int(value)


def dot(vector_1: np.array, vector_2: np.array) -> float:
    """
    Numpy dot product with decimal_precision

    Args:
        vector_1 (np.array): first of the dot product vectors
        vector_2 (np.array): second of the dot product vectors

    Returns:
        float: rounded dot product
    """
    return np.round(np.dot(vector_1, vector_2), decimal_precision)


def round(value) -> float:
    """
    Numpy rounding with decimal_precision

    Args:
        value: any numerical type supported by np.round()

    Returns:
        float: rounded number
    """
    return np.round(value, decimal_precision)


def cross(vector_1: np.array, vector_2: np.array) -> float:
    """
    Numpy cross product with decimal_precision

    Args:
        vector_1 (np.array): first of the cross product vectors
        vector_2 (np.array): second of the cross product vectors

    Returns:
        float: rounded cross product
    """
    return np.round(np.cross(vector_1, vector_2), decimal_precision)
