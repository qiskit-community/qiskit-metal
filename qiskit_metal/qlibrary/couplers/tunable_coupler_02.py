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
"""Tunable Coupler, as shown in Phys. Rev. Research 2, 033447 (2020).
"""

from math import sin, cos
import numpy as np
from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import BaseQubit


class TunableCoupler02(BaseQubit):
    """One of the tunable couplers

    .. image::
        tunable_coupler_02.png

    .. meta::
        Tunable Coupler 2

    BaseQubit Default Options:
        * connection_pads: empty Dict -- Currently not used, connection count is static. (WIP)
    Default Options:
        * pocket_width: '3mm' -- The width (x-axis) of the transmon pocket
        * pocket_height: '2m' -- The height (y-axis) of the transmon pocket
        * pos_x: '0mm' -- the x-coordinate location of the JJ in the middle of the qubit
        * pos_y: '0mm' -- the y-coordinate location of the JJ in the middle of the qubit
        * orientation: '0' -- the angle of rotation
        * pad_radius: '0.3mm' -- the radius of the two circular pads on either side of the JJ
        * bus_width: '0.1mm' -- the width of the CPW resonator in the coupler
        * bus_inner_length: '0.5mm' -- length of the CPW between the JJ and the circular pad
        * bus_outer_length: '0.5mm' -- length of the CPW between the circular pad and the in/out pin
        * bus_JJ_height: '0.5mm' -- vertical distance between the main cpw line and the offset JJ
        * JJ_width: '0.1mm' -- the width of the JJ
        * JJ_length: '0.4mm' -- the length of the JJ
        * fbl_width: '0.1mm' -- the width of the flux bias line drawn near the JJ
        * fbl_length: '0.5mm' -- the length of the flux bias line drawn near the JJ
        * fbl_offset: '0.1mm' -- the lateral offset between the flux bias line and the JJ
        * layer: '1' -- the default design layer
    """

    default_options = Dict(pocket_width='3mm',
                           pocket_height='2mm',
                           pos_x='0mm',
                           pos_y='0mm',
                           orientation='0',
                           pad_radius='0.3mm',
                           bus_width='0.1mm',
                           bus_inner_length='0.5mm',
                           bus_outer_length='0.5mm',
                           bus_JJ_height='0.5mm',
                           JJ_width='0.1mm',
                           JJ_length='0.4mm',
                           fbl_width='0.1mm',
                           fbl_length='0.5mm',
                           fbl_offset='0.1mm',
                           layer='1')

    component_metadata = Dict(short_name='Pocket',
                              _qgeometry_table_path='True',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='True')

    TOOLTIP = """One of the tunable couplers"""

    def make(self):
        """Builds the component."""
        """Convert self.options into QGeometry."""
        p = self.parse_options()  # Parse the string options into numbers
        # draw the Josephson Junction
        JJ = draw.LineString([
            (-0.5 * p.JJ_length, p.bus_JJ_height - 0.5 * p.JJ_width),
            (0.5 * p.JJ_length, p.bus_JJ_height - 0.5 * p.JJ_width)
        ])
        # draw the individual components of the CPW resonator
        bus_vertical_left = draw.rectangle(
            p.bus_width, p.bus_JJ_height,
            -0.5 * p.JJ_length - 0.5 * p.bus_width, 0.5 * p.bus_JJ_height)
        bus_vertical_right = draw.rectangle(
            p.bus_width, p.bus_JJ_height, 0.5 * p.JJ_length + 0.5 * p.bus_width,
            0.5 * p.bus_JJ_height)
        bus_left = draw.rectangle(
            p.bus_inner_length + p.bus_outer_length + 2.0 * p.pad_radius,
            p.bus_width, -0.5 * p.JJ_length - p.bus_width - 0.5 *
            (p.bus_inner_length + p.bus_outer_length + 2.0 * p.pad_radius),
            0.5 * p.bus_width)
        bus_right = draw.rectangle(
            p.bus_inner_length + p.bus_outer_length + 2.0 * p.pad_radius,
            p.bus_width, 0.5 * p.JJ_length + p.bus_width + 0.5 *
            (p.bus_inner_length + p.bus_outer_length + 2.0 * p.pad_radius),
            0.5 * p.bus_width)
        # draw the circular charge pads
        left_pad = draw.Point(
            -0.5 * p.JJ_length - p.bus_width - p.bus_inner_length -
            0.5 * p.pad_radius, 0.5 * p.bus_width).buffer(p.pad_radius)
        right_pad = draw.Point(
            0.5 * p.JJ_length + p.bus_width + p.bus_inner_length +
            0.5 * p.pad_radius, 0.5 * p.bus_width).buffer(p.pad_radius)
        # draw the flux bias line
        fbl = draw.rectangle(
            p.fbl_width, p.fbl_length,
            -0.5 * p.JJ_length - p.bus_width - p.fbl_offset - 0.5 * p.fbl_width,
            p.bus_JJ_height + 0.5 * p.fbl_length)
        # draw the pocket surrounding the qubit
        pocket = draw.rectangle(0.0, 0.0, p.pocket_width, p.pocket_height)
        # Translate and rotate all shapes
        objects = [
            JJ, bus_vertical_left, bus_vertical_right, bus_left, bus_right,
            left_pad, right_pad, fbl, pocket
        ]
        objects = draw.rotate(objects, p.orientation, origin=(0, 0))
        objects = draw.translate(objects, xoff=p.pos_x, yoff=p.pos_y)
        [
            JJ, bus_vertical_left, bus_vertical_right, bus_left, bus_right,
            left_pad, right_pad, fbl, pocket
        ] = objects
        # give each poly a name to send to qgeometry
        geom_jj = {'poly1': JJ}
        geom_bus_vertical_left = {'poly2': bus_vertical_left}
        geom_bus_vertical_right = {'poly3': bus_vertical_right}
        geom_bus_left = {'poly4': bus_left}
        geom_bus_right = {'poly5': bus_right}
        geom_left_pad = {'poly6': left_pad}
        geom_right_pad = {'poly7': right_pad}
        geom_fbl = {'poly8': fbl}
        #geom_pocket = {'poly9': pocket}
        # add to qgeometry
        self.add_qgeometry('junction',
                           geom_jj,
                           layer=p.layer,
                           subtract=False,
                           width=p.JJ_width)
        self.add_qgeometry('poly',
                           geom_bus_vertical_left,
                           layer=p.layer,
                           subtract=False)
        self.add_qgeometry('poly',
                           geom_bus_vertical_right,
                           layer=p.layer,
                           subtract=False)
        self.add_qgeometry('poly', geom_bus_left, layer=p.layer, subtract=False)
        self.add_qgeometry('poly',
                           geom_bus_right,
                           layer=p.layer,
                           subtract=False)
        self.add_qgeometry('poly', geom_left_pad, layer=p.layer, subtract=False)
        self.add_qgeometry('poly',
                           geom_right_pad,
                           layer=p.layer,
                           subtract=False)
        self.add_qgeometry('poly', geom_fbl, layer=p.layer, subtract=False)

        #self.add_qgeometry('poly', geom_pocket, layer=1, subtract=True)
        ###########################################################################
        # Add Qpin connections
        # define a function that both rotates and translates the qpin coordinates
        def qpin_rotate_translate(x):
            y = list(x)
            z = [0.0, 0.0]
            z[0] = y[0] * cos(p.orientation * 3.14159 / 180) - y[1] * sin(
                p.orientation * 3.14159 / 180)
            z[1] = y[0] * sin(p.orientation * 3.14159 / 180) + y[1] * cos(
                p.orientation * 3.14159 / 180)
            z[0] = z[0] + p.pos_x
            z[1] = z[1] + p.pos_y
            x = (z[0], z[1])
            return x

        # Right-hand pin
        qp1b = (0.5 * p.JJ_length + p.bus_width + p.bus_inner_length +
                p.bus_outer_length + 2.0 * p.pad_radius, 0.5 * p.bus_width)
        qp1a = (0.5 * p.JJ_length + p.bus_width + 0.9 * p.bus_inner_length +
                p.bus_outer_length + 2.0 * p.pad_radius, 0.5 * p.bus_width)
        qp1a = qpin_rotate_translate(qp1a)
        qp1b = qpin_rotate_translate(qp1b)
        self.add_pin('pin1',
                     points=np.array([qp1a, qp1b]),
                     width=0.01,
                     input_as_norm=True)
        # Left-hand pin
        qp2b = (-0.5 * p.JJ_length - p.bus_width - p.bus_inner_length -
                p.bus_outer_length - 2.0 * p.pad_radius, 0.5 * p.bus_width)
        qp2a = (-0.5 * p.JJ_length - p.bus_width - 0.9 * p.bus_inner_length -
                p.bus_outer_length - 2.0 * p.pad_radius, 0.5 * p.bus_width)
        qp2a = qpin_rotate_translate(qp2a)
        qp2b = qpin_rotate_translate(qp2b)
        self.add_pin('pin2',
                     points=np.array([qp2a, qp2b]),
                     width=0.01,
                     input_as_norm=True)
        # Flux Bias Line pin
        qp3b = (-0.5 * p.JJ_length - p.bus_width - p.fbl_offset -
                0.5 * p.fbl_width, p.bus_JJ_height + p.fbl_length)
        qp3a = (-0.5 * p.JJ_length - p.bus_width - p.fbl_offset -
                0.5 * p.fbl_width, p.bus_JJ_height + 0.9 * p.fbl_length)
        qp3a = qpin_rotate_translate(qp3a)
        qp3b = qpin_rotate_translate(qp3b)
        self.add_pin('fbl',
                     points=np.array([qp3a, qp3b]),
                     width=0.01,
                     input_as_norm=True)
