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
Draw (:mod:`qiskit_metal.draw`)
=================================================

.. currentmodule:: qiskit_metal.draw

Module containing all Qiskit Metal draw code.

@date: 2019

@author: Zlatko Minev (IBM)

UNDER CONSTRUCTION

Vector
---------------

.. autosummary::
    :toctree: ../stubs/

    Vector-TBD

Submodules
----------

.. autosummary::
    :toctree:

    basic
    utility-TBD

"""

import shapely
import shapely.wkt as wkt

# Base Geometry Definitions - extend here
from shapely.geometry.base import BaseGeometry
from shapely.geometry import Point, LineString, Polygon
from shapely.geometry import box, shape
from shapely.ops import cascaded_union

from . import basic
from . import utility
from . import mpl
#from . import cpw

# Useful functions
from .utility import get_poly_pts, Vector
from .basic import rectangle, is_rectangle, flip_merge, rotate, translate, scale, buffer,\
    rotate_position, _iter_func_geom_, union, subtract
from .mpl import render, figure_spawn