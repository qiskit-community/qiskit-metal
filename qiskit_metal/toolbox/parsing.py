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
#TODO: make a local pakcage `parse_units_user` remove from pyEPR dependency
#TODO: remove HFSS parse to hfss plugin

import ast
from pyEPR.hfss import parse_units, parse_units_user
from pyEPR.hfss import unparse_units # not used here, but in imports of this file
from .. import logger, Dict

#########################################################################
# UNIT and Conversion related

def is_variable_name(test_str : str):
    """Is the test string a valid name for a variable or not?

    Arguments:
        test_str {str} -- test string

    Returns:
        bool
    """
    return test_str.isidentifier()

def is_for_ast_eval(test_str : str):
    """
    Is the test string a valid list of dict string,
    such as "[1, 2]", that can be evaluated by ast eval

    Arguments:
        test_str {str} -- test string

    Returns:
        bool
    """
    return ('[' in test_str and ']' in test_str) or \
           ('{' in test_str and '}' in test_str)

def is_numeric_possible(test_str:str):
    """
    Is the test string a valid possible numerical with /or w/o units.

    Arguments:
        test_str {str} -- test string

    Returns:
        bool
    """
    return test_str[0].isdigit() or test_str[0] in ['+', '-', '.']

# look into pyparsing
def parse_value(value : str, variable_dict : dict):
    """Parse a single string value to correct type and value

    Arguments:
        value {[str]} -- string to parse
        variable_dict {[dict]} -- dict pointer of variables

    Return:
        Parse value: str, float, list, tuple, or ast eval
    """

    if isinstance(val, str):
        # remove trailing and leading white spaces in the name
        val = str(value).strip()

        if is_variable_name(val):
            # we have a string that could be interpreted as a variable
            # check if there is such a variable name, else return as string
            # logger.warning(f'Missing variable {opts[name]} from variable list.\n')

            if val in variable_dict:
                # Parse the returned value
                return parse_value(variable_dict[val], variable_dict)
            else:
                # Assume it is a string and just return it
                return val

        elif is_for_ast_eval(val):
            evaluated = ast.literal_eval(val)
            if isinstance(evaluated, list):
                # check if list, parse each element of the list
                return [parse_value(element, variable_dict) for element in evaluated]
            elif isinstance(evaluated, list):
                return Dict({key: parse_value(element, variable_dict) for key, element in evaluated.items()})
            else:
                logger.error(f'Unkown is_for_ast_eval\nval={val}\nevaluated={evaluated}')
                return evaluated

        elif is_numeric_possible(val):
            return parse_units_user(value)

        else: # assume it is just a string
            return value

    else: # no parsing needed, it is not a string
        return value

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
        parse_names = parse_names.split(',')

    # Do for each name
    # TODO: probably slow with for loop, can think of faster or vectorized method here
    res = []
    for name in parse_names:
        name = name.strip()  # remove trailing and leading white spaces in the name

        # is the name in the options at all?
        if not name in option_dict:
            logger.warning(f'Missing key {name} from options {option_dict}. Skipping ...\n')
            continue

        # option_dict[name] should be a string
        res += [ parse_value(option_dict[name], variable_dict) ]

    return res


def parse_options_hfss(opts, parse_names):
    '''
    To HFSS units.

    Parse a list of variable names (or a string of comma delimited ones
    to list of HFSS parsed ones.
    '''
    if isinstance(parse_names, str):
        parse_names = parse_names.split(',')

    return [parse_units(opts[name.strip()]) for name in parse_names]
