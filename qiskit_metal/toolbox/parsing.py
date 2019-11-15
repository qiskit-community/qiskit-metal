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

Test:
    from qiskit_metal.toolbox.parsing import *
    def test(val, _vars):
        res = parse_value(val, _vars)
        print(type(res), res)
    vars_ = {'x':5.0, 'y':'5um'}
    test(1, vars_)
    test('1', vars_)
    test('1mm', vars_)
    test(1., vars_)
    test('1.', vars_)
    test('1.0mm', vars_)
    test('1um', vars_)
    test('+1um', vars_)
    test('-1um', vars_)
    test('-0.1um', vars_)
    test('.1um', vars_)
    test('  0.1  m', vars_)
    test('-1E6 nm', vars_)
    test('-1e6 nm', vars_)
    test('.1e6 nm', vars_)
    test(' - .1e6nm ', vars_)
    test(' - .1e6 nm ', vars_)
    test(' - 1e6 nm ', vars_)
    test('- 1e6 nm ', vars_)

    print('------------------------------------------------\nList and dict')
    test(' [1,2,3.,4., "5um", " -0.1e6 nm"  ] ', vars_)
    test(' {3:2, 4: " -0.1e6 nm"  } ', vars_)
    print('------------------------------------------------\nVars')
    test('x', vars_)
    test('y', vars_)
    test('z', vars_)
    test('x1', vars_)

Should return

    <class 'int'> 1
    <class 'int'> 1
    <class 'int'> 1
    <class 'float'> 1.0
    <class 'float'> 1.0
    <class 'float'> 1.0
    <class 'float'> 0.001
    <class 'float'> 0.001
    <class 'float'> -0.001
    <class 'float'> -0.0001
    <class 'float'> 0.0001
    <class 'float'> 100.0
    <class 'float'> -1.0000000000000002
    <class 'float'> -1.0000000000000002
    <class 'float'> 0.10000000000000002
    <class 'float'> -0.10000000000000002
    <class 'float'> -0.10000000000000002
    <class 'str'>  - 1e6 nm
    <class 'str'> - 1e6 nm
    ------------------------------------------------
    List and dict
    <class 'list'> [1, 2, 3.0, 4.0, 0.005, -0.10000000000000002]
    <class 'addict.addict.Dict'> {3: 2, 4: -0.10000000000000002}
    ------------------------------------------------
    vars
    <class 'float'> 5.0
    <class 'float'> 0.005
    <class 'str'> z
    <class 'str'> x1

