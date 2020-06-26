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

UNDER CONSTRUCTION


Base Components
---------------

.. autosummary::
    :toctree: ../stubs/

    QComponent
    BaseJunction
    BaseQubit
    ParsedDynamicAttributes_Component
    MyQComponent


Basic
-----

.. autosummary::
    :toctree:

    CircleCaterpillar
    CircleRaster
    Rectangle
    RectangleHollow


Connectors
----------

.. autosummary::
    :toctree:

    connectors


Interconnects
-------------

.. autosummary::
    :toctree:

    Connector
    CpwMeanderSimple
    FakeCPW


Junctions
---------

.. autosummary::
    :toctree:

    junctions

Qubits
----------

.. autosummary::
    :toctree:

    TransmonCross
    TransmonPocket-TBD
    TransmonPocketCL-TBD

"""
from .. import is_component
from .base import QComponent
from .base.qubit import BaseQubit
from .base.junction import BaseJunction
from .base._parsed_dynamic_attrs import ParsedDynamicAttributes_Component
from .base._template import MyQComponent
from .basic.circle_caterpillar import CircleCaterpillar
from .basic.circle_raster import CircleRaster
from .basic.rectangle import Rectangle
from .basic.rectangle_hollow import RectangleHollow
from .interconnects.cpw_meander import Connector
from .interconnects.cpw_meander import CpwMeanderSimple
from .interconnects.fake_cpw import FakeCPW
from .qubits.transmon_cross import TransmonCross