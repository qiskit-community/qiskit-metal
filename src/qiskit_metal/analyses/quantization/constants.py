"""Physical constants and Josephson-junction unit converters used by the
quantization analyses.

The ``Ic_from_Lj`` / ``Ej_from_Lj`` / ``Ec_from_Cs`` helpers are
vendored from ``pyEPR.calcs.convert.Convert`` so the analyses path
doesn't carry a runtime pyEPR dependency. The formulas are textbook.

Constants are kept at the original metal precision (CODATA 2014) for
internal consistency — ``lumped_capacitive.transmon_props`` and other
analysis functions use these values directly, and existing tests have
hardcoded expected values to this precision. The difference vs pyEPR's
SI 2019 constants is ~10⁻⁷ relative — below any quantum measurement
precision, well below the ``assertAlmostEqual`` test tolerance.

``phi0`` here is the **reduced** flux quantum (ℏ/2e). ``phinot`` is
the **full** flux quantum (h/2e). This matches the pre-vendor
convention used by ``lumped_capacitive.py`` and others — don't swap
them.
"""

import numpy as np

MHzRad = 2 * np.pi * 1e6
GHzRad = 2 * np.pi * 1e9

NANO = 1e-9
FEMTO = 1e-15
ONE_OVER_FEMTO = 1e15

# Original metal constants (CODATA 2014 precision). Kept stable so
# existing analyses + tests don't shift.
e = 1.60217657e-19  # electron charge
h = 6.62606957e-34  # Plank's
hbar = 1.0545718e-34  # Plank's reduced
phinot = 2.067 * 1e-15  # magnetic flux quantum (full, h/2e)
phi0 = phinot / (2 * np.pi)  # reduced magnetic flux quantum (ℏ/2e)


# ---------------------------------------------------------------------------
# Vendored Josephson-junction unit converters
# ---------------------------------------------------------------------------
#
# These mirror ``pyEPR.calcs.convert.Convert.Ic_from_Lj`` etc. The pyEPR
# originals route through pint; the call sites in metal only use a
# small fixed set of units, so we use direct lookup tables (avoids
# importing pint into pure-Python math and keeps the helpers fast).

_LENGTH_FACTORS = {"H": 1.0, "nH": 1e-9, "pH": 1e-12}
_CURRENT_FACTORS = {"A": 1.0, "mA": 1e-3, "uA": 1e-6, "nA": 1e-9}
_CAP_FACTORS = {"F": 1.0, "uF": 1e-6, "nF": 1e-9, "pF": 1e-12, "fF": 1e-15}
_FREQ_FACTORS = {"Hz": 1.0, "kHz": 1e3, "MHz": 1e6, "GHz": 1e9, "THz": 1e12}


def _factor(table: dict, unit: str, label: str) -> float:
    try:
        return table[unit]
    except KeyError:
        raise ValueError(f"Unknown {label} unit {unit!r}. Supported: {sorted(table)}")


def Ic_from_Lj(Lj, units_in: str = "nH", units_out: str = "A") -> float:
    """Josephson junction critical current from Josephson inductance.

    Ic = φ₀ / Lj, where φ₀ = ℏ / (2e) is the reduced flux quantum.

    Mirrors ``pyEPR.calcs.convert.Convert.Ic_from_Lj``.
    """
    Lj_SI = Lj * _factor(_LENGTH_FACTORS, units_in, "inductance")
    Ic_SI = phi0 / Lj_SI
    return Ic_SI / _factor(_CURRENT_FACTORS, units_out, "current")


def Ej_from_Lj(Lj, units_in: str = "nH", units_out: str = "MHz") -> float:
    """Josephson energy from Josephson inductance.

    Ej = φ₀² / Lj  (in Joules), returned as a frequency via Ej/h.
    """
    Lj_SI = Lj * _factor(_LENGTH_FACTORS, units_in, "inductance")
    Ej_J = phi0**2 / Lj_SI
    Ej_Hz = Ej_J / h
    return Ej_Hz / _factor(_FREQ_FACTORS, units_out, "frequency")


def Ec_from_Cs(Cs, units_in: str = "fF", units_out: str = "MHz") -> float:
    """Charging energy from shunt capacitance.

    Ec = e² / (2 Cs)  (in Joules), returned as a frequency via Ec/h.
    """
    Cs_SI = Cs * _factor(_CAP_FACTORS, units_in, "capacitance")
    Ec_J = e**2 / (2.0 * Cs_SI)
    Ec_Hz = Ec_J / h
    return Ec_Hz / _factor(_FREQ_FACTORS, units_out, "frequency")
