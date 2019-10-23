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

from copy import deepcopy
from ...config import DEFAULT_OPTIONS, DEFAULT
from ...draw_functions import shapely, shapely_rectangle, translate, translate_objs,\
    rotate_objs, rotate_obj_dict, scale_objs, _angle_Y2X, make_connector_props,\
    Polygon, parse_options_user, parse_units_user, buffer, LineString,\
    Dict
from ... import draw_hfss