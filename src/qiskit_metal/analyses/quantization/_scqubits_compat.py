# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""Keep scqubits working with numpy 2 and qutip 5.3+.

Two incompatibilities break ``HilbertSpace.hamiltonian()`` and with it the
LOM 2.0 Hamiltonian step (``CompositeSystem.hamiltonian_results``):

* scqubits < 4.2 builds arrays with ``np.float_`` / ``np.complex_``, which
  numpy 2 removed. On macOS with Python >= 3.10, scqubits 4.2+ caps scipy at
  1.13.1, so resolvers that keep a newer scipy fall back to scqubits 4.1.
* qutip 5.3 returns scipy sparse *arrays* from ``Qobj.data.as_scipy()``.
  scqubits (through 4.3.1) converts every Qobj with
  ``Qobj_to_scipy_csc_matrix`` and then accepts only sparse *matrices*, so it
  raises ``TypeError: Unsupported operator type: csc_array``.

``apply()`` restores the two numpy aliases and makes the converter return a
``csc_matrix``. Each fix is applied only when it is needed, and none changes
results. Remove this module once scqubits handles both.
"""

import sys

import numpy as np
import scipy.sparse as sp


def _restore_numpy_aliases():
    if not hasattr(np, "float_"):
        np.float_ = np.float64
    if not hasattr(np, "complex_"):
        np.complex_ = np.complex128


def _qutip_returns_sparse_arrays() -> bool:
    import qutip

    data = qutip.num(2).to("csr").data.as_scipy()
    return not sp.isspmatrix(data)


def _qobj_to_csc_matrix(qobj):
    """scqubits' ``Qobj_to_scipy_csc_matrix``, always returning a matrix."""
    return sp.csc_matrix(qobj.to("csr").data.as_scipy())


def _patch_converter():
    """Swap the converter in every scqubits module that bound it by name."""
    from scqubits.utils import misc

    original = getattr(misc, "Qobj_to_scipy_csc_matrix", None)
    if original is None or original is _qobj_to_csc_matrix:
        return
    for name, module in list(sys.modules.items()):
        if name.startswith("scqubits") and module is not None:
            if getattr(module, "Qobj_to_scipy_csc_matrix", None) is original:
                module.Qobj_to_scipy_csc_matrix = _qobj_to_csc_matrix


def apply():
    """Apply the fixes this environment needs; safe to call more than once."""
    _restore_numpy_aliases()
    if _qutip_returns_sparse_arrays():
        _patch_converter()
