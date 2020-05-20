# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from ..base import QComponent
from ... import draw
from ...draw.basic import CAP_STYLE, JOIN_STYLE


class CircleRaster(QComponent):
    """A single configurable square."""

    default_options = dict(
        radius='300um',
        pos_x='0um',
        pos_y='0um',
        resolution='16',
        cap_style='round',  # round, flat, square
        # join_style = 'round', # round, mitre, bevel
        # General
        subtract='False',
        helper='False',
        chip='main',
        layer='1'
    )

    def make(self):
        p = self.p  # p for parsed parameters. Access to the parsed options.

        # create the geometry
        circle = draw.Point(p.pos_x, p.pos_y).buffer(p.radius,
                                                     resolution=int(
                                                         p.resolution),
                                                     cap_style=getattr(
                                                         CAP_STYLE, p.cap_style),
                                                     #join_style = getattr(JOIN_STYLE, p.join_style)
                                                     )

        # add elements
        self.add_elements('poly', {'circle': circle}, subtract=p.subtract,
                          helper=p.helper, layer=p.layer, chip=p.chip)
