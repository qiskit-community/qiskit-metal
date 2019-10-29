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

'''
Parsing functions for  Qiskit Metal.

@date: 2019
@author: Zlatko K. Minev, Thomas McConkey
'''

from pyEPR.hfss import parse_units, parse_units_user
from pyEPR.hfss import unparse_units # not used here, but in imports of this file
from .. import logger

#########################################################################
# UNIT and Conversion related


def parse_options_user(option_dict, parse_names, variable_dict=None):
    """
    Parses a list of option names from a dictionary of options.
        Assumes: User units.

    The dictionary values will be parse as variables, strings, int, floats, etc. and
    converted to USER units where appropriate.
    Units can be set in the design.

    Variable interpertation:
         will use isidentifier:  `'variable1'.isidentifier()

    Arguments:
        option_dict {[type]} -- Dict with key value pairs of options, from which to parse.
        parse_names {str, list} -- Either a list of strings that give the variables names,
            which can be comma delimited, or a single variable name
            e.g., one can pass
            'var_name1, var_name2'
            or
            ['var_name1', 'var_name2']

    Keyword Arguments:
        variable_dict {[dict]} -- Dictionary containing all variables (default: {None})

    Returns:
        [list] -- List of the parsed values
    """

    # Prep args
    if not variable_dict:       # If None, create an empty dict
        variable_dict = {}

    if isinstance(parse_names, str):
        names = names.split(',')

    # Do for each name
    # TODO: probably slow with for loop, can think of faster or vectorized method here
    opts = option_dict  # alias
    res = []
    for name in names:
        name = name.strip()  # remove trailing and leading white spaces in the name

        # is the name in the options at all?
        if not name in opts:
            logger.warning(f'Missing key {name} from options {opts}.\n')

        if isinstance(opts[name], str):
            if not(opts[name][0].isdigit() or opts[name][0] == '-'):
                if not opts[name] in variable_dict:
                    logger.warning(f'Missing variable {opts[name]} from variable list.\n')

                res += [parse_units_user(variable_dict[opts[name]])]
            else:
                res += [parse_units_user(opts[name])]
        else:
            res += [parse_units_user(opts[name])]

    return res
    # return [parse_units_user(opts[name.strip()]) for name in names]


def parse_options_hfss(opts, names):
    '''
    To HFSS units.

    Parse a list of variable names (or a string of comma delimited ones
    to list of HFSS parsed ones.
    '''
    if isinstance(names, str):
        names = names.split(',')

    return [parse_units(opts[name.strip()]) for name in names]
