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
"""
Does M functionality
@author: John Smith (Appleseed University of Technology), updated by Grace Harper (IBM Quantum)
"""


class FeatureM():
    """
    Provides M functionality for X use cases
    """
    def __init__(m_var):
        "Allows for M functionality given X and Y use cases"
        self.m_var = m_var
    def m_function(self, x):
        "FeatureM allows for M functionality for use case 1"
        return self.m_var * x

    def m_function_2(self, x):
        "FeatureM allows for M functionality for use case 2"
        return self.m_var * x**2

