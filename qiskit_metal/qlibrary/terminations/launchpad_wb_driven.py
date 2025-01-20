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


class LaunchpadWirebondDriven(QComponent):
    r"""Launch pad to feed/read signals to/from the chip.

    Inherits 'QComponent' class.

    Creates a 50 ohm launch pad with a ground pocket cutout.
    Limited but expandable parameters to control the launchpad polygons.
    The (0,0) point is the center of the necking of the launch tip.
    The pin attaches directly to the built in lead length at its midpoint
	There is pin at the back of the pad for DrivenModal simulations

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
            |      ---------\\
          in|      |    0    |    (0,0) pin at midpoint of necking, before the lead
            |      ---------//
            |          /
            -----------

            y
            ^
            |
            |------> x

    .. image::
        LaunchpadWirebond.png

    .. meta::
        Launchpad Wirebond Driven

    Default Options:
        * trace_width: 'cpw_width' -- Width of the transmission line attached to the launch pad
        * trace_gap: 'cpw_gap' -- Gap of the transmission line
        * lead_length: '25um' -- Length of the transmission line attached to the launch pad
        * pad_width: '80um' -- Width of the launch pad
        * pad_height: '80um' -- Height of the launch pad
        * pad_gap: '58um' -- Gap of the launch pad
        * taper_height: '122um' -- Height of the taper from the launch pad to the transmission line
    """

    default_options = Dict(trace_width='cpw_width',
                           trace_gap='cpw_gap',
                           lead_length='25um',
                           pad_width='80um',
                           pad_height='80um',
                           pad_gap='58um',
                           taper_height='122um')
    """Default options"""

    TOOLTIP = """Launch pad to feed/read signals to/from the chip."""

    def make(self):
        """This is executed by the user to generate the qgeometry for the
        component."""

        p = self.p

        pad_width = p.pad_width
        pad_height = p.pad_height
        pad_gap = p.pad_gap
        trace_width = p.trace_width
        trace_width_half = trace_width / 2.
        pad_width_half = pad_width / 2.
        lead_length = p.lead_length
        taper_height = p.taper_height
        trace_gap = p.trace_gap

        pad_gap = p.pad_gap
        #########################################################

        # Geometry of main launch structure
        # The shape is a polygon and we prepare this point as orientation is 0 degree
        launch_pad = draw.Polygon([
            (0, trace_width_half), (-taper_height, pad_width_half),
            (-(pad_height + taper_height), pad_width_half),
            (-(pad_height + taper_height), -pad_width_half),
            (-taper_height, -pad_width_half), (0, -trace_width_half),
            (lead_length, -trace_width_half), (lead_length, trace_width_half),
            (0, trace_width_half)
        ])

        # Geometry pocket (gap)
        # Same way applied for pocket
        pocket = draw.Polygon([(0, trace_width_half + trace_gap),
                               (-taper_height, pad_width_half + pad_gap),
                               (-(pad_height + taper_height + pad_gap),
                                pad_width_half + pad_gap),
                               (-(pad_height + taper_height + pad_gap),
                                -(pad_width_half + pad_gap)),
                               (-taper_height, -(pad_width_half + pad_gap)),
                               (0, -(trace_width_half + trace_gap)),
                               (lead_length, -(trace_width_half + trace_gap)),
                               (lead_length, trace_width_half + trace_gap),
                               (0, trace_width_half + trace_gap)])

        # These variables are used to graphically locate the pin locations
        main_pin_line = draw.LineString([(lead_length, trace_width_half),
                                         (lead_length, -trace_width_half)])
        driven_pin_line = draw.LineString([
            (-(pad_height + taper_height + pad_gap), pad_width_half),
            (-(pad_height + taper_height + pad_gap), -pad_width_half)
        ])

        # Create polygon object list
        polys1 = [main_pin_line, driven_pin_line, launch_pad, pocket]

        # Rotates and translates all the objects as requested. Uses package functions in
        # 'draw_utility' for easy rotation/translation
        polys1 = draw.rotate(polys1, p.orientation, origin=(0, 0))
        polys1 = draw.translate(polys1, xoff=p.pos_x, yoff=p.pos_y)
        [main_pin_line, driven_pin_line, launch_pad, pocket] = polys1

        # Adds the object to the qgeometry table
        self.add_qgeometry('poly', dict(launch_pad=launch_pad), layer=p.layer)

        # Subtracts out ground plane on the layer its on
        self.add_qgeometry('poly',
                           dict(pocket=pocket),
                           subtract=True,
                           layer=p.layer)

        # Generates the pins
        self.add_pin('tie', main_pin_line.coords, trace_width)
        self.add_pin('in', driven_pin_line.coords, pad_width, gap=pad_gap)
