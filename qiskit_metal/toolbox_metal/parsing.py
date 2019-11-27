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
Parsing module Qiskit Metal.

The main function in this module is `parse_value`, and it explains what
and how it is handled. Some basic arithemetic can be handled as well,
such as `'-2 * 1e5 nm'` will yield float(-0.2) when the default units are set to `mm`.

Example parsing values test:
------------------
    .. code-block:: python

        from qiskit_metal.toolbox_metal.parsing import *

        def test(val, _vars):
            res = parse_value(val, _vars)
            print( f'{type(val).__name__:<6} |{val:>12} >> {str(res):<20} | {type(res).__name__:<6}')

        def test2(val, _vars):
            res = parse_value(val, _vars)
            print( f'{type(val).__name__:<6} |{val:>38} >> {str(res):<47} | {type(res).__name__:<6}')

        vars_ = {'x':5.0, 'y':'5um'}
        test(1, vars_)
        test(1., vars_)
        test('1', vars_)
        test('1.', vars_)
        test('+1.', vars_)
        test('-1.', vars_)
        test('1.0', vars_)
        test('1mm', vars_)
        test(' 1  mm ', vars_)
        test('100mm', vars_)
        test('1.mm', vars_)
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
        test(' - 1. ', vars_)
        test(' + 1. ', vars_)
        test('1 .', vars_)

        print('------------------------------------------------\nArithmetic')
        test('2*1', vars_)
        test('2*10mm', vars_)
        test('-2 * 1e5 nm', vars_)

        print('------------------------------------------------\nVars')
        test('x', vars_)
        test('y', vars_)
        test('z', vars_)
        test('x1', vars_)

        print('------------------------------------------------\nList and dict')
        test2(' [1,2,3.,4., "5um", " -0.1e6 nm"  ] ', vars_)
        test2(' {3:2, 4: " -0.1e6 nm"  } ', vars_)


Returns:
------------------
    .. code-block:: python

        int    |           1 >> 1                    | int
        float  |         1.0 >> 1.0                  | float
        str    |           1 >> 1.0                  | float
        str    |          1. >> 1.0                  | float
        str    |         +1. >> 1.0                  | float
        str    |         -1. >> -1.0                 | float
        str    |         1.0 >> 1.0                  | float
        str    |         1mm >> 1                    | int
        str    |      1  mm  >> 1                    | int
        str    |       100mm >> 100                  | int
        str    |        1.mm >> 1.0                  | float
        str    |       1.0mm >> 1.0                  | float
        str    |         1um >> 0.001                | float
        str    |        +1um >> 0.001                | float
        str    |        -1um >> -0.001               | float
        str    |      -0.1um >> -0.0001              | float
        str    |        .1um >> 0.0001               | float
        str    |      0.1  m >> 100.0                | float
        str    |     -1E6 nm >> -1.0000000000000002  | float
        str    |     -1e6 nm >> -1.0000000000000002  | float
        str    |     .1e6 nm >> 0.10000000000000002  | float
        str    |   - .1e6nm  >> -0.10000000000000002 | float
        str    |  - .1e6 nm  >> -0.10000000000000002 | float
        str    |   - 1e6 nm  >>  - 1e6 nm            | str
        str    |   - 1e6 nm  >> - 1e6 nm             | str
        str    |       - 1.  >>  - 1.                | str
        str    |       + 1.  >>  + 1.                | str
        str    |         1 . >> 1 .                  | str
        ------------------------------------------------
        Arithmetic
        str    |         2*1 >> 2*1                  | str
        str    |      2*10mm >> 20                   | int
        str    | -2 * 1e5 nm >> -0.20000000000000004 | float
        ------------------------------------------------
        Vars
        str    |           x >> 5.0                  | float
        str    |           y >> 0.005                | float
        str    |           z >> z                    | str
        str    |          x1 >> x1                   | str
        ------------------------------------------------
        List and dict
        str    |   [1,2,3.,4., "5um", " -0.1e6 nm"  ]  >> [1, 2, 3.0, 4.0, 0.005, -0.10000000000000002]   | list
        str    |             {3:2, 4: " -0.1e6 nm"  }  >> {3: 2, 4: -0.10000000000000002}                 | Dict

