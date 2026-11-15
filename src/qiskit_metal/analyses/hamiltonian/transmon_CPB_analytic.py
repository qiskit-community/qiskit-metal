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
"""
Models the transmon qubit in the cooper-pair charge basis
and calculate the exact (analytic) solutions

Key References:
    - J. Koch et al. "Charge-insensitive qubit design derived from the Cooper
      pair box" Phys. Rev. A. 76, 042319 (2007), Eq. (2.11).

@author: Nick Lanzillo (IBM)
"""

import numpy as np
from scipy import linalg

__all__ = ["Hcpb_analytic", "mathieu_level"]


def mathieu_level(m: int, ng: float, Ej: float, Ec: float) -> float:
    r"""Energy of transmon level ``m`` from Mathieu characteristic values.

    Koch et al. Eq. (2.11): :math:`E_m = E_C\, a_{2[n_g + k(m, n_g)]}(q)`,
    :math:`q = -E_J/2E_C`, where :math:`a_\nu` is the characteristic value
    of real order :math:`\nu`.

    The value is the ``m``-th eigenvalue of the Hill (Fourier) matrix of
    Mathieu's equation with Floquet exponent :math:`2 n_g`, which is
    :math:`a_{2[n_g + k(m, n_g)]}(q)` for every ``ng``, integer orders
    included (ng = 0: :math:`a_0, b_2, a_2, \dots`; ng = 1/2:
    :math:`a_1, b_1, a_3, \dots`). ``scipy.special.mathieu_a`` and
    ``mathieu_b`` are not used: up to scipy 1.18.1 they return the value of
    another order in narrow windows of ``q`` (scipy#4479, scipy#14526, fixed
    on scipy main by scipy#25128), e.g. ``mathieu_b(5, -20.9)`` equals
    ``mathieu_b(3, -20.9)`` (#1252).

    ``ng`` is reduced modulo 1 into [-1/2, 1/2] first (the spectrum has
    period 1 in ``ng``).

    Args:
        m (int): Level index (0 = ground state).
        ng (float): Offset charge in units of 2e.
        Ej (float): Josephson energy.
        Ec (float): Charging energy, same units as ``Ej``.

    Returns:
        float: :math:`E_m` in the units of ``Ec``.
    """
    m = int(m)
    ng = ((float(ng) + 0.5) % 1.0) - 0.5
    q = -0.5 * Ej / Ec
    # Hill matrix: diag (2 (n - ng))^2, off-diagonal q, n in [-N, N].
    ncut = 30 + m
    n = np.arange(-ncut, ncut + 1)
    evals = linalg.eigh_tridiagonal(
        (2.0 * (n - ng)) ** 2,
        q * np.ones(2 * ncut),
        select="i",
        select_range=(m, m),
        eigvals_only=True,
    )
    value = evals[0]
    return Ec * value


class Hcpb_analytic:
    """
    Analytic version of Hamiltonian-model Cooper pair box (Hcpb) class.

    Used calculate the exact eigenvalues for arbitrary Ej, Ec, ng values.
    """

    def __init__(self, Ej: float = None, Ec: float = None, ng: float = 0.5):
        """
        Generate a Cooper-pair box (CPB) model.

        Arguments:
            Ej (float): Josephson energy of the JJ
            Ec (float): Charging energy of the CPB
            ng (float): Offset charge of the CPB (ng=0.5 is the sweet spot).
                        `ng` only needs to run between -0.5 and 0.5.
                        `ng` is defined in units of cooper pairs (2e)
        """

        self._Ej = Ej
        self._Ec = Ec
        self._ng = ng
        self.evals = None
        self.evecs = None

    def evalue_k(self, k: int):
        """
        Return the eigenvalue of the Hamiltonian for level k.

        Uses :func:`mathieu_level` (Koch et al. Eq. 2.11); see there for
        how integer and non-integer Mathieu orders are handled.

        Arguments:
            k (int): Index of the eigenvalue

        Returns:
            float: eigenvalue of the Hamiltonian
        """
        self.evals = mathieu_level(k, self._ng, self._Ej, self._Ec)
        return self.evals
