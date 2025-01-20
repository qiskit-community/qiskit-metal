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
QLibrary (:mod:`qiskit_metal.qlibrary`)
=================================================

.. currentmodule:: qiskit_metal.qlibrary

Module containing all Qiskit Metal QLibrary.

.. _qlibrary:

Core Classes
----------------

.. autosummary::
    :toctree: ../stubs/

    QComponent
    ParsedDynamicAttributes_Component
    BaseQubit
    QRoute
    QRouteLead
    QRoutePoint


Sample Shapes
-----------------

.. autosummary::
    :toctree:

    CircleCaterpillar
    CircleRaster
    NGon
    NSquareSpiral
    Rectangle
    RectangleHollow


Lumped
----------

.. autosummary::
    :toctree:

    Cap3Interdigital
    CapNInterdigital
    ResonatorCoilRect


Couplers
------------

.. autosummary::
    :toctree:

    CoupledLineTee
    LineTee
    CapNInterdigitalTee
	TunableCoupler01
    TunableCoupler02


Resonator
------------

.. autosummary::
    :toctree:

    ReadoutResFC
    ResonatorLumped


Terminations
----------------

.. autosummary::
    :toctree:

    LaunchpadWirebond
    LaunchpadWirebondCoupled
	LaunchpadWirebondDriven
    OpenToGround
    ShortToGround


Transmission Lines
----------------------

.. autosummary::
    :toctree:

    RouteStraight
    RouteFramed
    RouteMeander
    RouteAnchors
    RouteMixed
    RoutePathfinder


Qubits
----------

.. autosummary::
    :toctree:

    jj_dolan
    jj_manhattan
    TransmonConcentric
    TransmonConcentricType2
    TransmonCross
    TransmonCrossFL
    TransmonInterdigitated
    TransmonPocket
    TransmonPocketCL
    TransmonPocket6
    TransmonPocketTeeth
    TunableCoupler01
    SQUID_LOOP
    StarQubit


Submodules
--------------

.. autosummary::
    :toctree:

    anchored_path

"""

from .core import QComponent
from .core import QRoute
from .core import BaseQubit

from .. import config
if config.is_building_docs():
    from .core import QRouteLead
    from .core import QRoutePoint
    from .core._parsed_dynamic_attrs import ParsedDynamicAttributes_Component
    from .sample_shapes.circle_caterpillar import CircleCaterpillar
    from .sample_shapes.circle_raster import CircleRaster
    from .sample_shapes.n_gon import NGon
    from .sample_shapes.n_square_spiral import NSquareSpiral
    from .sample_shapes.rectangle import Rectangle
    from .sample_shapes.rectangle_hollow import RectangleHollow
    from .couplers.coupled_line_tee import CoupledLineTee
    from .couplers.line_tee import LineTee
    from .couplers.cap_n_interdigital_tee import CapNInterdigitalTee
    from .couplers.tunable_coupler_01 import TunableCoupler01
    from .couplers.tunable_coupler_02 import TunableCoupler02
    from .lumped.cap_n_interdigital import CapNInterdigital
    from .lumped.cap_3_interdigital import Cap3Interdigital
    from .lumped.resonator_coil_rect import ResonatorCoilRect
    from .terminations.launchpad_wb import LaunchpadWirebond
    from .terminations.launchpad_wb_coupled import LaunchpadWirebondCoupled
    from .terminations.launchpad_wb_driven import LaunchpadWirebondDriven
    from .terminations.open_to_ground import OpenToGround
    from .terminations.short_to_ground import ShortToGround
    from .tlines.straight_path import RouteStraight
    from .tlines.framed_path import RouteFramed
    from .tlines.meandered import RouteMeander
    from .tlines.anchored_path import RouteAnchors
    from .tlines.mixed_path import RouteMixed
    from .tlines.pathfinder import RoutePathfinder
    from .qubits.JJ_Dolan import jj_dolan
    from .qubits.JJ_Manhattan import jj_manhattan
    from .qubits.transmon_concentric import TransmonConcentric
    from .qubits.transmon_concentric_type_2 import TransmonConcentricType2
    from .qubits.transmon_cross import TransmonCross
    from .qubits.transmon_cross_fl import TransmonCrossFL
    from .qubits.Transmon_Interdigitated import TransmonInterdigitated
    from .qubits.transmon_pocket import TransmonPocket
    from .qubits.transmon_pocket_cl import TransmonPocketCL
    from .qubits.transmon_pocket_6 import TransmonPocket6
    from .qubits.transmon_pocket_teeth import TransmonPocketTeeth
    from .qubits.SQUID_loop import SQUID_LOOP
    from .qubits.star_qubit import StarQubit
    from .resonators.readoutres_fc import ReadoutResFC
    from .resonators.resonator_lumped import ResonatorLumped

    from .tlines import anchored_path
