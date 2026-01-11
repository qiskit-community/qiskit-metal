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

# modified by Chalmers/SK 20210611 to add DesignFlipChip
"""
=================================================
Designs (:mod:`qiskit_metal.designs`)
=================================================

.. currentmodule:: qiskit_metal.designs

Module containing all Qiskit Metal designs.

.. _qdesign:

QDesign
---------------

.. autosummary::
    :toctree: .

    QDesign


DesignPlanar
---------------

.. autosummary::
    :toctree: .

    DesignPlanar


MultiPlanar
---------------

.. autosummary::
    :toctree: .

    MultiPlanar


DesignFlipChip
---------------

.. autosummary::
    :toctree: .

    DesignFlipChip

QNet
---------------

.. autosummary::
    :toctree: .

    QNet


InterfaceComponents
-------------------

.. autosummary::
    :toctree: .

    Components
"""

from qiskit_metal import Dict
from qiskit_metal import is_design
from qiskit_metal.designs.design_base import QDesign
from qiskit_metal.designs.design_planar import DesignPlanar
from qiskit_metal.designs.design_multiplanar import MultiPlanar
from qiskit_metal.designs.design_flipchip import DesignFlipChip
from qiskit_metal.designs.net_info import QNet
from qiskit_metal.designs.interface_components import Components
