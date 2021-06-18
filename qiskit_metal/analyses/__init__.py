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
"""
=================================================
Analyses (:mod:`qiskit_metal.analyses`)
=================================================

.. currentmodule:: qiskit_metal.analyses

Module containing all Qiskit Metal analyses.

.. _qanalysis:


Analysis Core
-------------

.. autosummary::
    :toctree:

    QAnalysis
    QAnalysisRenderer

Hamiltonian
-----------

.. autosummary::
    :toctree:

    Hcpb
    Hcpb_analytic
    HO_wavefunctions
    transmon_analytics

Electromagnetic & quantization / parameter extraction
-----------------------------------------------------

.. autosummary::
    :toctree:

    cpw_calculations
    kappa_calculation

Sweeping Options
----------------

.. autosummary::
    :toctree:

    Sweeping

Quantization
------------

.. autosummary::
    :toctree:

    LumpedElementsSim
    LOManalysis
    EigenmodeSim
    EPRanalysis
    ScatteringImpedanceSim
    lumped_capacitive

"""

from .. import config

from .core.base import QAnalysis
from .core.base_with_renderer import QAnalysisRenderer
from .em import cpw_calculations
from .em import kappa_calculation
from .quantization import lumped_capacitive
from .quantization import EPRanalysis
from .quantization import LOManalysis
from .quantization import LumpedElementsSim
from .quantization import EigenmodeSim
from .quantization import ScatteringImpedanceSim
from .hamiltonian.transmon_charge_basis import Hcpb
from .hamiltonian import HO_wavefunctions
from .hamiltonian import transmon_analytics
from .hamiltonian.transmon_CPB_analytic import Hcpb_analytic
from .sweep_options.sweeping import Sweeping
