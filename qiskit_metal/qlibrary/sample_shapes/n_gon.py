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

from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import QComponent
import numpy as np


class NGon(QComponent):
    """A n-gon polygon. Eg. n = 3 : triangle, n = infinity : circle

    Inherits `QComponent` class.

    .. image::
        NGon.png

    .. meta::
        N-Gon Polygon

    Default Options:
        Convention: Values (unless noted) are strings with units included,
        (e.g., '30um')

        * n: '3' -- Number of sides of the polygon
        * radius: '30um' -- The radius of the circle given n=infinity
        * subtract: 'False'
        * helper: 'False'
    """

    default_options = Dict(n='3',
                           radius='30um',
                           subtract='False',
                           helper='False')
    """Default drawing options"""

    TOOLTIP = """A n-gon polygon"""

    def make(self):
        """The make function implements the logic that creates the geometry
        (poly, path, etc.) from the qcomponent.options dictionary of
        parameters, and the adds them to the design, using
        qcomponent.add_qgeometry(...), adding in extra needed information, such
        as layer, subtract, etc."""
        p = self.p  # p for parsed parameters. Access to the parsed options.
        n = int(p.n)
        # Create the geometry
        # Generates a list of points
        n_polygon = [(p.radius * np.cos(2 * np.pi * x / n),
                      p.radius * np.sin(2 * np.pi * x / n)) for x in range(n)]
        # Converts said list into a shapely polygon
        n_polygon = draw.Polygon(n_polygon)

        n_polygon = draw.rotate(n_polygon, p.orientation, origin=(0, 0))
        n_polygon = draw.translate(n_polygon, p.pos_x, p.pos_y)

        ##############################################
        # add qgeometry
        self.add_qgeometry('poly', {'n_polygon': n_polygon},
                           subtract=p.subtract,
                           helper=p.helper,
                           layer=p.layer,
                           chip=p.chip)
