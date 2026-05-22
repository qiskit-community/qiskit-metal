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

# pyEPR is an opt-in dependency (extras: ``[ansys]``). Keep this module
# importable on the lite install — the pyEPR symbols load lazily via
# ``__getattr__`` on first attribute access. Callers get a clear error
# at use time rather than at ``import qiskit_metal`` time.
#
# Historical note: ``pyEPR.hfss`` was removed in pyEPR 0.9; these
# symbols now live in ``pyEPR.ansys``.

# See also: is_variable_name, is_numeric_possible
# from ... import Dict
from qiskit_metal.toolbox_metal.parsing import parse_value

__all__ = ["parse_value_hfss", "unparse_units"]  # noqa: F822 (unparse_units is exposed via __getattr__)


def __getattr__(name):
    """PEP 562 module-level ``__getattr__`` — lazy-load pyEPR symbols.

    Lets ``from .parse import unparse_units`` work in callers without
    pulling pyEPR at this module's import time. The actual import
    happens on the first attribute access.
    """
    if name == "unparse_units":
        from pyEPR.ansys import unparse_units as _u

        return _u
    if name == "__parse_units_hfss__":
        from pyEPR.ansys import parse_units as _p

        return _p
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def parse_value_hfss(*args):
    """Parse to HFSS units (from user units)."""
    from pyEPR.ansys import parse_units as _parse_units_hfss

    return _parse_units_hfss(*args)


# TODO: function to itterate and convert user units to


def to_ansys_units(
    value,
):  # can make more efifiecnt if we assume this is already a float
    """Converve given value to ansys units.

    Args:
        value (float): Value
    """
    from pyEPR.ansys import parse_units as _parse_units_hfss

    _parse_units_hfss(value)
