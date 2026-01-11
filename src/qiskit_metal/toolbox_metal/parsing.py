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

# pylint: disable-msg=broad-except
# pylint: disable-msg=relative-beyond-top-level
# pylint: disable-msg=import-error
# pylint: disable-msg=line-too-long
"""Parsing module Qiskit Metal.

The main function in this module is `parse_value`, and it explains what
and how it is handled. Some basic arithmetic can be handled as well,
such as `'-2 * 1e5 nm'` will yield float(-0.2) when the default units are set to `mm`.

Example parsing values test:
----------------------------
    .. code-block:: python

        from qiskit_metal.toolbox_metal.parsing import *

        def test(val, _vars):
            res = parse_value(val, _vars)
            print( f'{type(val).__name__:<6} |{val:>12} >> {str(res):<20} | {type(res).__name__:<6}')

        def test2(val, _vars):
            res = parse_value(val, _vars)
            print( f'{type(val).__name__:<6} |{str(val):>38} >> {str(res):<47} | {type(res).__name__:<6}')

        vars_ = Dict({'x':5.0, 'y':'5um', 'cpw_width':'10um'})

        print('------------------------------------------------')
        print('String: Basics')
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

        print('------------------------------------------------')
        print('String: Arithmetic')
        test('2*1', vars_)
        test('2*10mm', vars_)
        test('-2 * 1e5 nm', vars_)

        print('------------------------------------------------')
        print('String: Variable')
        test('x', vars_)
        test('y', vars_)
        test('z', vars_)
        test('x1', vars_)
        test('2*y', vars_)

        print('------------------------------------------------')
        print('String: convert list and dict')
        test2(' [1,2,3.,4., "5um", " -0.1e6 nm"  ] ', vars_)
        test2(' {3:2, 4: " -0.1e6 nm"  } ', vars_)

        print('')
        print('------------------------------------------------')
        print('Dict: convert list and dict')
        my_dict = Dict(
            string1 = '1m',
            string2 = '1mm',
            string3 = '1um',
            string4 = '1nm',
            variable1 = 'cpw_width',
            list1 = "['1m', '5um', 'cpw_width', -1, False, 'a string']",
            dict1 = "{'key1':'4e-6mm', '2mm':'100um'}"
        )
        #test2(my_dict, vars_)
        display(parse_value(my_dict, vars_))


Returns:
------------------

    .. code-block:: python

        ------------------------------------------------
        String: Basics
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
        String: Arithmetic
        str    |         2*1 >> 2*1                  | str
        str    |      2*10mm >> 20                   | int
        str    | -2 * 1e5 nm >> -0.20000000000000004 | float
        ------------------------------------------------
        String: Variable
        str    |           x >> 5.0                  | float
        str    |           y >> 0.005                | float
        str    |           z >> z                    | str
        str    |          x1 >> x1                   | str
        str    |         2*y >> 2*y                  | str
        ------------------------------------------------
        String: convert list and dict
        str    |   [1,2,3.,4., "5um", " -0.1e6 nm"  ]  >> [1, 2, 3.0, 4.0, 0.005, -0.10000000000000002]   | list
        str    |             {3:2, 4: " -0.1e6 nm"  }  >> {3: 2, 4: -0.10000000000000002}                 | Dict


        ------------------------------------------------
        Dict: convert list and dict

        {'string1': 1000.0,
        'string2': 1,
        'string3': 0.001,
        'string4': 1.0000000000000002e-06,
        'variable1': 0.01,
        'list1': [1000.0, 0.005, 0.01, -1, False, 'a string'],
        'dict1': {'key1': 4e-06, '2mm': 0.1}}
"""

from collections.abc import Iterable
from collections.abc import Mapping
from numbers import Number
from typing import Union

import ast
import numpy as np
import pint
from pint import UnitRegistry

from qiskit_metal import Dict, config, logger

__all__ = [
    'parse_value',  # Main function
    'is_variable_name',  # extra helpers
    'is_numeric_possible',
    'is_for_ast_eval',
    'is_true',
    'parse_options'
]

#########################################################################
# Constants

# Values that can represent True bool
TRUE_STR = [
    'true', 'True', 'TRUE', True, '1', 't', 'y', 'Y', 'YES', 'yes', 'yeah', 1,
    1.0
]
FALSE_STR = [
    'false', 'False', 'FALSE', False, '0', 'f', 'n', 'N', 'NO', 'no', 'na', 0,
    0.0
]


