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
"""Lumped Resonator, as shown in Phys. Rev. Appl. 10, 034050 (2018).
"""
from math import sin, cos
import numpy as np
from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import QComponent


class ResonatorLumped(QComponent):
    '''
    The base ResonatorLumped class
    Inherits the QComponent class

    .. image::
        resonator_lumped.png

    .. meta::
        Lumped Resonator

    Default Options:
        * pos_x: '0um' -- x-coordinate of the bottom center of the resonator
        * pos_y: '0um' -- y-coordinate of the bottom center of the resonator
        * orientation: '0' -- angle of rotation of the resonator
        * box_width: '5mm' -- the width of the rectangular resonator structure
        * box_height: '5mm' -- the height of the rectangular resonator structure
        * perimeter_thicknes: '0.01mm' -- the width of the resonator along the perimeter
        * res_width: '0.01m' -- the width of the resonator
        * initial: '0.1m' -- the length of the lower straight resonator segment
        * n_turns: '10' -- the number of turns in the curved resonator segment
        * turn_radius: '0.1mm' - the radius of the turns in the curved resonator segment
        * inner_space: '0.1mm' - the space between the curved resonator
        * outer_space: '0.1mm' -- the space between rectangular and curved resonator turns
        * final: '2.5mm' -- the length of the upper straight segment of the resonator
        * break_width: '0.2mm' -- the width of the "break" in the top of the rectangular resonator
        * layer: '1' -- the layer of the component
    '''

    default_options = Dict(
        pos_x='0 um',
        pos_y='0 um',
        orientation='0',
        box_width='5mm',
        box_height='5mm',
        perimeter_thickness='0.01mm',
        res_width='0.01mm',
        initial='0.1mm',
        n_turns='10',
        turn_radius='0.1mm',
        inner_space='0.1mm',
        outer_space='0.1mm',
        final='2.5mm',
        break_width='0.2mm',
        layer='1',
    )

    ##########################
    def make(self):
        """Builds the component."""
        """Convert self.options into QGeometry."""
        p = self.parse_options()  # Parse the string options into numbers

        # draw the perimeter
        box_out = draw.rectangle(p.box_width, p.box_height, 0.0, 0.0)
        box_in = draw.rectangle(p.box_width - 2.0 * p.perimeter_thickness,
                                p.box_height - 2.0 * p.perimeter_thickness, 0.0,
                                0.0)
        perimeter = draw.subtract(box_out, box_in)
        perimeter = draw.translate(perimeter, xoff=0.0, yoff=0.5 * p.box_height)
        break_rect = draw.rectangle(p.break_width, p.break_width, 0.0,
                                    p.box_height)
        perimeter = draw.subtract(perimeter, break_rect)
        # start the resonator
        initial = draw.LineString([(0.0, p.perimeter_thickness),
                                   (0.0, p.perimeter_thickness + p.initial)])
        # Draw the first quarter turn
        centerx, centery = -1.0 * p.turn_radius, p.perimeter_thickness + p.initial
        radius = p.turn_radius
        start_angle, end_angle = 0, 90  # In degrees
        numsegments = 1000
        # The coordinates of the arc
        theta = np.radians(np.linspace(start_angle, end_angle, numsegments))
        x = centerx + radius * np.cos(theta)
        y = centery + radius * np.sin(theta)
        arc = draw.LineString(np.column_stack([x, y]))
        # Draw the first half-turn (left); this gets repeated
        centerx2 = -0.5 * p.box_width + p.outer_space + p.turn_radius
        centery2 = p.perimeter_thickness + p.initial + 2.0 * p.turn_radius
        radius2 = p.turn_radius
        start_angle2, end_angle2 = 270, 90  # In degrees
        numsegments2 = 1000
        # The coordinates of the arc
        theta2 = np.radians(np.linspace(start_angle2, end_angle2, numsegments2))
        x2 = centerx2 + radius2 * np.cos(theta2)
        y2 = centery2 + radius2 * np.sin(theta2)
        arc_left_1 = draw.LineString(np.column_stack([x2, y2]))
        # Draw the first half-turn (right); this gets repeated
        centerx3 = 0.5 * p.box_width - p.outer_space - p.turn_radius
        centery3 = p.perimeter_thickness + p.initial + 4.0 * p.turn_radius
        radius3 = p.turn_radius
        start_angle3, end_angle3 = 90, -90  # In degrees
        numsegments3 = 1000
        # The coordinates of the arc
        theta3 = np.radians(np.linspace(start_angle3, end_angle3, numsegments3))
        x3 = centerx3 + radius3 * np.cos(theta3)
        y3 = centery3 + radius3 * np.sin(theta3)
        arc_right_1 = draw.LineString(np.column_stack([x3, y3]))
        # bottom half-line
        line1 = draw.LineString([
            (-1.0 * p.turn_radius - 0.0 * p.res_width,
             p.perimeter_thickness + p.initial + p.turn_radius),
            (-0.5 * p.box_width + p.outer_space + p.turn_radius,
             p.perimeter_thickness + p.initial + p.turn_radius)
        ])
        # bottom full-line (this one gets repeated)
        line2 = draw.LineString([
            (-0.5 * p.box_width + p.outer_space + p.turn_radius,
             p.initial + 3.0 * p.turn_radius + p.res_width),
            (0.5 * p.box_width - p.outer_space - p.turn_radius,
             p.initial + 3.0 * p.turn_radius + p.res_width)
        ])
        # repeat the full fline
        line3 = draw.translate(line2, 0.0, 2.0 * p.turn_radius)
        line4 = draw.translate(line3, 0.0, 2.0 * p.turn_radius)
        line5 = draw.translate(line4, 0.0, 2.0 * p.turn_radius)
        line6 = draw.translate(line5, 0.0, 2.0 * p.turn_radius)
        line7 = draw.translate(line6, 0.0, 2.0 * p.turn_radius)
        line8 = draw.translate(line7, 0.0, 2.0 * p.turn_radius)
        line9 = draw.translate(line8, 0.0, 2.0 * p.turn_radius)
        line10 = draw.translate(line9, 0.0, 2.0 * p.turn_radius)
        line11 = draw.translate(line10, 0.0, 2.0 * p.turn_radius)
        line12 = draw.translate(line11, 0.0, 2.0 * p.turn_radius)
        line13 = draw.translate(line12, 0.0, 2.0 * p.turn_radius)
        line14 = draw.translate(line13, 0.0, 2.0 * p.turn_radius)
        # hard code the position for now; make it adjustable later
        line_last = draw.translate(
            line1, 0.5 * p.box_width - 0.0 * p.turn_radius - p.outer_space,
            28 * p.turn_radius)
        # draw the line exiting the rectangle
        final = draw.LineString([
            (0.0, p.perimeter_thickness + p.initial + 30.0 * p.turn_radius),
            (0.0,
             p.perimeter_thickness + p.initial + 30.0 * p.turn_radius + p.final)
        ])
        arc_last = draw.rotate(arc,
                               180,
                               origin=(0.0, p.perimeter_thickness + p.initial +
                                       1.5 * p.turn_radius))
        arc_last = draw.translate(arc_last, 0.0, p.initial + 26 * p.turn_radius)
        # repeat the left turns
        arc_left_2 = draw.translate(arc_left_1, 0.0, 4.0 * p.turn_radius)
        arc_left_3 = draw.translate(arc_left_2, 0.0, 4.0 * p.turn_radius)
        arc_left_4 = draw.translate(arc_left_3, 0.0, 4.0 * p.turn_radius)
        arc_left_5 = draw.translate(arc_left_4, 0.0, 4.0 * p.turn_radius)
        arc_left_6 = draw.translate(arc_left_5, 0.0, 4.0 * p.turn_radius)
        arc_left_7 = draw.translate(arc_left_6, 0.0, 4.0 * p.turn_radius)
        # repeat the right turns
        arc_right_2 = draw.translate(arc_right_1, 0.0, 4.0 * p.turn_radius)
        arc_right_3 = draw.translate(arc_right_2, 0.0, 4.0 * p.turn_radius)
        arc_right_4 = draw.translate(arc_right_3, 0.0, 4.0 * p.turn_radius)
        arc_right_5 = draw.translate(arc_right_4, 0.0, 4.0 * p.turn_radius)
        arc_right_6 = draw.translate(arc_right_5, 0.0, 4.0 * p.turn_radius)
        arc_right_7 = draw.translate(arc_right_6, 0.0, 4.0 * p.turn_radius)
        # Translate and rotate all shapes
        objects = [
            perimeter, initial, arc, arc_left_1, arc_left_2, arc_left_3,
            arc_left_4, arc_left_5, arc_left_6, arc_left_7, arc_right_1,
            arc_right_2, arc_right_2, arc_right_3, arc_right_4, arc_right_4,
            arc_right_5, arc_right_6, arc_right_7, arc_last, final, line1,
            line2, line3, line4, line5, line6, line7, line8, line9, line10,
            line11, line12, line13, line14, line_last
        ]
        # first translate so that the origin is at the middle of the loop
        objects = draw.translate(objects, 0.0, -0.5 * p.box_height)
        # now translate and rotate according to the values specified in the dictionary
        objects = draw.rotate(objects, p.orientation, origin=(0, 0))
        objects = draw.translate(objects, xoff=p.pos_x, yoff=p.pos_y)
        [
            perimeter, initial, arc, arc_left_1, arc_left_2, arc_left_3,
            arc_left_4, arc_left_5, arc_left_6, arc_left_7, arc_right_1,
            arc_right_2, arc_right_2, arc_right_3, arc_right_4, arc_right_4,
            arc_right_5, arc_right_6, arc_right_7, arc_last, final, line1,
            line2, line3, line4, line5, line6, line7, line8, line9, line10,
            line11, line12, line13, line14, line_last
        ] = objects
        # give polys names for qgeometry
        geom_perimeter = {'poly1': perimeter}
        geom_initial = {'poly2': initial}
        geom_arc = {'poly3': arc}
        geom_arc_left_1 = {'poly4': arc_left_1}
        geom_arc_left_2 = {'poly4': arc_left_2}
        geom_arc_left_3 = {'poly4': arc_left_3}
        geom_arc_left_4 = {'poly4': arc_left_4}
        geom_arc_left_5 = {'poly4': arc_left_5}
        geom_arc_left_6 = {'poly4': arc_left_6}
        geom_arc_left_7 = {'poly4': arc_left_7}
        geom_arc_right_1 = {'poly4': arc_right_1}
        geom_arc_right_2 = {'poly4': arc_right_2}
        geom_arc_right_3 = {'poly4': arc_right_3}
        geom_arc_right_4 = {'poly4': arc_right_4}
        geom_arc_right_5 = {'poly4': arc_right_5}
        geom_arc_right_6 = {'poly4': arc_right_6}
        geom_arc_right_7 = {'poly4': arc_right_7}
        geom_arc_last = {'poly4': arc_last}
        geom_final = {'poly': final}
        geom_line1 = {'poly5': line1}
        geom_line2 = {'poly6': line2}
        geom_line3 = {'poly7': line3}
        geom_line4 = {'poly8': line4}
        geom_line5 = {'poly9': line5}
        geom_line6 = {'poly10': line6}
        geom_line7 = {'poly11': line7}
        geom_line8 = {'poly11': line8}
        geom_line9 = {'poly9': line9}
        geom_line10 = {'poly10': line10}
        geom_line11 = {'poly11': line11}
        geom_line12 = {'poly12': line12}
        geom_line13 = {'poly13': line13}
        geom_line14 = {'poly14': line14}
        geom_line_last = {'poly14': line_last}
        # add to qgeometry
        self.add_qgeometry('poly',
                           geom_perimeter,
                           layer=p.layer,
                           subtract=False)
        self.add_qgeometry('path',
                           geom_initial,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_arc,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_arc_left_1,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_arc_left_2,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_arc_left_3,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_arc_left_4,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_arc_left_5,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_arc_left_6,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_arc_left_7,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_arc_right_1,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_arc_right_2,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_arc_right_3,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_arc_right_4,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_arc_right_5,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_arc_right_6,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_arc_right_7,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_arc_last,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_line1,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_line2,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_line3,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_line4,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_line5,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_line6,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_line7,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_line8,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_line9,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_line10,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_line11,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_line12,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_line13,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_line14,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_line_last,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)
        self.add_qgeometry('path',
                           geom_final,
                           layer=p.layer,
                           subtract=False,
                           width=p.res_width)

        ##########################
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

        # East pin
        qp1a = (0.5 * p.box_width - p.perimeter_thickness, 0.0)
        qp1b = (0.5 * p.box_width, 0.0)
        qp1a = qpin_rotate_translate(qp1a)
        qp1b = qpin_rotate_translate(qp1b)
        self.add_pin('pin_east',
                     points=np.array([qp1a, qp1b]),
                     width=0.01,
                     input_as_norm=True)
        # North-East pin
        qpa_ne = (0.5 * p.box_width - p.perimeter_thickness,
                  0.5 * p.box_height - p.perimeter_thickness)
        qpb_ne = (0.5 * p.box_width, 0.5 * p.box_height)
        qpa_ne = qpin_rotate_translate(qpa_ne)
        qpb_ne = qpin_rotate_translate(qpb_ne)
        self.add_pin('pin_ne',
                     points=np.array([qpa_ne, qpb_ne]),
                     width=0.01,
                     input_as_norm=True)
        # South-East pin
        qpa_se = (0.5 * p.box_width - p.perimeter_thickness,
                  -0.5 * p.box_height + p.perimeter_thickness)
        qpb_se = (0.5 * p.box_width, -0.5 * p.box_height)
        qpa_se = qpin_rotate_translate(qpa_se)
        qpb_se = qpin_rotate_translate(qpb_se)
        self.add_pin('pin_se',
                     points=np.array([qpa_se, qpb_se]),
                     width=0.01,
                     input_as_norm=True)
        # North-West pin
        qpa_nw = (-0.5 * p.box_width + p.perimeter_thickness,
                  0.5 * p.box_height - p.perimeter_thickness)
        qpb_nw = (-0.5 * p.box_width, 0.5 * p.box_height)
        qpa_nw = qpin_rotate_translate(qpa_nw)
        qpb_nw = qpin_rotate_translate(qpb_nw)
        self.add_pin('pin_nw',
                     points=np.array([qpa_nw, qpb_nw]),
                     width=0.01,
                     input_as_norm=True)
        # West pin
        qp2a = (-0.5 * p.box_width + p.perimeter_thickness, 0.0)
        qp2b = (-0.5 * p.box_width, 0.0)
        qp2a = qpin_rotate_translate(qp2a)
        qp2b = qpin_rotate_translate(qp2b)
        self.add_pin('pin_west',
                     points=np.array([qp2a, qp2b]),
                     width=0.01,
                     input_as_norm=True)
        # South-West pin
        qpa_sw = (-0.5 * p.box_width + p.perimeter_thickness,
                  -0.5 * p.box_height + p.perimeter_thickness)
        qpb_sw = (-0.5 * p.box_width, -0.5 * p.box_height)
        qpa_sw = qpin_rotate_translate(qpa_sw)
        qpb_sw = qpin_rotate_translate(qpb_sw)
        self.add_pin('pin_sw',
                     points=np.array([qpa_sw, qpb_sw]),
                     width=0.01,
                     input_as_norm=True)
        # South pin
        qpa_s = (0.0, -0.5 * p.box_height + p.perimeter_thickness)
        qpb_s = (0.0, -0.5 * p.box_height)
        qpa_s = qpin_rotate_translate(qpa_s)
        qpb_s = qpin_rotate_translate(qpb_s)
        self.add_pin('pin_s',
                     points=np.array([qpa_s, qpb_s]),
                     width=0.01,
                     input_as_norm=True)
        # north pin
        qpa_n = (0.0, -0.5 * p.box_height + p.perimeter_thickness + p.initial +
                 30.0 * p.turn_radius)
        qpb_n = (0.0, -0.5 * p.box_height + p.perimeter_thickness + p.initial +
                 30.0 * p.turn_radius + p.final)
        qpa_n = qpin_rotate_translate(qpa_n)
        qpb_n = qpin_rotate_translate(qpb_n)
        self.add_pin('pin_n',
                     points=np.array([qpa_n, qpb_n]),
                     width=0.01,
                     input_as_norm=True)
