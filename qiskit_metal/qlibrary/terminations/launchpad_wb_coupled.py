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

#  This a launch structure used on BlueJayV2, used for wire bonding
#  There is no CPW tee attached to this p#

# Imports required for drawing

# import numpy as np # (currently not used, may be needed later for component customization)
from qiskit_metal import draw
from qiskit_metal.toolbox_python.attr_dict import Dict
from qiskit_metal.qlibrary.core import QComponent

# Define class and options for the launch geometry


class LaunchpadWirebondCoupled(QComponent):
    r"""Launch pad to feed/read signals to/from the chip.

    Inherits 'QComponent' class.

    .. image:
        LaunchpadWirebondCoupled.png

    .. meta::
        Launchpad Wirebond Coupled

    Creates a 50 ohm launch pad with a ground pocket cutout.
    Limited but expandable parameters to control the launchpad polygons.
    The (0,0) point is the center of the necking of the launch tip.
    The pin attaches directly to the built in lead length at its midpoint
    This launch has an inductive coupler section.

    Pocket and pad:
        Pocket and launch pad geometries are currently fixed.
        (0,0) point is the midpoint of the necking of the launch tip.
        Pocket is a negative shape that is cut out of the ground plane

    Values (unless noted) are strings with units included, (e.g., '30um')

    Sketch:
        Below is a sketch of the launch
        ::

            -----------
            |          \
            |      ------------\\   |--
            |      |    O   --------|    (0,0) pin at midpoint of necking, before the coupling section
            |      ------------//   |--
            |          /
            -----------

            y
            ^
            |
            |------> x

    .. image::
        LaunchpadWirebondCoupled.png

    Default Options:
        * trace_width: 'cpw_width' -- center trace width of the terminating transmission line
        * trace_gap: 'cpw_gap' -- gap of the transmission line
        * coupler_length: '62.5um' -- distance between the necking and the end of the coupler external finger
        * lead_length: '25um' -- length of the cpw line attached to the end of the launch pad
    """

    default_options = Dict(trace_width='cpw_width',
                           trace_gap='cpw_gap',
                           coupler_length='62.5um',
                           lead_length='25um')
    """Default options"""

    TOOLTIP = """Launch pad to feed/read signals to/from the chip."""

    def make(self):
        """This is executed by the user to generate the qgeometry for the
        component."""

        p = self.p
        lead_length = p.lead_length
        trace_width = p.trace_width
        trace_width_half = trace_width / 2
        trace_gap = p.trace_gap
        inner_finger_width = .001
        inner_finger_width_half = inner_finger_width / 2
        inner_finger_offset = .015
        finger_side_gap = .002
        outer_finger_tip_gap = .0075
        inner_finger_tip_gap = .05 + inner_finger_offset
        outer_finger_width = (trace_width - inner_finger_width -
                              2 * finger_side_gap) / 2
        coupler_length = p.coupler_length
        lead_offset = coupler_length + outer_finger_tip_gap
        #########################################################

        # Geometry of main launch structure
        launch_pad = draw.Polygon([
            (0, trace_width_half), (-.122, trace_width_half + .035),
            (-.202, trace_width_half + .035), (-.202, -trace_width_half - .035),
            (-.122, -trace_width_half - .035), (0, -trace_width_half),
            (coupler_length, -trace_width_half),
            (coupler_length, -trace_width_half + outer_finger_width),
            (-inner_finger_tip_gap + inner_finger_offset,
             -trace_width_half + outer_finger_width),
            (-inner_finger_tip_gap + inner_finger_offset,
             trace_width_half - outer_finger_width),
            (coupler_length, trace_width_half - outer_finger_width),
            (coupler_length, trace_width_half), (0, trace_width / 2)
        ])

        # Geometry of coupling structure
        ind_stub = draw.Polygon([
            (inner_finger_offset, -inner_finger_width_half),
            (lead_offset, -inner_finger_width_half),
            (lead_offset, -trace_width_half),
            (lead_offset + lead_length, -trace_width_half),
            (lead_offset + lead_length, trace_width_half),
            (lead_offset, trace_width_half),
            (lead_offset, +inner_finger_width_half),
            (inner_finger_offset, +inner_finger_width_half),
            (inner_finger_offset, -inner_finger_width_half)
        ])

        # Geometry pocket (gap)
        pocket = draw.Polygon([
            (0, trace_width_half + trace_gap),
            (-.122, trace_width_half + trace_gap + .087),
            (-.25, trace_width_half + trace_gap + .087),
            (-.25, -trace_width_half - trace_gap - .087),
            (-.122, -trace_width_half - trace_gap - .087),
            (0, -trace_width_half - trace_gap),
            (lead_offset + lead_length, -trace_width_half - trace_gap),
            (lead_offset + lead_length, +trace_width_half + trace_gap),
            (0, trace_width_half + trace_gap)
        ])

        # These variables are used to graphically locate the pin locations
        main_pin_line = draw.LineString([
            (lead_offset + lead_length, trace_width_half),
            (lead_offset + lead_length, -trace_width_half)
        ])

        # Create polygon object list
        polys1 = [main_pin_line, launch_pad, ind_stub, pocket]

        # Rotates and translates all the objects as requested. Uses package functions
        # in 'draw_utility' for easy rotation/translation
        polys1 = draw.rotate(polys1, p.orientation, origin=(0, 0))
        polys1 = draw.translate(polys1, xoff=p.pos_x, yoff=p.pos_y)
        [main_pin_line, launch_pad, ind_stub, pocket] = polys1

        # Adds the object to the qgeometry table
        self.add_qgeometry('poly',
                           dict(launch_pad=launch_pad, ind_stub=ind_stub),
                           layer=p.layer)

        # Subtracts out ground plane on the layer its on
        self.add_qgeometry('poly',
                           dict(pocket=pocket),
                           subtract=True,
                           layer=p.layer)

        # Generates the pins
        self.add_pin('tie', main_pin_line.coords, trace_width)