def is_true(value: Union[str, int, bool, float]) -> bool:
    """Check if a value is true or not.

    Args:
        value (str): Value to check

    Returns:
       bool: Is the string a true
    """
    return value in TRUE_STR  # membership test operator


# The unit registry stores the definitions and relationships between units.
UREG = pint.UnitRegistry()

#########################################################################
# Basic string to number

units = config.DefaultMetalOptions.default_generic.units


def _parse_string_to_float(expr: str):
    """Extract the value of a string.

    If the passed value is not convertable,
    the input value `expr` will just ne returned.

    Note that you can also pass in some arithmetic:
        `UREG.Quantity('2*130um').to('mm').magnitude`
        >> 0.26

    Original code: pyEPR.hfss - see file.

    Args:
        expr (str): String expression such as '1nm'.

    Internal:
        to_units (str): Units to convert the value to, such as 'mm'.
                        Hardcoded to  config.DEFAULT.units

    Returns:
        float: Converted value, such as float(1e-6)

    Raises:
        Exception: Errors in parsing
    """
    try:
        return UREG.Quantity(expr).to(units).magnitude

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

    Args:
        test_str (str): Test string

    Returns:
        bool: Is str a variable name
    """
    return test_str.isidentifier()


def is_for_ast_eval(test_str: str):
    """Is the test string a valid list of dict string, such as "[1, 2]", that
    can be evaluated by ast eval.

    Args:
        test_str (str): Test string

    Returns:
        bool: Is test_str a valid list of dict strings
    """
    return ('[' in test_str and ']' in test_str) or \
           ('{' in test_str and '}' in test_str)


def is_numeric_possible(test_str: str):
    """Is the test string a valid possible numerical with /or w/o units.

    Args:
        test_str (str): Test string

    Returns:
        bool: Is the test string a valid possible numerical
    """
    return test_str[0].isdigit() or test_str[0] in ['+', '-', '.']
    # look into pyparsing


# pylint: disable-msg=too-many-branches
# pylint: disable-msg=too-many-return-statements
def parse_value(value: str, variable_dict: dict):
    """Parse a string, mappable (dict, Dict), iterable (list, tuple) to account
    for units conversion, some basic arithmetic, and design variables. This is
    the main parsing function of Qiskit Metal.

    Handled Inputs:

        Strings of numbers, numbers with units; e.g., '1', '1nm', '1 um'
            Converts to int or float.
            Some basic arithmetic is possible, see below.
        Strings of variables 'variable1'.
            Variable interpretation will use string method
            isidentifier 'variable1'.isidentifier()
        Strings of Dictionaries:
            Returns ordered `Dict` with same key-value mappings, where the values have
            been subjected to parse_value.
        Strings of Iterables(list, tuple, ...):
            Returns same kind and calls itself `parse_value` on each elemnt.

        Numbers:
            Returns the number as is. Int to int, etc.

    Arithmetic:
        Some basic arithmetic can be handled as well, such as `'-2 * 1e5 nm'`
        will yield float(-0.2) when the default units are set to `mm`.

    Default units:
        User units can be set in the design. The design will set config.DEFAULT.units

    Examples:
        See the docstring for this module.
            >> ?qiskit_metal.toolbox_metal.parsing

    Args:
        value (str): String to parse
        variable_dict (dict): dict pointer of variables

    Return:
        str, float, list, tuple, or ast eval: Parsed value
    """

    if isinstance(value, str):

        # remove trailing and leading white spaces in the name
        val = str(value).strip()

        if val:
            if is_variable_name(val):
                # we have a string that could be interpreted as a variable
                # check if there is such a variable name, else return as string
                # logger.warning(f'Missing variable {opts[name]} from variable list.\n')

                if val in variable_dict:
                    # Parse the returned value
                    return parse_value(variable_dict[val], variable_dict)

                # Assume it is a string and just return it
                # CAUTION: This could cause issues for the user, if they meant to pass a variable
                # but mistyped it or didn't define it. But they might also want to pass a string
                # that is variable name compatible, such as pec.
                # This is basically about type checking, which we can get back to later.
                return val

            if is_for_ast_eval(val):
                # If it is a list or dict, this will do a literal eval, so string have
                # to be in "" else [5um , 4um ] wont work, but ["5um", "0.4 um"] will
                evaluated = ast.literal_eval(val)
                if isinstance(evaluated, list):
                    # check if list, parse each element of the list
                    return [
                        parse_value(element, variable_dict)
                        for element in evaluated
                    ]
                if isinstance(evaluated, dict):
                    return Dict({
                        key: parse_value(element, variable_dict)
                        for key, element in evaluated.items()
                    })

                logger.error(
                    f'Unknown error in `is_for_ast_eval`\nval={val}\nevaluated={evaluated}'
                )
                return evaluated

            if is_numeric_possible(val):
                return _parse_string_to_float(value)

    elif isinstance(value, Mapping):
        # If the value is a dictionary (dict,Dict,...),
        # then parse that dictionary. return Dict
        return Dict(
            map(
                lambda item:  # item = [key, value]
                [item[0], parse_value(item[1], variable_dict)],
                value.items()))

    elif isinstance(value, Iterable):
        # list, tuple, ... Return the same type
        return {
            np.ndarray: np.array
        }.get(type(value),
              type(value))([parse_value(val, variable_dict) for val in value])

    elif isinstance(value, Number):
        # If it is an int it will return an int, not a float, etc.
        return value

    # else no parsing needed, it is not data that we can handle
    return value


def parse_options(params: dict, parse_names: str, variable_dict=None):
    """
    Calls parse_value to extract from a dictionary a small subset of values.
    You can specify parse_names = 'x,y,z,cpw_width'.

    Args:
        params (dict): Dictionary of params
        parse_names (str): Name to parse
        variable_dict (dict): Dictionary of variables.  Defaults to None.
    """

    # Prep args
    if not variable_dict:  # If None, create an empty dict
        variable_dict = {}

    res = []
    for name in parse_names.split(','):
        name = name.strip(
        )  # remove trailing and leading white spaces in the name

        # is the name in the options at all?
        if not name in params:
            logger.warning(
                f'Missing key {name} from params {params}. Skipping ...\n')
            continue

        # option_dict[name] should be a string
        res += [parse_value(params[name], variable_dict)]

    return res


##############################################################################
# From pyepr, being used by renderer using comm port.
#
"""The methods in this section were copied from Ansys renderer which used comm-ports."""

# UNITS
# LENGTH_UNIT         --- HFSS UNITS
# #Assumed default input units for ansys hfss
LENGTH_UNIT = 'meter'
# LENGTH_UNIT_ASSUMED --- USER UNITS
# if a user inputs a blank number with no units in `parse_fix`,
# we can assume the following using
LENGTH_UNIT_ASSUMED = 'mm'

try:
    u_reg = UnitRegistry()
    Q = u_reg.Quantity
except (ImportError, ModuleNotFoundError):
    pass  # raise NameError ("Pint module not installed. Please install.")


def extract_value_unit(expr, units):
    """
    :type expr: str
    :type units: str
    :return: float
    """
    # pylint: disable=broad-except
    try:
        return Q(expr).to(units).magnitude
    except Exception:
        try:
            return float(expr)
        except Exception:
            return expr


def fix_units(x, unit_assumed=None):
    '''
    Convert all numbers to string and append the assumed units if needed.
    For an iterable, returns a list
    '''
    unit_assumed = LENGTH_UNIT_ASSUMED if unit_assumed is None else unit_assumed
    if isinstance(x, str):
        # Check if there are already units defined, assume of form 2.46mm  or 2.0 or 4.
        if x[-1].isdigit() or x[-1] == '.':  # number
            return x + unit_assumed
        else:  # units are already applied
            return x

    elif isinstance(x, Number):
        return fix_units(str(x) + unit_assumed, unit_assumed=unit_assumed)

    elif isinstance(x, Iterable):  # hasattr(x, '__iter__'):
        return [fix_units(y, unit_assumed=unit_assumed) for y in x]
    else:
        return x


def parse_entry(entry, convert_to_unit=LENGTH_UNIT):
    '''
    Should take a list of tuple of list... of int, float or str...
    For iterables, returns lists
    '''
    if not isinstance(entry, list) and not isinstance(entry, tuple):
        return extract_value_unit(entry, convert_to_unit)
    else:
        entries = entry
        _entry = []
        for entry in entries:
            _entry.append(parse_entry(entry, convert_to_unit=convert_to_unit))
        return _entry


def parse_units(x):
    '''
    Convert number, string, and lists/arrays/tuples to numbers scaled
    in HFSS units.

    Converts to                  LENGTH_UNIT = meters  [HFSS UNITS]
    Assumes input units  LENGTH_UNIT_ASSUMED = mm      [USER UNITS]

    [USER UNITS] ----> [HFSS UNITS]
    '''
    return parse_entry(fix_units(x))