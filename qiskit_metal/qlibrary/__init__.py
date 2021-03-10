# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2020.
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
QLibrary (:mod:`qiskit_metal.qlibrary`)
=================================================

.. currentmodule:: qiskit_metal.qlibrary

Module containing all Qiskit Metal QLibrary.

.. _qlibrary:

Base Components
---------------

.. autosummary::
    :toctree: ../stubs/

    QComponent
    BaseQubit
    ParsedDynamicAttributes_Component
    QRoute
    QRouteLead
    QRoutePoint


Basic
-----

.. autosummary::
    :toctree:

    CircleCaterpillar
    CircleRaster
    NGon
    NSquareSpiral
    Rectangle
    RectangleHollow


Connectors
----------

.. autosummary::
    :toctree:

    CPWFingerCap
    CPWHangerT
    CPWT
    CPWTFingerCap
    OpenToGround
    ShortToGround


Interconnects
-------------

.. autosummary::
    :toctree:

    RouteStraight
    RouteFramed
    RouteMeander
    RouteAnchors
    RouteMixed
    RoutePathfinder
    ResonatorRectangleSpiral



Passives
--------

.. autosummary::
    :toctree:

    LaunchpadWirebond
    LaunchpadWirebondCoupled
    CapThreeFingers


Qubits
----------

.. autosummary::
    :toctree:

    TransmonConcentric
    TransmonCross
    TransmonCrossFL
    TransmonPocket
    TransmonPocketCL
    TransmonPocket6
    TunableCoupler01


Submodules
----------

.. autosummary::
    :toctree:

    anchored_path

"""

from .. import is_component
from .base import QComponent
from .base import QRoute
from .base import BaseQubit

from .. import config
if config.is_building_docs():
    from .base.qroute import QRouteLead
    from .base.qroute import QRoutePoint
    from .base._parsed_dynamic_attrs import ParsedDynamicAttributes_Component
    from .basic.circle_caterpillar import CircleCaterpillar
    from .basic.circle_raster import CircleRaster
    from .basic.n_gon import NGon
    from .basic.n_square_spiral import NSquareSpiral
    from .basic.rectangle import Rectangle
    from .basic.rectangle_hollow import RectangleHollow
    from .connectors.cpw_hanger_t import CPWHangerT
    from .connectors.cpw_finger_cap import CPWFingerCap
    from .connectors.cpw_t import CPWT
    from .connectors.cpw_t_finger_cap import CPWTFingerCap
    from .connectors.open_to_ground import OpenToGround
    from .connectors.short_to_ground import ShortToGround
    from .interconnects.straight_path import RouteStraight
    from .interconnects.framed_path import RouteFramed
    from .interconnects.meandered import RouteMeander
    from .interconnects.anchored_path import RouteAnchors
    from .interconnects.mixed_path import RouteMixed
    from .interconnects.pathfinder import RoutePathfinder
    from .interconnects.resonator_rectangle_spiral import ResonatorRectangleSpiral
    from .passives.launchpad_wb import LaunchpadWirebond
    from .passives.launchpad_wb_coupled import LaunchpadWirebondCoupled
    from .passives.cap_three_fingers import CapThreeFingers
    from .qubits.transmon_concentric import TransmonConcentric
    from .qubits.transmon_cross import TransmonCross
    from .qubits.transmon_cross_fl import TransmonCrossFL
    from .qubits.transmon_pocket import TransmonPocket
    from .qubits.transmon_pocket_cl import TransmonPocketCL
    from .qubits.transmon_pocket_6 import TransmonPocket6
    from .qubits.tunable_coupler_01 import TunableCoupler01

    from .interconnects import anchored_path
