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
"""Concentric Transmon, as shown in Phys. Rev. Appl. 10, 034050 (2018).
"""
from math import sin, cos
import numpy as np
from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import BaseQubit


class TransmonConcentricType2(BaseQubit):
    """The base `TrasmonConcentric` class
    Inherits `BaseQubit` class.
    Metal transmon object consisting of a circle surrounding by a concentric
    ring. There are two Josephson Junction connecting the circle to the ring;
    one at the south end and one at the north end. There is a readout resonator.

    .. image::
        transmon_concentric_type_2.png

    .. meta::
        Transmon Concentric Type 2

    BaseQubit Default Options:
        * connection_pads: empty Dict -- the dictionary which contains all active
          connection lines for the qubit.
        * _default_connection_pads: empty Dict -- the default values for the
          (if any) connection lines of the qubit.
    Default Options:
        * width: '1000um' -- Width of transmon pocket
        * height: '1000um' -- Height of transmon pocket
        * rad_o: '170um' -- Outer radius
        * rad_i: '115um' -- Inner radius
        * gap: '35um' -- Radius of gap between two pads
        * jj_w: '10um' -- Josephson Junction width
        * res_s: '100um' -- Space between top electrode and readout resonator
        * res_ext: '100um' -- Extension of readout resonator in x-direction
          beyond midpoint of transmon
        * fbl_rad: '100um' -- Radius of the flux bias line loop
        * fbl_sp: '100um' -- Spacing between metal pad and flux bias loop
        * fbl_gap: '80um' -- Space between parallel lines of the flux bias loop
        * fbl_ext: '300um' -- Run length of flux bias line between circular
          loop and edge of pocket
        * pocket_w: '1500um' -- Transmon pocket width
        * pocket_h: '1000um' -- Transmon pocket height
        * cpw_width: '10.0um' -- Width of the readout resonator and flux bias line
        * layer: '1' -- default layer
    """

    # default drawing options
    default_options = Dict(pos_x='0mm',
                           pos_y='0mm',
                           orientation='0',
                           rad_outer='2mm',
                           rad_inner='1mm',
                           gap='0.5mm',
                           jj_w='0.2mm',
                           finger_NE_width='0.1mm',
                           finger_NE_length='0.5mm',
                           coupler_NE_width='0.1mm',
                           coupler_NE_gap='0.1mm',
                           finger_NW_width='0.1mm',
                           finger_NW_length='0.5mm',
                           coupler_NW_width='0.1mm',
                           coupler_NW_gap='0.1mm',
                           finger_SW_width='0.1mm',
                           finger_SW_length='0.5mm',
                           coupler_SW_width='0.1mm',
                           coupler_SW_gap='0.1mm',
                           finger_E_width='0.1mm',
                           finger_E_length='0.5mm',
                           box_E_width='0.7mm',
                           box_E_length='0.7mm',
                           finger_N_width='0.1mm',
                           finger_N_length='2mm',
                           triangle_base='2mm',
                           triangle_height='1mm',
                           pocket_w='10mm',
                           pocket_h='10mm',
                           layer='1')
    """Default drawing options"""

    def make(self):
        """Convert self.options into QGeometry."""
        p = self.parse_options()  # Parse the string options into numbers
        # draw the concentric pad regions
        outer_pad = draw.Point(0, 0).buffer(p.rad_outer)
        space = draw.Point(0, 0).buffer((p.gap + p.rad_inner))
        cutout = draw.rectangle(8.0 * p.finger_N_width, p.finger_N_length, 0.0,
                                p.rad_inner + 0.5 * p.finger_N_length)
        outer_pad = draw.subtract(outer_pad, space)
        outer_pad = draw.subtract(outer_pad, cutout)
        inner_pad = draw.Point(0, 0).buffer(p.rad_inner)
        # draw the Josephson Junction
        JJ = draw.LineString([
            (p.rad_inner * cos(45 * 3.14159 / 180),
             -1.0 * p.rad_inner * sin(45 * 3.14159 / 180)),
            ((p.rad_inner + p.gap) * cos(45 * 3.14159 / 180),
             -1.0 * (p.rad_inner + p.gap) * sin(45 * 3.14159 / 180))
        ])
        # draw the northeast finger
        finger_NE = draw.LineString([
            (p.rad_outer * cos(45 * 3.14159 / 180),
             p.rad_outer * sin(45 * 3.14159 / 180)),
            ((p.rad_outer + p.finger_NE_length) * cos(45 * 3.14159 / 180),
             (p.rad_outer + p.finger_NE_length) * sin(45 * 3.14159 / 180))
        ])
        # draw the coupling resonator to the northeast finger
        r = (p.rad_outer + 0.5 * p.finger_NE_length + 0.5 *
             (0.5 * p.finger_NE_length + p.coupler_NE_gap + p.coupler_NE_width))
        coupler_NE = draw.rectangle(
            2.0 * p.coupler_NE_width + p.finger_NE_width + 2 * p.coupler_NE_gap,
            0.5 * p.finger_NE_length + p.coupler_NE_gap + p.coupler_NE_width,
            r * cos(45 * 3.14159 / 180), r * sin(45 * 3.14159 / 180))
        coupler_NE = draw.rotate(coupler_NE,
                                 -45,
                                 origin=(r * cos(45 * 3.14159 / 180),
                                         r * sin(45 * 3.14159 / 180)))
        l = p.rad_outer + 0.5 * p.finger_NE_length + 0.5 * (
            0.5 * p.finger_NE_length + p.coupler_NE_gap)
        coupler_NE_cut = draw.rectangle(
            p.finger_NE_width + 2.0 * p.coupler_NE_gap,
            0.5 * p.finger_NE_length + p.coupler_NE_gap +
            0.05 * p.finger_NE_length, l * cos(45 * 3.145159 / 180),
            l * sin(45 * 3.14159 / 180))
        coupler_NE_cut = draw.rotate(coupler_NE_cut,
                                     -45,
                                     origin=(l * cos(45 * 3.14159 / 180),
                                             l * sin(45 * 3.14159 / 180)))
        coupler_NE = draw.subtract(coupler_NE, coupler_NE_cut)
        # draw the northwest finger
        finger_NW = draw.LineString([
            (-1.0 * p.rad_outer * cos(45 * 3.14159 / 180),
             p.rad_outer * sin(45 * 3.14159 / 180)),
            (-1.0 * (p.rad_outer + p.finger_NW_length) *
             cos(45 * 3.14159 / 180),
             (p.rad_outer + p.finger_NW_length) * sin(45 * 3.14159 / 180))
        ])
        # draw the coupling resonator to the northwest finger
        r_nw = (
            p.rad_outer + 0.5 * p.finger_NW_length + 0.5 *
            (0.5 * p.finger_NW_length + p.coupler_NW_gap + p.coupler_NW_width))
        coupler_NW = draw.rectangle(
            2.0 * p.coupler_NW_width + p.finger_NW_width + 2 * p.coupler_NW_gap,
            0.5 * p.finger_NW_length + p.coupler_NW_gap + p.coupler_NW_width,
            -1.0 * r_nw * cos(45 * 3.14159 / 180),
            r_nw * sin(45 * 3.14159 / 180))
        coupler_NW = draw.rotate(coupler_NW,
                                 45,
                                 origin=(-1.0 * r_nw * cos(45 * 3.14159 / 180),
                                         r_nw * sin(45 * 3.14159 / 180)))
        l_nw = p.rad_outer + 0.5 * p.finger_NW_length + 0.5 * (
            0.5 * p.finger_NW_length + p.coupler_NW_gap)
        coupler_NW_cut = draw.rectangle(
            p.finger_NW_width + 2.0 * p.coupler_NW_gap,
            0.5 * p.finger_NW_length + p.coupler_NW_gap +
            0.05 * p.finger_NW_length, -1.0 * l_nw * cos(45 * 3.145159 / 180),
            l_nw * sin(45 * 3.14159 / 180))
        coupler_NW_cut = draw.rotate(
            coupler_NW_cut,
            45,
            origin=(-1.0 * l_nw * cos(45 * 3.14159 / 180),
                    l_nw * sin(45 * 3.14159 / 180)))
        coupler_NW = draw.subtract(coupler_NW, coupler_NW_cut)
        # draw the southwest finger
        finger_SW = draw.LineString([
            (-1.0 * p.rad_outer * cos(45 * 3.14159 / 180),
             -1.0 * p.rad_outer * sin(45 * 3.14159 / 180)),
            (-1.0 * (p.rad_outer + p.finger_SW_length) *
             cos(45 * 3.14159 / 180), -1.0 *
             (p.rad_outer + p.finger_SW_length) * sin(45 * 3.14159 / 180))
        ])
        # draw the coupling resonator to the southwest finger
        r_sw = (
            p.rad_outer + 0.5 * p.finger_SW_length + 0.5 *
            (0.5 * p.finger_SW_length + p.coupler_SW_gap + p.coupler_SW_width))
        coupler_SW = draw.rectangle(
            2.0 * p.coupler_SW_width + p.finger_SW_width + 2 * p.coupler_SW_gap,
            0.5 * p.finger_SW_length + p.coupler_SW_gap + p.coupler_SW_width,
            -1.0 * r_sw * cos(45 * 3.14159 / 180),
            -1.0 * r_sw * sin(45 * 3.14159 / 180))
        coupler_SW = draw.rotate(coupler_SW,
                                 135,
                                 origin=(-1.0 * r_sw * cos(45 * 3.14159 / 180),
                                         -1.0 * r_sw * sin(45 * 3.14159 / 180)))
        l_sw = p.rad_outer + 0.5 * p.finger_SW_length + 0.5 * (
            0.5 * p.finger_SW_length + p.coupler_SW_gap)
        coupler_SW_cut = draw.rectangle(
            p.finger_SW_width + 2.0 * p.coupler_SW_gap,
            0.5 * p.finger_SW_length + p.coupler_SW_gap +
            0.05 * p.finger_SW_length, -1.0 * l_sw * cos(45 * 3.145159 / 180),
            -1.0 * l_sw * sin(45 * 3.14159 / 180))
        coupler_SW_cut = draw.rotate(
            coupler_SW_cut,
            135,
            origin=(-1.0 * l_sw * cos(45 * 3.14159 / 180),
                    -1.0 * l_sw * sin(45 * 3.14159 / 180)))
        coupler_SW = draw.subtract(coupler_SW, coupler_SW_cut)
        # draw the east finger with the rectangular coupling pad
        finger_E = draw.LineString([(-1.0 * p.rad_outer, 0.0),
                                    (-1.0 * (p.rad_outer + p.finger_E_length),
                                     0.0)])
        box = draw.rectangle(
            p.box_E_width, p.box_E_length,
            -1.0 * (p.rad_outer + p.finger_E_length + 0.5 * p.box_E_width), 0.0)
        # draw the north finger with the triangular coupling pad
        finger_N = draw.LineString([(0.0, p.rad_inner),
                                    (0.0, p.rad_inner + p.finger_N_length)])
        # draw the top triangular coupling pad
        padtop_i = draw.rectangle(
            p.triangle_base, p.triangle_height, 0.0,
            p.rad_inner + p.finger_N_length + 0.5 * p.triangle_height)
        cut1 = draw.rotate(padtop_i,
                           45,
                           origin=(0.5 * p.triangle_base, p.rad_inner +
                                   p.finger_N_length + p.triangle_height))
        padtop = draw.subtract(padtop_i, cut1)
        cut2 = draw.rotate(padtop_i,
                           315,
                           origin=(-0.5 * p.triangle_base, p.rad_inner +
                                   p.finger_N_length + p.triangle_height))
        padtop = draw.subtract(padtop, cut2)
        padtop = draw.translate(padtop, 0.0, -.05 * p.triangle_height)
        # draw the transmon pocket bounding box
        # pocket = draw.rectangle(p.pocket_w, p.pocket_h)
        # Translate and rotate all shapes
        objects = [
            outer_pad, inner_pad, JJ, finger_NE, finger_NW, finger_SW, finger_E,
            box, finger_N, padtop, coupler_NE, coupler_NW, coupler_SW
        ]
        objects = draw.rotate(objects, p.orientation, origin=(0, 0))
        objects = draw.translate(objects, xoff=p.pos_x, yoff=p.pos_y)
        [
            outer_pad, inner_pad, JJ, finger_NE, finger_NW, finger_SW, finger_E,
            box, finger_N, padtop, coupler_NE, coupler_NW, coupler_SW
        ] = objects
        ##############################################################
        # Use the geometry to create Metal QGeometry
        geom_outer = {'poly1': outer_pad}
        geom_inner = {'poly2': inner_pad}
        geom_jj = {'poly3': JJ}
        geom_finger_NE = {'finger_NE': finger_NE}
        geom_finger_NW = {'finger_NW': finger_NW}
        geom_finger_SW = {'finger_SW': finger_SW}
        geom_finger_E = {'finger_E': finger_E}
        geom_box_E = {'box_E': box}
        geom_finger_N = {'finger_N': finger_N}
        geom_pad_top = {'pad_top': padtop}
        geom_coupler_NE = {'coupler_NE': coupler_NE}
        geom_coupler_NW = {'coupler_NW': coupler_NW}
        geom_coupler_SW = {'coupler_SW': coupler_SW}
        self.add_qgeometry('poly', geom_outer, layer=p.layer, subtract=False)
        self.add_qgeometry('poly', geom_inner, layer=p.layer, subtract=False)
        self.add_qgeometry('junction',
                           geom_jj,
                           layer=p.layer,
                           subtract=False,
                           width=p.jj_w)
        self.add_qgeometry('path',
                           geom_finger_NE,
                           layer=p.layer,
                           subtract=False,
                           width=p.finger_NE_width)
        self.add_qgeometry('path',
                           geom_finger_NW,
                           layer=p.layer,
                           subtract=False,
                           width=p.finger_NW_width)
        self.add_qgeometry('path',
                           geom_finger_SW,
                           layer=p.layer,
                           subtract=False,
                           width=p.finger_SW_width)
        self.add_qgeometry('path',
                           geom_finger_E,
                           layer=p.layer,
                           subtract=False,
                           width=p.finger_E_width)
        self.add_qgeometry('poly', geom_box_E, layer=p.layer, subtract=False)
        self.add_qgeometry('path',
                           geom_finger_N,
                           layer=p.layer,
                           subtract=False,
                           width=p.finger_N_width)
        self.add_qgeometry('poly', geom_pad_top, layer=p.layer, subtract=False)
        self.add_qgeometry('poly',
                           geom_coupler_NE,
                           layer=p.layer,
                           subtract=False)
        self.add_qgeometry('poly',
                           geom_coupler_NW,
                           layer=p.layer,
                           subtract=False)
        self.add_qgeometry('poly',
                           geom_coupler_SW,
                           layer=p.layer,
                           subtract=False)

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

        # Northeast coupler
        qp1a_r = p.rad_outer + p.finger_NE_length + p.coupler_NE_gap
        qp1a = (qp1a_r * cos(45 * 3.14159 / 180),
                qp1a_r * sin(45 * 3.14159 / 180))
        qp1b_r = p.rad_outer + p.finger_NE_length + p.coupler_NE_gap + p.coupler_NE_width
        qp1b = (qp1b_r * cos(45 * 3.14159 / 180),
                qp1b_r * sin(45 * 3.14159 / 180))
        qp1a = qpin_rotate_translate(qp1a)
        qp1b = qpin_rotate_translate(qp1b)
        self.add_pin('pin1',
                     points=np.array([qp1a, qp1b]),
                     width=0.01,
                     input_as_norm=True)
        # Northwest coupler
        qp2a_r = p.rad_outer + p.finger_NW_length + p.coupler_NW_gap
        qp2a = (-1.0 * qp2a_r * cos(45 * 3.14159 / 180),
                qp2a_r * sin(45 * 3.14159 / 180))
        qp2b_r = p.rad_outer + p.finger_NW_length + p.coupler_NW_gap + p.coupler_NW_width
        qp2b = (-1.0 * qp2b_r * cos(45 * 3.14159 / 180),
                qp2b_r * sin(45 * 3.14159 / 180))
        qp2a = qpin_rotate_translate(qp2a)
        qp2b = qpin_rotate_translate(qp2b)
        self.add_pin('pin2',
                     points=np.array([qp2a, qp2b]),
                     width=0.01,
                     input_as_norm=True)
        # Southwest coupler
        qp3a_r = p.rad_outer + p.finger_SW_length + p.coupler_SW_gap
        qp3a = (-1.0 * qp3a_r * cos(45 * 3.14159 / 180),
                -1.0 * qp3a_r * sin(45 * 3.14159 / 180))
        qp3b_r = p.rad_outer + p.finger_SW_length + p.coupler_SW_gap + p.coupler_SW_width
        qp3b = (-1.0 * qp3b_r * cos(45 * 3.14159 / 180),
                -1.0 * qp3b_r * sin(45 * 3.14159 / 180))
        qp3a = qpin_rotate_translate(qp3a)
        qp3b = qpin_rotate_translate(qp3b)
        self.add_pin('pin3',
                     points=np.array([qp3a, qp3b]),
                     width=0.01,
                     input_as_norm=True)
