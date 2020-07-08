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

"""File contains dictionary for Rectangle and the make()."""

from qiskit_metal import draw, Dict#, QComponent
from qiskit_metal.components.base import QComponent
#from qiskit_metal import is_true
import numpy as np

class NGon(QComponent):
    """A single configurable square.

        Inherits QComponent class

        The class will add default_options class Dict to QComponent class before calling make.
    """

    default_options = Dict(
        n = '3',
        radius = '30um',
        pos_x='0um',
        pos_y='0um',
        rotation='0',
        subtract='False',
        helper='False',
        chip='main',
        layer='1'
    )
    """Default drawing options"""

    def make(self):
        """Build the component"""
        p = self.p  # p for parsed parameters. Access to the parsed options.
        n = int(p.n)
        #Create the geometry
        #Generates a list of points
        n_polygon = [(p.radius*np.cos(2*np.pi*x/n),p.radius*np.sin(2*np.pi*x/n)) for x in range(n)]
        #Converts said list into a shapely polygon
        n_polygon = draw.Polygon(n_polygon)

        n_polygon = draw.rotate(n_polygon, p.rotation, origin=(0, 0))
        n_polygon = draw.translate(n_polygon, p.pos_x, p.pos_y)

        ##############################################
        # add elements
        self.add_elements('poly', {'n_polygon': n_polygon}, subtract=p.subtract,
                          helper=p.helper, layer=p.layer, chip=p.chip)
