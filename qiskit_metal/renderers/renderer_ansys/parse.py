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
@auhtor: Zlatko Minev
@date: 2019
"""

from pyEPR.hfss import parse_units as __parse_units_hfss__
from pyEPR.hfss import \
    unparse_units  # not used here, but in imports of this file

# See also: is_variable_name, is_numeric_possible
#from ... import Dict
from ...toolbox_metal.parsing import parse_value

__all__ = ['parse_value_hfss', 'unparse_units']

def parse_value_hfss(*args):
    '''
    Parse to HFSS units (from user units)
    '''
    return __parse_units_hfss__(*args)

#TODO: function to itterate and convert user units to

def to_ansys_units(value): # can make more efifiecnt if we assume this is already a flaot
    __parse_units_hfss__(value)
