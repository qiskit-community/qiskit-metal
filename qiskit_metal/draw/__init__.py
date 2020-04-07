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
@auhtor: Zlatko Minev
@date: 2019
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
from . import cpw

# Useful functions
from .utility import vec_unit_norm, get_poly_pts, vec_add_z, vec_norm
from .basic import rectangle, is_rectangle, flip_merge, rotate, translate, scale, buffer,\
    rotate_position, _iter_func_geom_, union, subtract