@date: 2019
@author: Zlatko K. Minev, Thomas McConkey (IBM)
'''

import ast
from collections.abc import Iterable
from numbers import Number

import pint

from .. import Dict, config, logger

__all__ = ['is_variable_name', 'is_numeric_possible',
           'parse_value', 'parse_params']

#########################################################################
# Constants

# Values that can represent True bool
TRUE_STR = ['true', 'True', 'TRUE', '1', 't', 'y', 'Y', 'YES',
            'yes', 'yeah', 'yup', 'certainly', 'uh-huh', True, 1]

# The unit registry stores the definitions and relationships between units.
UREG = pint.UnitRegistry()

#########################################################################
# Basic string to number


def _parse_string_to_float(expr: str):
    """Extract the value of a string.

    If the passed value is not convertable,
    the input value `expr`  will just ne returned.

    Note that you can also pass in some arithmetic:
        `UREG.Quantity('2*130um').to('mm').magnitude`
        >> 0.26

    Original code: pyEPR.hfss - see file.

    Arguments:
        expr {str} -- String expression such as '1nm'.

    Internal:
        to_units {str} -- Units to conver the value to, such as 'mm'.
                            Hardcoded to  config.DEFAULT.units

    Returns:
        float -- Converted value, such as float(1e-6)
    """
    try:
        return UREG.Quantity(expr).to(config.DEFAULT.units).magnitude
    except Exception:
        # DimensionalityError, UndefinedUnitError, TypeError
        try:
            return float(expr)
        except Exception:
            return expr


#########################################################################
# UNIT and Conversion related


def is_variable_name(test_str: str):
    """Is the test string a valid name for a variable or not?

    Arguments:
        test_str {str} -- test string

    Returns:
        bool
    """
    return test_str.isidentifier()


def is_for_ast_eval(test_str: str):
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


def is_numeric_possible(test_str: str):
    """
    Is the test string a valid possible numerical with /or w/o units.

    Arguments:
        test_str {str} -- test string

    Returns:
        bool
    """
    return test_str[0].isdigit() or test_str[0] in ['+', '-', '.']
    # look into pyparsing


def parse_value(value: str, variable_dict: dict):
    """
    Parse a string, mappable (dict, Dict), iterrable (list, tuple) to account for units conversion,
    some basic arithmetic, and design variables.
    This is the main parsing function of Qiskit Metal.

    Handled Inputs:

        Strings:
            Strings of numbers, numbers with units; e.g., '1', '1nm', '1 um'
                Converts to float.
            Strings of variables 'variable1'
            Strings of

        Dictionaries:
            Returns ordered `Dict` with same key-value mappings, where the values have
            been subjected to parse_value.

        Itterables(list, tuple, ...):
            Returns same kind and calls itself `parse_value` on each elemnt.

        Numbers:
            Returns the number as is. Int to int, etc.


    Arithemetic:
        Some basic arithemetic can be handled as well, such as `'-2 * 1e5 nm'`
        will yield float(-0.2) when the default units are set to `mm`.

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
            # If it is a list or dict, this will do a literal eval, so string have
            # to be in "" else [5um , 4um ] wont work, but ["5um", "0.4 um"] will
            evaluated = ast.literal_eval(val)
            if isinstance(evaluated, list):
                # check if list, parse each element of the list
                return [parse_value(element, variable_dict) for element in evaluated]
            elif isinstance(evaluated, dict):
                return Dict({key: parse_value(element, variable_dict)
                             for key, element in evaluated.items()})
            else:
                logger.error(
                    f'Unkown error in `is_for_ast_eval`\nval={val}\nevaluated={evaluated}')
                return evaluated

        elif is_numeric_possible(val):
            return _parse_string_to_float(value)

        else:  # assume it is just a string (not intended to be parsed)
            return value

    elif isinstance(value, dict):  # collections.abc.Mapping
        # If the value is a dictionary, then parse that dictionary
        return parse_params(value, variable_dict)  # returns Dict

    elif isinstance(value, Iterable):
        # list, tuple, ... Return the same type
        return type(value)([parse_value(val, variable_dict) for val in value])

    elif isinstance(value, Number):
        # If it is an int it will return an int, not a float, etc.
        return value

    else:  # no parsing needed, it is not a string, mappable, or iterrable we can handle
        return value


def parse_params(options: dict, variable_dict: dict):
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
        lambda item: [item[0], parse_value(
            item[1], variable_dict)],  # key, value
        options.items()))
