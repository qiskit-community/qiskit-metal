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

    Args:
        value: Any integer. If present, decimal part will be truncated (flooring)
    """
    global DECIMAL_PRECISION
    DECIMAL_PRECISION = int(value)


def dot(vector_1: np.array, vector_2: np.array) -> float:
    """Numpy dot product with decimal_precision.

    Args:
        vector_1 (np.array): First of the dot product vectors
        vector_2 (np.array): Second of the dot product vectors

    Returns:
        float: Rounded dot product
    """
    return round(np.dot(vector_1, vector_2))


# pylint: disable=redefined-builtin
def round(value) -> float:
    """Numpy rounding with decimal_precision.

    Args:
        value: Any numerical type supported by np.round()

    Returns:
        float: Rounded number
    """
    return np.round(value, DECIMAL_PRECISION)


def cross(vector_1: np.array, vector_2: np.array) -> float:
    """Numpy cross product with decimal_precision.

    Args:
        vector_1 (np.array): First of the cross product vectors
        vector_2 (np.array): Second of the cross product vectors

    Returns:
        float: Rounded cross product
    """
    return round(np.cross(vector_1, vector_2))


def aligned_pts(points: list) -> bool:
    """Are the three points aligned? with decimal_precision.

    Args:
        points (list): of 3 points expressed as list or np.array

    Returns:
        bool: True if they are aligned. False otherwise
    """
    if len(points) != 3:
        raise Exception(
            "Ambiguous. You can only pass exactly 3 points to this method")
    v1 = points[1] - points[0]
    v1_dir = v1 / np.linalg.norm(v1)
    v2 = points[2] - points[1]
    v2_dir = v2 / np.linalg.norm(v2)
    result = dot(v1_dir, v2_dir)
    return True if result == 1 else False
