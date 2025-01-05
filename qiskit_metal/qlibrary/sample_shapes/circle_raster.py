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
"""This is the CircleCaterpillar module."""

from qiskit_metal import draw, Dict  # , QComponent
from qiskit_metal.qlibrary.core import QComponent
#from qiskit_metal import is_true
from shapely.geometry import CAP_STYLE, JOIN_STYLE


class CircleRaster(QComponent):
    """A single configurable circle.

    Inherits QComponent class.

    .. image::
        CircleRaster.png

    .. meta::
        Circle Raster

    Default Options:
        * radius: '300um'
        * resolution: '16'
        * cap_style: 'round' -- Valid options are 'round', 'flat', 'square'
        * subtract: 'False'
        * helper: 'False'
    """

    default_options = dict(
        radius='300um',
        resolution='16',
        cap_style='round',  # round, flat, square
        # join_style = 'round', # round, mitre, bevel
        # General
        subtract='False',
        helper='False')
    """Default drawing options"""

    TOOLTIP = """A single configurable circle"""

    def make(self):
        """The make function implements the logic that creates the geometry
        (poly, path, etc.) from the qcomponent.options dictionary of
        parameters, and the adds them to the design, using
        qcomponent.add_qgeometry(...), adding in extra needed information, such
        as layer, subtract, etc."""
        p = self.p  # p for parsed parameters. Access to the parsed options.

        # create the geometry
        circle = draw.Point(p.pos_x, p.pos_y).buffer(
            p.radius,
            resolution=int(p.resolution),
            cap_style=getattr(CAP_STYLE, p.cap_style),
            #join_style = getattr(JOIN_STYLE, p.join_style)
        )

        # add qgeometry
        self.add_qgeometry('poly', {'circle': circle},
                           subtract=p.subtract,
                           helper=p.helper,
                           layer=p.layer,
                           chip=p.chip)
