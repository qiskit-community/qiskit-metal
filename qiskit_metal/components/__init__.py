# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
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
Component (:mod:`qiskit_metal.components`)
=================================================

.. currentmodule:: qiskit_metal.components

Module containing all Qiskit Metal components.

@date: 2019

@author: Zlatko Minev (IBM)

Base Components
---------------

.. autosummary::
    :toctree: ../stubs/

    QComponent
    BaseJunction
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

    BumpPad
    CPWHangerT
    OpenToGround
    ShortToGround


Interconnects
-------------

.. autosummary::
    :toctree:

    CpwStraightLine
    CpwAutoStraightLine
    CpwMeanderSimple
    ConnectTheDots
    HybridPathfinder
    FakeCPW
    ResonatorRectangleSpiral


Junctions
---------

.. autosummary::
    :toctree:

    junctions


Passives
--------

.. autosummary::
    :toctree:

    Capacitor3Fingers


Qubits
----------

.. autosummary::
    :toctree:

    TransmonCross
    TransmonPocket
    TransmonPocketCL


User Components
---------------

.. autosummary::
    :toctree:

    MyQComponent


Submodules
----------

.. autosummary::
    :toctree:

    pathfinder

"""

from .. import is_component
from .base import QComponent
from .base import QRoute
from .base import BaseQubit
from .base import BaseJunction

from .. import config
if config.is_building_docs():
    from .base._parsed_dynamic_attrs import ParsedDynamicAttributes_Component
    from .basic.circle_caterpillar import CircleCaterpillar
    from .basic.circle_raster import CircleRaster
    from .basic.n_gon import NGon
    from .basic.n_square_spiral import NSquareSpiral
    from .basic.rectangle import Rectangle
    from .basic.rectangle_hollow import RectangleHollow
    from .connectors.bump_pad import BumpPad
    from .connectors.cpw_hanger_t import CPWHangerT
    from .connectors.open_to_ground import OpenToGround
    from .connectors.short_to_ground import ShortToGround
    from .interconnects.connect_the_dots import ConnectTheDots
    from .interconnects.cpw_autostraightline import CpwAutoStraightLine
    from .interconnects.cpw_basic_straight_line import CpwStraightLine
    from .interconnects.cpw_meander_simple import CpwMeanderSimple
    from .interconnects.fake_cpw import FakeCPW
    from .interconnects.pathfinder import HybridPathfinder
    from .interconnects.resonator_rectangle_spiral import ResonatorRectangleSpiral
    from .passives.capacitor_three_fingers import Capacitor3Fingers
    from .qubits.transmon_cross import TransmonCross
    from .qubits.transmon_pocket import TransmonPocket
    from .qubits.transmon_pocket_cl import TransmonPocketCL
    from .user_components.my_qcomponent import MyQComponent

    from .interconnects import pathfinder
