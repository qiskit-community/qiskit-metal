#-*- coding: utf-8 -*-
"""The methods in this module were copied from Ansys renderer which used comm-ports."""

from numbers import Number
from collections.abc import Iterable
from pint import UnitRegistry

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