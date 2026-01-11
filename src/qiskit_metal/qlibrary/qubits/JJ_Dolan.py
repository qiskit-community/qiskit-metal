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
"""
Josephson Junction (Dolan-Style)
REFERENCE: G. Dolan, Applied Physics Letters 31, 337 (1977)
"""
from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core.base import QComponent


class jj_dolan(QComponent):
    """
    The base "JJ_Dolan" inherits the "QComponent" class.
    
    NOTE TO USER: Please be aware that when designing with this
    qcomponent, one must take care in accounting for the junction
    qgeometry when exporting to to GDS and/or to a simulator. This
    qcomponent should not be rendered for EM simulation.

    This creates a "Dolan"-style Josephson Junction consisting
    of two non-overlapping metal rectangles each connected
    to a larger rectangular pad. There is also a second,
    smaller rectangle drawn on a different metal level
    which overlaps part of one of the rectangular fingers.

    .. image::
        JJDolan.png

    .. meta::
        :description: Josephson Junction Dolan

    Default Options:
        * JJ_pad_lower_width: '25um' -- width of lower JJ metal region
        * JJ_pad_lower_height: '10um' -- height of lower JJ metal region
        * JJ_pad_lower_pos_x: '0um' -- the initial x-coord of the lower JJ pad
        * JJ_pad_lower_pos_y: '0um' -- the initial y-coord of the lower JJ pad
        * finger_lower_width: '1um' -- the width of the rectangular finger(s)
        * finger_lower_height: '20um' -- the length of the rectangular finger(s)
        * extension: '1um' -- the amount of rectangle extending beyond X-point
        * offset: '2um' -- the separation between finger and the 2nd metal level
        * second_metal_length: '5um' -- the length of the 2nd metal level
        * second_metal_width: '1um' -- the width of the 2nd metal level
    """
    # Default drawing options
    default_options = Dict(JJ_pad_lower_width='25um',
                           JJ_pad_lower_height='10um',
                           JJ_pad_lower_pos_x='0',
                           JJ_pad_lower_pos_y='0',
                           finger_lower_width='1um',
                           finger_lower_height='20um',
                           extension='1um',
                           offset='2um',
                           second_metal_length='5um',
                           second_metal_width='1um')
    """Default drawing options"""

    # Name prefix of component, if user doesn't provide name
    component_metadata = Dict(short_name='component')
    """Component metadata"""

    def make(self):
        """Convert self.options into QGeometry."""

        p = self.parse_options()  # Parse the string options into numbers

        # draw the lower pad as a rectangle
        JJ_pad_lower = draw.rectangle(p.JJ_pad_lower_width,
                                      p.JJ_pad_lower_height,
                                      p.JJ_pad_lower_pos_x,
                                      p.JJ_pad_lower_pos_y)

        finger_lower = draw.rectangle(
            p.finger_lower_width, p.finger_lower_height, p.JJ_pad_lower_pos_x,
            0.5 * (p.JJ_pad_lower_height + p.finger_lower_height))

        # merge the lower pad and the finger into a single object
        design = draw.union(JJ_pad_lower, finger_lower)

        # copy the pad/finger and rotate it by 90 degrees
        design2 = draw.rotate(design, 90.0)

        # translate the second pad/finger to achieve the desired extension
        # for a Manhattan-like configuration
        design2 = draw.translate(
            design2, 0.5 * (p.JJ_pad_lower_height + p.finger_lower_height) -
            0.5 * p.finger_lower_width - p.extension,
            0.5 * (p.JJ_pad_lower_height + p.finger_lower_height) -
            0.5 * p.finger_lower_width - p.extension)

        # now translate the second pad/finger to achieve the desired offset
        # from the first pad/finger
        design2 = draw.translate(design2,
                                 p.extension + p.finger_lower_width + p.offset)

        final_design = draw.union(design, design2)

        second_metal = draw.rectangle(
            p.second_metal_width, p.second_metal_length,
            p.JJ_pad_lower_pos_x + p.offset + 0.5 * p.finger_lower_width,
            0.5 * p.JJ_pad_lower_height + p.finger_lower_height -
            0.5 * p.second_metal_length)

        # translate everything so that the bottom left corner of the lower
        # pad is at the origin
        final_design = draw.translate(final_design, 0.5 * p.JJ_pad_lower_width,
                                      0.5 * p.JJ_pad_lower_height)
        second_metal = draw.translate(second_metal, 0.5 * p.JJ_pad_lower_width,
                                      0.5 * p.JJ_pad_lower_height)

        # now translate so that the bottom left corner is at the
        # user-defined coordinates (pos_x, pos_y)
        final_design = draw.translate(final_design, p.pos_x, p.pos_y)
        second_metal = draw.translate(second_metal, p.pos_x, p.pos_y)

        geom1 = {'design': final_design}
        self.add_qgeometry('poly', geom1, layer=p.layer, subtract=False)

        geom2 = {'design': second_metal}
        self.add_qgeometry('poly', geom2, layer=2.0, subtract=False)
