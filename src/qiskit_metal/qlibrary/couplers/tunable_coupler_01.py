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

import numpy as np
from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import BaseQubit


class TunableCoupler01(BaseQubit):
    """One of the tunable couplers Based off the implementation in
    https://arxiv.org/pdf/2011.01261.pdf.

    WIP - initial test structure

    Inherits `BaseQubit` class

    Description:
        Creates a tunable coupler, interdigitated capacitor to ground, with a junction to ground and a coupler arm.
        The shapes origin is shown with 0. X the location of the SQUID.

    ::

                            connection claw
                              _____
                X             |   |
        |       |       |     | | |     |       |
        |       |       |     | | |     |       | charge island
        |       |       |       |       |       |
        --------------------0--------------------

    .. image::
        TunableCoupler01.png

    .. meta::
        :description: Tunable Coupler 01

    Options:
        Convention: Values (unless noted) are strings with units included,
        (e.g., '30um')

    BaseQubit Default Options:
        * connection_pads: empty Dict -- Currently not used, connection count is static. (WIP)
        * _default_connection_pads: empty Dict -- The default values for the (if any) connection lines of the qubit.

    Default Options:
        * c_width: '400um' -- The width (x-axis) of the interdigitated charge island
        * l_width: '20um' -- The width of lines forming the body and arms of the charge island
        * l_gap: '10um' -- The dielectric gap of the charge island to ground
        * a_height: '60um' -- The length of the arms forming the 'fingers' of the charge island
        * cp_height: '15um' -- The thickness (y-axis) of the connection claw
        * cp_arm_length: '30um' -- The length of the 'fingers' of the connection claw (Warning: can break
          the component if they are too long)
        * cp_arm_width: '6um' -- The width of the 'fingers' of the connection claw (Warning: can break
          the component if too wide)
        * cp_gap: '6um' -- The dielectric gap of the connection claw
        * cp_gspace: '3um' -- How much ground remains between the connection claw and the charge island
        * fl_width: '5um' -- Width of the flux line
        * fl_gap: '3um' -- Dielectric gap of the flux line
        * fl_length: '10um' -- Length of the flux line for mutual inductance to the SQUID
        * fl_ground: '2um' -- Amount of ground between the SQUID and the flux line
        * _default_connection_pads: Currently empty
    """

    default_options = Dict(c_width='400um',
                           l_width='20um',
                           l_gap='10um',
                           a_height='60um',
                           cp_height='15um',
                           cp_arm_length='30um',
                           cp_arm_width='6um',
                           cp_gap='6um',
                           cp_gspace='3um',
                           fl_width='5um',
                           fl_gap='3um',
                           fl_length='10um',
                           fl_ground='2um')

    component_metadata = Dict(short_name='Pocket',
                              _qgeometry_table_path='True',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='True')

    TOOLTIP = """One of the tunable couplers"""

    def make(self):
        """Builds the component."""
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

        left_side = draw.shapely.ops.unary_union([btm, arm1, arm2, arm3])
        cap_island = draw.shapely.ops.unary_union([
            left_side,
            draw.shapely.affinity.scale(left_side,
                                        xfact=-1,
                                        yfact=1,
                                        origin=(0, 0))
        ])

        cap_subtract = cap_island.buffer(p.l_gap, cap_style=3, join_style=2)

        #Reference coordinates
        cpl_x = 1 / 5 * x_spot
        cpl_y = p.a_height + p.l_gap + p.cp_gap + p.cp_gspace
        fl_y = p.a_height + p.l_gap + p.fl_ground + p.fl_gap + p.fl_width / 2

        #Draw the junction and flux line
        rect_jj = draw.LineString([(-cpl_x * 3, p.a_height),
                                   (-cpl_x * 3, p.a_height + p.l_gap)])

        flux_line = draw.LineString([[-cpl_x * 3 - p.fl_length, fl_y],
                                     [-cpl_x * 3, fl_y],
                                     [-cpl_x * 3, fl_y + 0.01]])

        #Draw the connector
        cpl_x = 1 / 5 * x_spot
        cpl_y = p.a_height + p.l_gap + p.cp_gap + p.cp_gspace

        con_pad = draw.shapely.geometry.box(
            cpl_x - 1 / 5 * x_spot - p.cp_arm_width / 2, cpl_y,
            cpl_x + 1 / 5 * x_spot + p.cp_arm_width / 2, cpl_y + p.cp_height)

        con_arm_l = draw.shapely.geometry.box(
            cpl_x - 1 / 5 * x_spot - p.cp_arm_width / 2,
            cpl_y - p.cp_arm_length,
            cpl_x - 1 / 5 * x_spot + p.cp_arm_width / 2, cpl_y)

        con_arm_r = draw.shapely.geometry.box(
            cpl_x + 1 / 5 * x_spot - p.cp_arm_width / 2,
            cpl_y - p.cp_arm_length,
            cpl_x + 1 / 5 * x_spot + p.cp_arm_width / 2, cpl_y)

        con_body = draw.shapely.ops.unary_union([con_pad, con_arm_l, con_arm_r])

        con_sub = con_body.buffer(p.cp_gap, cap_style=3, join_style=2)

        con_pin = draw.LineString([[cpl_x, cpl_y], [cpl_x,
                                                    cpl_y + p.cp_height]])

        #Rotate and translate.
        c_items = [
            cap_island, cap_subtract, rect_jj, con_body, con_sub, flux_line,
            con_pin
        ]
        c_items = draw.rotate(c_items, p.orientation, origin=(0, 0))
        c_items = draw.translate(c_items, p.pos_x, p.pos_y)
        [
            cap_island, cap_subtract, rect_jj, con_body, con_sub, flux_line,
            con_pin
        ] = c_items

        #Add to qgeometry
        self.add_qgeometry('poly', {
            'cap_island': cap_island,
            'connector_body': con_body
        },
                           layer=p.layer)
        self.add_qgeometry('poly', {
            'cap_subtract': cap_subtract,
            'connector_sub': con_sub
        },
                           layer=p.layer,
                           subtract=True)

        self.add_qgeometry('path', {'flux_line': flux_line},
                           width=p.fl_width,
                           layer=p.layer)
        self.add_qgeometry('path', {'flux_line_sub': flux_line},
                           width=p.fl_width + 2 * p.fl_gap,
                           subtract=True,
                           layer=p.layer)

        self.add_qgeometry('junction', dict(rect_jj=rect_jj), width=p.l_width)

        #Add pin
        self.add_pin('Control',
                     points=np.array(con_pin.coords),
                     width=p.l_width,
                     input_as_norm=True)
        self.add_pin('Flux',
                     points=np.array(flux_line.coords[-2:]),
                     width=p.l_width,
                     input_as_norm=True)