@date: 2019
@author: Zlatko K. Minev, Thomas McConkey
'''
#TODO: make a local pakcage `parse_units_user` remove from pyEPR dependency
#TODO: remove HFSS parse to hfss plugin

import ast
from collections import OrderedDict

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
    """
    Parse a single string value to correct type and value
    USER UNITS.

    ** Main parsing funciton.**

    Arguments:
        value {[str]} -- string to parse
        variable_dict {[dict]} -- dict pointer of variables

    Return:
        Parse value: str, float, list, tuple, or ast eval
    """

    if isinstance(value, str):
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
            # If it is a list or dict, this will do a literal eval, so string have to be in "" else [5um , 4um ] wont work.
            # but ["5um", "0.4 um"] will
            evaluated = ast.literal_eval(val)
            if isinstance(evaluated, list):
                # check if list, parse each element of the list
                return [parse_value(element, variable_dict) for element in evaluated]
            elif isinstance(evaluated, dict):
                return Dict({key: parse_value(element, variable_dict) for key, element in evaluated.items()})
            else:
                logger.error(f'Unkown error in `is_for_ast_eval`\nval={val}\nevaluated={evaluated}')
                return evaluated

        elif is_numeric_possible(val):
            return parse_units_user(value)

        else: # assume it is just a string
            return value

    elif isinstance(value, dict):
        # If the value is a dictionary, then parse that dictionary
        return parse_options_dict(value, variable_dict)

    elif isinstance(value, list):
        return [parse_value(val, variable_dict) for val in value]

    elif isinstance(value, tuple):
        return tuple([parse_value(val, variable_dict) for val in value])

    else: # no parsing needed, it is not a string
        return value



def parse_options_dict(options:dict, variable_dict:dict):
    """
    Parses a list of option names from a dictionary of options.
    The dictionary values will be parse as variables, strings, int, floats, etc.
    Values with units are converted to **USER UNITS.** User units can be set in the design.
    Variable interpertation will use string method isidentifier `'variable1'.isidentifier()

    Arguments:
        options {[dict]} -- Dict with key value pairs of options, from which to parse.
        variable_dict {[dict]} -- Dictionary containing all variables (default: {None})

    Returns:
        [Dict] -- Dict of the parsed values


    Example test:
        vars_ = {'x':5.0, 'y':'5um'}
        parse_options_user({'a':4, 'b':'-0.1e6 nm', 'c':'x', 'd':'y','e':'z'},
                        'a,b,c,d,e',
                        vars_)

    Example converstions with a `design`:

        ..code-block python
            design.variables.cpw_width = '10um' # Example variable
            design.parse_options(Dict(
                string1 = '1m',
                string2 = '1mm',
                string3 = '1um',
                string4 = '1nm',
                variable1 = 'cpw_width',
                list1 = "['1m', '5um', 'cpw_width', -1, False, 'a string']",
                dict1 = "{'key1':'4e-6mm'}"
            ))

        Yields:

        ..code-block python
            {'string1': 1000.0,
            'string2': 1,
            'string3': 0.001,
            'string4': 1.0e-06,
            'variable1': 0.01,
            'list1': [1000.0, 0.005, 0.01, -1, False, 'a string'],
            'dict1': {'key1': 4e-06}}

    """
    return Dict(map(
                    lambda item: [item[0],  parse_value(item[1], variable_dict)],  # key, value
                options.items()))


def parse_options_user(option_dict, parse_names = None, variable_dict=None,
                       as_dict = False):
    """
    OUTDATED FUNCTION.
    MAY BE REMOVED IN FUTURE.
    SUPERSEEDED BY `parse_options_dict`

    Parses a list of option names from a dictionary of options.
        Assumes: User units.

    The dictionary values will be parse as variables, strings, int, floats, etc. and
    converted to USER units where appropriate.
    Units can be set in the design.

    Variable interpertation:
         will use isidentifier:  `'variable1'.isidentifier()

    Arguments:
        option_dict {[type]} -- Dict with key value pairs of options, from which to parse.
        parse_names {str, list, None} -- Either a list of strings that give the variables names,
            which can be comma delimited, or a single variable name
            e.g., one can pass
            'var_name1, var_name2'
            or
            ['var_name1', 'var_name2']
            If parse_names == None, then it will parse all the options in the dicitonary

    Keyword Arguments:
        variable_dict {[dict]} -- Dictionary containing all variables (default: {None})
        as_dict {bool} -- (default: False) Return as dicitonary or a lis

    Returns:
        [list] -- List of the parsed values


    Example test:
        vars_ = {'x':5.0, 'y':'5um'}
        parse_options_user({'a':4, 'b':'-0.1e6 nm', 'c':'x', 'd':'y','e':'z'},
                        'a,b,c,d,e',
                        vars_)
    """

    # Prep args
    if not variable_dict:       # If None, create an empty dict
        variable_dict = {}

    if parse_names is None:
        parse_names = option_dict.keys()

    elif isinstance(parse_names, str):
        parse_names = parse_names.split(',')

    # Do for each name
    # TODO: probably slow with for loop, can think of faster or vectorized method here
    res = OrderedDict()
    for name in parse_names:
        name = name.strip()  # remove trailing and leading white spaces in the name

        # is the name in the options at all?
        if not name in option_dict:
            logger.warning(f'Missing key {name} from options {option_dict}. Skipping ...\n')
            continue

        # option_dict[name] should be a string
        res[name] = parse_value(option_dict[name], variable_dict)

    if as_dict:
        return res
    else:
        return list(res.values())


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
