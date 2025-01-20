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

from shapely.geometry import CAP_STYLE, JOIN_STYLE
from qiskit_metal import draw  # , Dict
from qiskit_metal.qlibrary.core import QComponent
#from qiskit_metal import is_true


class CircleCaterpillar(QComponent):
    """A single configurable circle.

    Inherits QComponent class.

    .. image::
        CircleCaterpillar.png

    .. meta::
        Circle Caterpillar

    Default Options:
        * segments: '5'
        * distance: '1.2'
        * radius: '300um'
        * resolution: '16'
        * cap_style: 'round' -- Valid options are 'round', 'flat', 'square'
        * subtract: 'False'
        * helper: 'False'
    """

    default_options = dict(
        segments='5',
        distance='1.2',
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
        caterpillar = [
            draw.Point(p.pos_x - p.radius * i * p.distance, p.pos_y).buffer(
                p.radius,
                resolution=int(p.resolution),
                cap_style=getattr(CAP_STYLE, p.cap_style),
                #join_style = getattr(JOIN_STYLE, p.join_style)
            ) for i in range(int(p.segments))
        ]
        caterpillar = draw.union(caterpillar)

        poly = draw.Polygon([(0, 0), (0.5, 0), (0.25, 0.5)])
        poly = draw.translate(poly, p.pos_x, p.pos_y)
        poly = draw.rotate(poly, angle=65)
        caterpillar = draw.subtract(caterpillar, poly)

        # rect = draw.rectangle(p.radius*0.75, p.radius*0.23,
        #                      xoff=p.pos_x+p.radius*0.3,
        #                      yoff=p.pos_y+p.radius*0.4)
        #caterpillar = draw.subtract(caterpillar, rect)
        # print(caterpillar)

        # add qgeometry
        #self.add_qgeometry('poly', {'mount': rect})
        self.add_qgeometry('poly', {'caterpillar': caterpillar})
        # subtract=p.subtract,
        #                   helper=p.helper, layer=p.layer, chip=p.chip)
