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

import numpy as np
from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.base.qubit import BaseQubit


class TunableCoupler01(BaseQubit):
    """
    One of the tunable couplers
    Based off the implementation in https://arxiv.org/pdf/2011.01261.pdf
    
    Inherits `BaseQubit` class

    Description:
        Creates a tunable coupler, interdigitated capacitor to ground, with a junction to ground and a coupler arm.
        The shapes origin is shown with 0. X the location of the SQUID.

                                |
                              __|__
                X             |   |
        |       |       |     | | |     |       |
        |       |       |     | | |     |       |
        |       |       |       |       |       |  
        --------------------0--------------------

    Options:
        Convention: Values (unless noted) are strings with units included,
        (e.g., '30um')
    Args:
        BaseQubit ([type]): [description]
    """

    default_options = Dict(pos_x='0um',
                           pos_y='0um',
                           orientation='0',
                           layer='1',
                           c_width='300um',
                           l_width='10um',
                           l_gap='6um',
                           a_height='60um')

    component_metadata = Dict(short_name='Pocket',
                              _qgeometry_table_path='True',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='True')

    def make(self):
        """
        Builds the component
        """
        p = self.p

        #Draw the charge island
        btm = draw.shapely.geometry.box(-p.c_width / 2, -p.l_width / 2, 0,
                                        p.l_width / 2)

        x_spot = p.c_width / 2 - p.l_width / 2

        arm1 = draw.shapely.geometry.box(-(x_spot + p.l_width / 2),
                                         p.l_width / 2,
                                         -(x_spot - p.l_width / 2), p.a_height)
        arm2 = draw.shapely.geometry.box(-((x_spot) * 3 / 5 + p.l_width / 2),
                                         p.l_width / 2,
                                         -((x_spot) * 3 / 5 - p.l_width / 2),
                                         p.a_height)
        arm3 = draw.shapely.geometry.box(-((x_spot) * 1 / 5 + p.l_width / 2),
                                         p.l_width / 2,
                                         -((x_spot) * 1 / 5 - p.l_width / 2),
                                         p.a_height)

        left_side = draw.shapely.ops.cascaded_union([btm, arm1, arm2, arm3])
        cap_island = draw.shapely.ops.cascaded_union([
            left_side,
            draw.shapely.affinity.scale(left_side,
                                        xfact=-1,
                                        yfact=1,
                                        origin=(0, 0))
        ])

        cap_subtract = cap_island.buffer(p.l_gap, cap_style=3, join_style=2)

        #Draw the junction
        rect_jj = draw.LineString([(-(x_spot) * 3 / 5, p.a_height),
                                   (-(x_spot) * 3 / 5, p.a_height + p.l_gap)])

        #Draw the connector

        #Rotate and translate.
        c_items = [cap_island, cap_subtract]
        c_items = draw.rotate(c_items, p.orientation, origin=(0, 0))
        c_items = draw.translate(c_items, p.pos_x, p.pos_y)
        [cap_island, cap_subtract] = c_items

        #Add to qgeometry
        self.add_qgeometry('poly', {'cap_island': cap_island}, layer=p.layer)
        self.add_qgeometry('poly', {'cap_subtract': cap_subtract},
                           layer=p.layer,
                           subtract=True)
