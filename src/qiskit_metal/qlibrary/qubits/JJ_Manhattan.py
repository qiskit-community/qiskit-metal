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
Josephson Junction (Manhattan-Style)
REFERENCE: I.M. Pop et al., Nature 508, 369-372 (2014)
"""
from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core.base import QComponent


class jj_manhattan(QComponent):
    """
    The base "JJ_Manhattan" inherits the "QComponent" class.
    
    NOTE TO USER: Please be aware that when designing with this
    qcomponent, one must take care in accounting for the junction
    qgeometry when exporting to to GDS and/or to a simulator. This
    qcomponent should not be rendered for EM simulation.

    This creates a "Manhattan"-style Josephson Junction consisting
    of two overlapping thin metal strips, each connected to a
    larger metallic pad region.

    .. image::
        JJManhattan.png

    .. meta::
        :description: Josephson Junction Manhattan

    Default Options:
        * JJ_pad_lower_width: '4um' -- width of lower JJ metal region
        * JJ_pad_lower_height: '2um' -- height of lower JJ metal region
        * JJ_pad_lower_pos_x: '0' -- the initial x-coord of the lower rectangle
        * JJ_pad_lower_pos_y: '0' -- the initial y-coord of the lower rectangle
        * finger_lower_width: '1um' -- the width of the overlapping rectangular finger(s)
        * finger_lower_height: '20um' -- the length of the overlapping rectangular finger(s)
        * extension: '1um' -- the length of the fingers extending beyond the cross-point
    """
    # Default drawing options
    default_options = Dict(JJ_pad_lower_width='25um',
                           JJ_pad_lower_height='10um',
                           JJ_pad_lower_pos_x='0',
                           JJ_pad_lower_pos_y='0',
                           finger_lower_width='1um',
                           finger_lower_height='20um',
                           extension='1um')
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

        # fudge factor to merge the two options
        finger_lower = draw.translate(finger_lower, 0.0, -0.0001)

        # merge the lower pad and the finger into a single object
        design = draw.union(JJ_pad_lower, finger_lower)

        # copy the pad/finger and rotate it by 90 degrees
        design2 = draw.rotate(design, 90.0)

        # translate the second pad/finger to achieve the desired extension
        design2 = draw.translate(
            design2, 0.5 * (p.JJ_pad_lower_height + p.finger_lower_height) -
            0.5 * p.finger_lower_width - p.extension,
            0.5 * (p.JJ_pad_lower_height + p.finger_lower_height) -
            0.5 * p.finger_lower_width - p.extension)

        final_design = draw.union(design, design2)

        # translate the final design so that the bottom left
        # corner of the lower pad is at the origin
        final_design = draw.translate(final_design, 0.5 * p.JJ_pad_lower_width,
                                      0.5 * p.JJ_pad_lower_height)

        # now translate so that the design is centered on the
        # user-defined coordinates (pos_x, pos_y)
        final_design = draw.translate(final_design, p.pos_x, p.pos_y)

        geom = {'design': final_design}
        self.add_qgeometry('poly', geom, layer=p.layer, subtract=False)
