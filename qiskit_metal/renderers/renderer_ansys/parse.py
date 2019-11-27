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

from pyEPR.hfss import parse_units
from pyEPR.hfss import unparse_units # not used here, but in imports of this file

__all__ = ['parse_value_hfss', 'unparse_units']

def parse_value_hfss(*args):
    '''
    Parse to HFSS units (from user units)
    '''
    return parse_units(*args)


#TODO: Remove this
def parse_options_hfss(opts, parse_names):
    '''
    To HFSS units.

    Used in HFSS renderer only.

    TODO: Supersee by USER UNITS TO HFSS UNITS.

    Parse a list of variable names (or a string of comma delimited ones
    to list of HFSS parsed ones.
    '''
    if isinstance(parse_names, str):
        parse_names = parse_names.split(',')

    return [parse_units(opts[name.strip()]) for name in parse_names]
