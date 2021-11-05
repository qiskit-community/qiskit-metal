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
"""Interdigitated Transmon.
"""

from math import sin, cos
import numpy as np
from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core.base import QComponent

#from ... import config
#if not config.is_building_docs():
#    from qiskit_metal import is_true


class TransmonInterdigitated(QComponent):
    """
    The base "TransmonInterdigitated" inherits the "QComponent" class.

    This creates a transmon pocket with two large pads connected by a Josephson
    junction. Both pads have four interdigitated "fingers" which increase the
    capacitance of the structure. There are three coupling capacitor pads with qpins
    defined; these can be connected to other structures in a design using CPWs.

    .. image::
        Transmon_Interdigitated.png

    .. meta::
        Transmon Interdigitated

    Default Options:
        * pad_width: '1000um' -- width of the large rectangular pads on either side
          of the junction
        * pad_height: '300um' -- height of the large rectangular pads on either side
          of the junction
        * finger_width: '50um' -- width of the "finger" on either side of the junction
        * finger_height: '100um' -- height of the "finger" on the side of the junction
        * finger_space: '50um' -- height of the Josephson Junction (equivalently; space
          between two fingers)
        * pad_pos_x: '0um' -- the internal coordinate defining the center of the bottom
          rectangular pad
        * pad_pos_y: '0um' -- the internal coordinate defining the center of the bottom
          rectangular pad
        * comb_width: '50um' -- the width of the four interdigitated combs connected to
          either pad
        * comb_space_vert: '50um' -- the space between the edge of a comb and the edge of
          the opposite rectangular pad
        * comb_space_hor: '50um' -- the space between adjacent interdigitated comb structures
        * jj_width: '20um' -- the width of the Josephson Junction located between the two
          fingers of the device
        * cc_space: '50um' -- the space between the lower rectangular pad and the coupling
          capacitor below it
        * cc_width: '100um' -- the width of the coupling capacitor located below the bottom
          rectangular pad
        * cc_height: '100um' -- the height of the coupling capacitor located below the bottom
          rectangular pad
        * cc_topleft_space: '50um' -- the space between the upper rectangular pad and the top
          left coupling capacitor
        * cc_topleft_width: '100um' -- the width of the top left coupling capacitor pad
        * cc_topleft_height: '100um' -- the height of the top left coupling capacitor pad
        * cc_topright_space: '50um' -- the space between the upper rectangular pad and the
          top right coupling capacitor
        * cc_topright_width: '100um' -- the width of the top right coupling capacitor pad
        * cc_topright_height: '100um' -- the height of the top right coupling capacitor pad
        * rotation_top_pad: '180' -- internal coordinate defining the angle of rotation
          between top and bottom pads
        * inductor_width: '20.0um' -- the width of the Josephson Junction
    """

    # Default drawing options
    default_options = Dict(pad_width='1000um',
                           pad_height='300um',
                           finger_width='50um',
                           finger_height='100um',
                           finger_space='50um',
                           pad_pos_x='0um',
                           pad_pos_y='0um',
                           comb_width='50um',
                           comb_space_vert='50um',
                           comb_space_hor='50um',
                           jj_width='20um',
                           cc_space='50um',
                           cc_width='100um',
                           cc_height='100um',
                           cc_topleft_space='50um',
                           cc_topleft_width='100um',
                           cc_topleft_height='100um',
                           cc_topright_space='50um',
                           cc_topright_width='100um',
                           cc_topright_height='100um',
                           rotation_top_pad='180',
                           inductor_width='20um')
    """Default drawing options"""

    # Name prefix of component, if user doesn't provide name
    component_metadata = Dict(short_name='component')
    """Component metadata"""

    def make(self):
        """Convert self.options into QGeometry."""

        p = self.parse_options()  # Parse the string options into numbers

        # draw the lower pad as a rectangle
        pad_lower = draw.rectangle(p.pad_width, p.pad_height, p.pad_pos_x,
                                   p.pad_pos_y)

        # draw the lower finger as a rectangle
        finger_lower = draw.rectangle(
            p.finger_width, p.finger_height, p.pad_pos_x, p.pad_pos_y +
            0.49999 * (p.pad_height) + 0.49999 * (p.finger_height))

        # draw the Josephson Junction as a LineString
        rect_jj = draw.LineString([
            (0, 0.5 * p.pad_height + p.finger_height),
            (0, 0.5 * p.pad_height + p.finger_height + p.finger_space)
        ])

        # draw the first comb to the right of the lower finger as a rectangle
        comb1_lower = draw.rectangle(
            p.comb_width, (2 * p.finger_height),
            (0.5 * p.finger_width + p.comb_space_hor + 0.5 * p.comb_width),
            (p.pad_pos_y + 0.5 * p.pad_height + 1.0 * p.finger_height))

        # draw the second comb to the right of the lower finger by translating the first comb
        comb2_lower = draw.translate(comb1_lower,
                                     2.0 * (p.comb_space_hor + p.comb_width),
                                     0.0)

        # draw the first comb to the left of the lower finger
        comb3_lower = draw.rectangle(
            p.comb_width, (2 * p.finger_height),
            (-0.5 * p.finger_width - 2.0 * p.comb_space_hor -
             1.5 * p.comb_width),
            (p.pad_pos_y + 0.5 * p.pad_height + 1.0 * p.finger_height))

        # draw the second comb to the left of the lower finger
        comb4_lower = draw.translate(comb3_lower,
                                     -2.0 * (p.comb_space_hor + p.comb_width),
                                     0.0)

        coupling_capacitor = draw.rectangle(
            p.cc_width, p.cc_height, p.pad_pos_x,
            p.pad_pos_y - 0.5 * (p.pad_height) - p.cc_space - 0.5 * p.cc_height)

        cc_topleft = draw.rectangle(
            p.cc_topleft_width, p.cc_topleft_height,
            p.pad_pos_x - 0.5 * p.pad_width + 0.5 * p.cc_topleft_width,
            p.pad_pos_y + 1.5 * p.pad_height + 2.0 * p.finger_height +
            p.finger_space + p.cc_topleft_space + 0.5 * p.cc_topleft_height)

        cc_topright = draw.translate(
            cc_topleft,
            p.pad_width - 0.5 * p.cc_topleft_width - 0.5 * p.cc_topright_width,
            0.0)

        # merge the bottom elements
        bottom = draw.union(pad_lower, finger_lower, comb1_lower, comb2_lower,
                            comb3_lower, comb4_lower)

        # create the top portion of the comb by translating and rotating
        # the bottom portion of the comb
        top = draw.translate(bottom, 0.0, p.pad_height + p.finger_space)
        top = draw.rotate(top, p.rotation_top_pad)

        # draw the transmon pocket bounding box
        pocket = draw.rectangle(1.5 * p.pad_width, 5.0 * p.pad_height)

        # the origin is originally set to the middle of the lower pad.
        # Let's move it to the center of the JJ.
        bottom = draw.translate(
            bottom, 0.0,
            -0.5 * p.pad_height - p.finger_height - 0.5 * p.finger_space)
        top = draw.translate(
            top, 0.0,
            -0.5 * p.pad_height - p.finger_height - 0.5 * p.finger_space)
        coupling_capacitor = draw.translate(
            coupling_capacitor, 0.0,
            -0.5 * p.pad_height - p.finger_height - 0.5 * p.finger_space)
        cc_topleft = draw.translate(
            cc_topleft, 0.0,
            -0.5 * p.pad_height - p.finger_height - 0.5 * p.finger_space)
        cc_topright = draw.translate(
            cc_topright, 0.0,
            -0.5 * p.pad_height - p.finger_height - 0.5 * p.finger_space)
        rect_jj = draw.translate(
            rect_jj, 0.0,
            -0.5 * p.pad_height - p.finger_height - 0.5 * p.finger_space)

        # now translate the final structure according to the user input
        bottom = draw.rotate(bottom, p.orientation, origin=(0, 0))
        bottom = draw.translate(bottom, p.pos_x, p.pos_y)
        top = draw.rotate(top, p.orientation, origin=(0, 0))
        top = draw.translate(top, p.pos_x, p.pos_y)
        coupling_capacitor = draw.rotate(coupling_capacitor,
                                         p.orientation,
                                         origin=(0, 0))
        coupling_capacitor = draw.translate(coupling_capacitor, p.pos_x,
                                            p.pos_y)
        cc_topleft = draw.rotate(cc_topleft, p.orientation, origin=(0, 0))
        cc_topleft = draw.translate(cc_topleft, p.pos_x, p.pos_y)
        cc_topright = draw.rotate(cc_topright, p.orientation, origin=(0, 0))
        cc_topright = draw.translate(cc_topright, p.pos_x, p.pos_y)
        rect_jj = draw.rotate(rect_jj, p.orientation, origin=(0, 0))
        rect_jj = draw.translate(rect_jj, p.pos_x, p.pos_y)
        pocket = draw.rotate(pocket, p.orientation, origin=(0, 0))
        pocket = draw.translate(pocket, p.pos_x, p.pos_y)

        # add each shape separately
        geom1 = {'pad_bot': bottom}
        geom2 = {'pad_top': top}
        geom3 = {'readout': coupling_capacitor}
        geom4 = {'bus1': cc_topleft}
        geom5 = {'bus2': cc_topright}
        geom_pocket = {'pocket': pocket}
        geom_jj = {'design': rect_jj}

        # add to qgeometry
        self.add_qgeometry('poly', geom1, layer=p.layer, subtract=False)
        self.add_qgeometry('poly', geom2, layer=p.layer, subtract=False)
        self.add_qgeometry('poly', geom3, layer=p.layer, subtract=False)
        self.add_qgeometry('poly', geom4, layer=p.layer, subtract=False)
        self.add_qgeometry('poly', geom5, layer=p.layer, subtract=False)

        self.add_qgeometry('poly', geom_pocket, layer=p.layer, subtract=True)
        self.add_qgeometry('junction',
                           geom_jj,
                           layer=p.layer,
                           subtract=False,
                           width=p.inductor_width)

        ###################################################################

        # Add Qpin connections for coupling capacitors

        # define a function that both rotates and translates the
        # qpin coordinates
        def qpin_rotate_translate(x):
            """ This function rotates the coordinates of the three qpins
            according to the user inputs for "pos_x", "pos_y"
            and "orientation".
            """
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

        # Add Qpin connections for the bottom coupling capacitor

        qp1a = (0.0,
                -0.5 * p.pad_height - p.finger_height - 0.5 * p.finger_space)
        qp1b = (0.0, -0.5 * p.pad_height - p.cc_space - p.cc_height -
                0.5 * p.pad_height - p.finger_height - 0.5 * p.finger_space)

        # rotate and translate the qpin coordinates
        qp1a = qpin_rotate_translate(qp1a)
        qp1b = qpin_rotate_translate(qp1b)

        self.add_pin('readout',
                     points=np.array([qp1a, qp1b]),
                     width=0.01,
                     input_as_norm=True)

        # Add Qpin connections for top left coupling capacitor

        qp2a = (p.pad_pos_x - 0.5 * p.pad_width + 0.5 * p.cc_topleft_width,
                p.pad_pos_y + 1.5 * p.pad_height + 2.0 * p.finger_height +
                p.finger_space + p.cc_topleft_space +
                0.5 * p.cc_topleft_height - 0.5 * p.pad_height -
                p.finger_height - 0.5 * p.finger_space)
        qp2b = (p.pad_pos_x - 0.5 * p.pad_width, p.pad_pos_y +
                1.5 * p.pad_height + 2.0 * p.finger_height + p.finger_space +
                p.cc_topleft_space + 0.5 * p.cc_topleft_height -
                0.5 * p.pad_height - p.finger_height - 0.5 * p.finger_space)

        qp2a = qpin_rotate_translate(qp2a)
        qp2b = qpin_rotate_translate(qp2b)

        self.add_pin('bus1',
                     points=np.array([qp2a, qp2b]),
                     width=0.01,
                     input_as_norm=True)

        # Add Qpin connections for top right coupling capacitor

        qp3a = (p.pad_pos_x + 0.5 * p.pad_width - 0.5 * p.cc_topleft_width,
                p.pad_pos_y + 1.5 * p.pad_height + 2.0 * p.finger_height +
                p.finger_space + p.cc_topleft_space +
                0.5 * p.cc_topleft_height - 0.5 * p.pad_height -
                p.finger_height - 0.5 * p.finger_space)
        qp3b = (p.pad_pos_x + 0.5 * p.pad_width, p.pad_pos_y +
                1.5 * p.pad_height + 2.0 * p.finger_height + p.finger_space +
                p.cc_topleft_space + 0.5 * p.cc_topleft_height -
                0.5 * p.pad_height - p.finger_height - 0.5 * p.finger_space)

        qp3a = qpin_rotate_translate(qp3a)
        qp3b = qpin_rotate_translate(qp3b)

        self.add_pin('bus2',
                     points=np.array([qp3a, qp3b]),
                     width=0.01,
                     input_as_norm=True)
