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
from scipy.special import mathieu_a, mathieu_b

__all__ = ["Hcpb_analytic", "mathieu_level"]


def _koch_index(m, ng):
    """2 [ng + k(m, ng)] of Koch Eq. (2.11), for -1/2 <= ng <= 1/2."""
    if ng == 0:
        return m + 1.0 - ((m + 1.0) % 2.0)
    return (
        m
        + 1.0
        - ((m + 1.0) % 2.0)
        + 2.0 * ng * ((-1.0) ** (m - 0.5 * (np.sign(ng) - 1.0)))
    )


def mathieu_level(m: int, ng: float, Ej: float, Ec: float) -> float:
    r"""Energy of transmon level ``m`` from Mathieu characteristic values.

    Koch et al. Eq. (2.11): :math:`E_m = E_C\, a_{2[n_g + k(m, n_g)]}(q)`,
    :math:`q = -E_J/2E_C`, where :math:`a_\nu` is the characteristic value
    of real order :math:`\nu`.

    * At integer order (``ng`` = 0 or 1/2 modulo 1) the even and odd
      solutions are degenerate in the index: even ``m`` uses
      ``scipy.special.mathieu_a`` and odd ``m`` uses ``mathieu_b`` of the
      same order (ng = 0: :math:`a_m`, :math:`b_{m+1}`; ng = 1/2:
      :math:`a_{m+1}`, :math:`b_m`).
    * scipy has no characteristic values of non-integer order, so for other
      ``ng`` the value is computed from the Hill (Fourier) matrix of
      Mathieu's equation with Floquet exponent :math:`2 n_g`, whose
      ``m``-th eigenvalue is :math:`a_{2[n_g + k(m, n_g)]}(q)`.

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
    index = _koch_index(m, ng)
    order = round(index)
    if abs(index - order) < 1e-12:
        order = abs(int(order))
        value = mathieu_a(order, q) if m % 2 == 0 else mathieu_b(order, q)
    else:
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
