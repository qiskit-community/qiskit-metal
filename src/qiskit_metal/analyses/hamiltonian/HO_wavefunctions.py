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
"""This code calculations the wavefunction(s) of the simple harmonic oscillator
corresponding to an LC circuit.

Key References:
    - *R. Shankar*, "Principles of Quantum Mechanics", Second Edition, Springer (1994)
    - or any other undergraduate quantum mechanics textbook)
"""

import numpy as np
from scipy.special import eval_hermite, gammaln

__all__ = ["wavefunction"]


def wavefunction(L, C, n, x, hbar=1.0):
    r"""Return the n-th energy eigenfunction of the LC (harmonic) oscillator.

    The coordinate ``x`` is the capacitor charge :math:`Q`. With
    :math:`H = \Phi^2/2L + Q^2/2C`, the flux :math:`\Phi` is the momentum
    conjugate to :math:`Q`, so the "mass" is :math:`L` and

    .. math::

        \omega = 1/\sqrt{LC}, \qquad
        \psi_n(Q) = \frac{1}{\sqrt{2^n n!}}
        \left(\frac{L\omega}{\pi\hbar}\right)^{1/4}
        e^{-L\omega Q^2/2\hbar}\,
        H_n\!\left(\sqrt{L\omega/\hbar}\,Q\right),

    normalized so that :math:`\int |\psi_n|^2\,dQ = 1`. Note
    :math:`L\omega = \sqrt{L/C} = Z`, the characteristic impedance.

    Args:
        L (float): The inductance of the inductor in an LC circuit.
        C (float): The capacitance of the capacitor in an LC circuit.
        n (int): The energy level (any non-negative integer).
        x (float or array): The charge at which the wavefunction is evaluated.
        hbar (float): Reduced Planck constant in the units of ``L``, ``C``
            and ``x``. Defaults to 1 (natural units); pass
            ``scipy.constants.hbar`` for SI inputs.

    Returns:
        float or array: :math:`\psi_n(x)`.
    """
    n = int(n)
    if n < 0:
        raise ValueError(f"n must be a non-negative integer, got {n}")
    # Fundamental (angular) frequency of the LC circuit.
    omega = 1.0 / np.sqrt(L * C)
    m_omega = L * omega  # = sqrt(L/C)
    xi = np.sqrt(m_omega / hbar) * np.asarray(x, dtype=float)
    # (2^n n!)^(-1/2) computed in log form so large n does not overflow.
    log_norm = -0.5 * (n * np.log(2.0) + gammaln(n + 1))
    prefactor = np.exp(log_norm) * (m_omega / (np.pi * hbar)) ** 0.25
    return prefactor * np.exp(-0.5 * xi**2) * eval_hermite(n, xi)
