# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""Run ``sequencing`` 1.2.0 on qutip 5 (#1231).

``sequencing`` (https://github.com/sequencing-dev/sequencing, last release
1.2.0, 2022) is an optional third-party package used by ``lom_extensions`` and
``lom_time_evolution_sim``. It is written for qutip 4, and two places stop it
on the qutip >= 5.1 that Quantum Metal requires:

* ``CompiledPulseSequence.run`` and ``.propagator`` configure the solver
  through ``qutip.Options`` attributes and ``qutip.rhs_clear()``, pass
  ``e_ops`` positionally, and pass array coefficients without a ``tlist``.
* ``System.couplings``, ``System.H0`` and ``System.c_ops`` drop zero
  operators with ``Qobj.data.nnz``, which qutip 5 data layers do not have.

``apply()`` replaces the two solver calls with qutip 5 equivalents (same
solver settings: ``max_step`` = the sequence time step, states stored, cubic
interpolation of the pulse arrays) and wraps the three ``System`` methods so
they call the original with ``clean=False`` and drop the zero operators
themselves. Nothing else in ``sequencing`` is changed, nothing is copied from
it beyond the solver call, and nothing happens with qutip 4 or with a
``sequencing`` release newer than 1.2.0. Remove this module once
``sequencing`` supports qutip 5.
"""

import re
from importlib.metadata import PackageNotFoundError, version

import numpy as np

_PATCHED = "_qiskit_metal_qutip5_compat"


def _major_minor(dist: str, installed: str = None):
    if installed is None:
        try:
            installed = version(dist)
        except PackageNotFoundError:
            return None
    return tuple(int(part) for part in re.findall(r"\d+", installed)[:2])


def needs_patch(qutip_version: str = None, sequencing_version: str = None) -> bool:
    """True for qutip >= 5 together with sequencing <= 1.2.

    Args:
        qutip_version (str): version to check instead of the installed one.
        sequencing_version (str): version to check instead of the installed one.
    """
    qutip_v = _major_minor("qutip", qutip_version)
    seq_v = _major_minor("sequencing", sequencing_version)
    return bool(qutip_v and seq_v and qutip_v >= (5, 0) and seq_v <= (1, 2))


def _solver_options(options, dt, store_states):
    """qutip 5 options dict with sequencing's defaults, updated by ``options``."""
    opts = {"max_step": dt, "store_states": store_states}
    if options is not None:
        opts.update(dict(options))
    return opts


def _add_static_channel(seq):
    """Add the static Hamiltonian as channel ``H0``, as sequencing does."""
    if "H0" not in seq.hc.channels:
        H0 = sum(seq.system.H0())
        if isinstance(H0, int) and H0 == 0:
            H0 = 0 * seq.system.I()
        seq.hc.add_channel("H0", H=H0, time_dependent=False)


def _time_dependent(ops, times):
    """``[op, coefficient array]`` terms as QobjEvo sampled on ``times``."""
    import qutip

    return [
        qutip.QobjEvo(op, tlist=times) if isinstance(op, list) else op for op in ops
    ]


def _run(
    self,
    init_state,
    c_ops=None,
    e_ops=None,
    options=None,
    only_final_state=False,
    progress_bar=None,
):
    """``CompiledPulseSequence.run`` for qutip 5 (same arguments and result).

    ``options`` may be a dict of qutip 5 solver options; it updates the
    defaults ``max_step`` = the sequence time step and ``store_states=True``.
    """
    import qutip
    from sequencing.sequencing.common import ops2dms

    c_ops = list(c_ops or [])
    e_ops = ops2dms(list(e_ops or []))
    _add_static_channel(self)
    c_ops.extend(self.system.c_ops())
    H, C_ops, times = self.build_hamiltonian()
    c_ops.extend(C_ops)
    tlist = [times.min(), times.max()] if only_final_state else times
    opts = _solver_options(options, self.hc.dt, True)
    if progress_bar:
        opts["progress_bar"] = "text"
    return qutip.mesolve(
        qutip.QobjEvo(H, tlist=times),
        init_state,
        tlist,
        c_ops=_time_dependent(c_ops, times),
        e_ops=e_ops,
        options=opts,
    )


def _propagator(self, c_ops=None, options=None, unitary_mode="batch", parallel=False):
    """``CompiledPulseSequence.propagator`` for qutip 5.

    ``unitary_mode`` and ``parallel`` are accepted for compatibility and
    ignored: qutip 5's ``propagator`` has no such modes.
    """
    import qutip

    c_ops = list(c_ops or [])
    _add_static_channel(self)
    c_ops.extend(self.system.c_ops())
    H, C_ops, times = self.build_hamiltonian()
    c_ops.extend(C_ops)
    # qutip 5 builds the propagator by evolving the identity, so the states
    # must be stored; tighter tolerances keep it as accurate as ``run``.
    opts = {"atol": 1e-10, "rtol": 1e-8, **_solver_options(options, self.hc.dt, True)}
    props = qutip.propagator(
        qutip.QobjEvo(H, tlist=times),
        times,
        c_ops=_time_dependent(c_ops, times),
        options=opts,
    )
    return props if isinstance(props, list) else [props]


def _is_nonzero(op) -> bool:
    return bool(np.any(op.full()))


def _drop_zero_operators(method):
    """Wrap a ``System`` method with a ``clean`` flag so it avoids ``data.nnz``."""

    def wrapper(self, modes=None, clean=True):
        ops = method(self, modes=modes, clean=False)
        return [op for op in ops if _is_nonzero(op)] if clean else ops

    wrapper.__doc__ = method.__doc__
    wrapper.__name__ = method.__name__
    wrapper.__wrapped__ = method
    return wrapper


def apply():
    """Patch ``sequencing`` for qutip 5 if needed; safe to call more than once."""
    if not needs_patch():
        return
    from sequencing.sequencing.basic import CompiledPulseSequence
    from sequencing.system import System

    if getattr(CompiledPulseSequence, _PATCHED, False):
        return
    CompiledPulseSequence.run = _run
    CompiledPulseSequence.propagator = _propagator
    for name in ("couplings", "H0", "c_ops"):
        setattr(System, name, _drop_zero_operators(getattr(System, name)))
    setattr(CompiledPulseSequence, _PATCHED, True)
