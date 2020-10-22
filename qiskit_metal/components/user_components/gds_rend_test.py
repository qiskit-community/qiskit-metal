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
'''
@date: 2019
@author: Qiskit Team

TEST COMPONENT
NOT FOR ACTUAL USE
'''

from qiskit_metal import draw, Dict
from qiskit_metal.components.base import QComponent
import numpy as np


class GDSRendTest(QComponent):
    """TEST COMPONENT
    """

    component_metadata = Dict(
        short_name='TESTCASE'
        )
    """Component metadata"""

    default_options = Dict(
    )
    """Default connector options"""

    def make(self):
        """Build the component"""

        #square donut
        rect_base = draw.shapely.geometry.box(-0.199999999999995, -0.2, 0.2, 0.2)
        rect_hole = draw.shapely.geometry.box(-0.1, -0.1, 0.1, 0.0999999999995)

        square_donut = draw.subtract(rect_base, rect_hole)

        #square with multiple holes
        rect_hole_2 = draw.shapely.geometry.box(-0.15, -0.15, -0.05, -0.05)
        rect_hole_3 = draw.shapely.geometry.box(0.15, 0.15, 0.05, 0.05)

        square_donut_2 = draw.subtract(rect_base,rect_hole_2)
        square_donut_2 = draw.subtract(square_donut_2,rect_hole_3)
        square_donut_2 = draw.translate(square_donut_2,1,0)

        #'square' with no interior holes (makes two 'half moons')
        rect_base_2 = draw.shapely.geometry.box(-0.2, -0.2, 0, 0.2)
        rect_hole_4 = draw.shapely.geometry.box(-0.1, -0.1, 0, 0.1)
        square_donut_3L = draw.subtract(rect_base_2,rect_hole_4)
        square_donut_3R = draw.rotate(square_donut_3L, 180, origin=(0, 0))

        #cascaded union of the above square
        square_donut_4 = draw.shapely.ops.cascaded_union([square_donut_3L,square_donut_3R])

        polys = [square_donut_3L, square_donut_3R]
        polys = draw.translate(polys, -1, 0)
        [square_donut_3L, square_donut_3R] = polys

        square_donut_4 = draw.translate(square_donut_4, 0, 1)
        
        #MultiPolyTest
        rect_hole_5 = draw.shapely.geometry.Polygon([(-0.22,-0.2),(-0.2,-0.22),(0.22,0.2),(0.2,0.22)])
        test_cut = draw.subtract(rect_base,rect_hole_5)
        test_cut = draw.translate(test_cut,0,-1)
        
        #linstring check
        line_tester = draw.LineString([(0.400000000002,-0.4), (0.4, 0.4), (0.5,0.4),(0.5,0.5)])
        #Add to qgeometry
        self.add_qgeometry('path', {'line_test':line_tester}, width=0.02)
        self.add_qgeometry('poly', {'square_donut':square_donut,'square_donut2':square_donut_2})

        #self.add_qgeometry('poly', {'square_donut2':square_donut_2})
        self.add_qgeometry('poly', {'HalfMoon_L':square_donut_3L})
        self.add_qgeometry('poly', {'HalfMoon_R':square_donut_3R})
        self.add_qgeometry('poly', {'Unioned_HalfMoon':square_donut_4})
        self.add_qgeometry('poly', {'MultiPoly':test_cut})

