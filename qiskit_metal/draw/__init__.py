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

import shapely
import shapely.wkt as wkt

# Base Geometry Definitions - extend here
from shapely.geometry.base import BaseGeometry
from shapely.geometry import Point, LineString, Polygon
from shapely.geometry import box, shape
from shapely.ops import unary_union

from . import basic
from . import utility
from . import mpl

# Useful functions
from .utility import get_poly_pts, Vector
from .basic import rectangle, is_rectangle, flip_merge, rotate, translate, scale, buffer,\
    rotate_position, _iter_func_geom_, union, subtract
from .mpl import render, figure_spawn
