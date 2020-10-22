# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2020.
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
@author: Marco Facchini (IBM)
@date: 2020-10
'''

import numpy as np

__all__ = ['dot']

decimal_precision = 10

def set_decimal_precision(value):
    global decimal_precision
    decimal_precision = value

def dot(vector_1, vector_2):
    # idea of this function is to standardize the dot precision
    return np.round(np.dot(vector_1, vector_2), decimal_precision)

def round(number):
    # idea of this function is to standardize the dot precision
    return np.round(number, decimal_precision)
