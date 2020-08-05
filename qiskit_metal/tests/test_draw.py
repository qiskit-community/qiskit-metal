# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019-2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

#pylint: disable-msg=unnecessary-pass

"""
Qiskit Metal unit tests analyses functionality.

Created on Wed Apr 22 10:02:44 2020
@author: Jeremy D. Drysdale
"""

import unittest

from shapely.geometry import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry import LineString

from qiskit_metal.draw import basic
from qiskit_metal.draw.utility import Vector
from qiskit_metal.tests.assertions import AssertionsMixin

class TestDraw(unittest.TestCase, AssertionsMixin):
    """
    Unit test class
    """

    def setUp(self):
        """
        Setup unit test
        """
        pass

    def tearDown(self):
        """
        Tie any loose ends
        """
        pass

    def test_draw_instantiate_vector(self):
        """
        Test instantiation of Vector class
        """
        try:
            Vector
        except Exception:
            self.fail("Vector failed")

    def test_draw_basic_rectangle(self):
        """
        Test rectangle in basic.py
        """
        polygon_actual = basic.rectangle(0.5, 1.5, 2.1, 3.2)
        polygon_expected = Polygon([[1.85, 2.45], [2.35, 2.45], [2.35, 3.95], [1.85, 3.95], [1.85, 2.45]])

        coords_actual = list(polygon_actual.exterior.coords)
        coords_expected = list(polygon_expected.exterior.coords)
        self.assertEqual(len(coords_actual), len(coords_expected))
        for i in range(len(coords_actual)):
            for j in range(2):
                self.assertEqual(coords_actual[i][j], coords_expected[i][j])

    def test_draw_basic_is_rectangle(self):
        """
        Test is_rectangle in basic.py
        """
        my_rectangle = basic.rectangle(0.5, 1.5, 2.1, 3.2)
        my_integer = 7

        self.assertEqual(basic.is_rectangle(my_rectangle), True)
        self.assertEqual(basic.is_rectangle(my_integer), False)

    def test_draw_basic_subtract(self):
        """
        Test subtract in basic.py
        """
        first = basic.rectangle(0.5, 1.5, 2.1, 3.2)
        second = basic.rectangle(0.1, 1.3, 1.9, 2.2)

        subtract_results = basic.subtract(first, second)
        actual_subtract = list(subtract_results.exterior.coords)
        expected_subtract = [(1.85, 2.85), (1.85, 3.95), (2.35, 3.95), (2.35, 2.45), (1.95, 2.45), (1.95, 2.85), (1.85, 2.85)]

        self.assertEqual(len(actual_subtract), len(expected_subtract))
        for i in range(len(actual_subtract)):
            for j in range(2):
                self.assertEqual(actual_subtract[i][j], expected_subtract[i][j])

    def test_draw_basic_union(self):
        """
        Test union in basic.py
        """
        first = basic.rectangle(0.5, 1.5, 2.1, 3.2)
        second = basic.rectangle(0.1, 1.3, 1.9, 2.2)
        third = basic.rectangle(1, 1.4, 2.1, 6)

        expected_1 = [(1.85, 2.45), (2.35, 2.45), (2.35, 3.95), (1.85, 3.95), (1.85, 2.45)]
        expected_2 = [(1.85, 2.85), (1.85, 3.95), (2.35, 3.95), (2.35, 2.45), (1.95, 2.45), (1.95, 1.55), (1.85, 1.55), (1.85, 2.85), (1.85, 2.85)]
        expected_3_0 = [(1.6, 5.3), (2.6, 5.3), (2.6, 6.7), (1.6, 6.7), (1.6, 5.3)]
        expected_3_1 = [(1.95, 2.45), (1.95, 1.55), (1.85, 1.55), (1.85, 2.85), (1.85, 2.85), (1.85, 3.95), (2.35, 3.95), (2.35, 2.45), (1.95, 2.45)]

        union_results_1 = basic.union(first)
        union_results_2 = basic.union(first, second)
        union_results_3 = basic.union(first, second, third)

        actual_1 = list(union_results_1.exterior.coords)
        actual_2 = list(union_results_2.exterior.coords)

        my_elements = [[actual_1, expected_1], [actual_2, expected_2]]
        for actual, expected in my_elements:
            self.assertEqual(len(actual), len(expected))
            for i in range(len(actual)):
                for j in range(2):
                    self.assertAlmostEqualRel(actual[i][j], expected[i][j], rel_tol=1e-6)

        self.assertEqual(len(union_results_3), 2)
        actual_3_0 = list(union_results_3[0].exterior.coords)
        actual_3_1 = list(union_results_3[1].exterior.coords)

        my_elements = [[actual_3_0, expected_3_0], [actual_3_1, expected_3_1]]
        for actual, expected in my_elements:
            self.assertEqual(len(actual), len(expected))
            for i in range(len(actual)):
                for j in range(2):
                    self.assertAlmostEqualRel(actual[i][j], expected[i][j], rel_tol=1e-6)

    def test_draw_basic_flip_merge(self):
        """
        Test flip_merge in basic.py
        """
        my_line_string = LineString([(0, 0), (1, 1), (1,2), (2,2)])

        expected_1 = [(0.0, 0.0), (1.0, 1.0), (1.0, 2.0), (2.0, 2.0), (-2.0, 2.0), (-1.0, 2.0), (-1.0, 1.0), (0.0, 0.0)]
        expected_2 = [(0.0, 0.0), (1.0, 1.0), (1.0, 2.0), (2.0, 2.0), (2.0, 2.0), (7.0, 2.0), (7.0, -3.0), (12.0, -8.0)]

        actual_1 = basic.flip_merge(my_line_string)
        actual_2 = basic.flip_merge(my_line_string, xfact=-5, yfact=5, origin=(2, 2))

        my_elements = [[actual_1, expected_1], [actual_2, expected_2]]
        for actual, expected in my_elements:
            self.assertEqual(len(actual), len(expected))
            for i in range(len(actual)):
                for j in range(2):
                    self.assertAlmostEqualRel(actual[i][j], expected[i][j], rel_tol=1e-6)

    def test_draw_basic_rotate(self):
        """
        Test rotate in basic.py
        """
        expected_1 = [(0.3709223813239876, -0.08223151219433734), (0.5822315121943373, 0.37092238132398764), (0.023423053240837488, 0.3556545654351749), (0.3709223813239876, -0.08223151219433734)]
        expected_2 = [(0.2953967324042668, -0.13034665704927906), (0.5067058632746165, 0.3228072364690459), (-0.05210259567888331, 0.30753942058023315), (0.2953967324042668, -0.13034665704927906)]
        expected_3 = [(0.5284182427245603, 0.053701805333836145), (0.24719131710547426, 0.4671161450788879), (-0.025609559830034434, -0.020817950412724023), (0.5284182427245603, 0.053701805333836145)]

        poly = Polygon([(0, 0), (0.5, 0), (0.25, 0.5)])
        poly_1 = basic.rotate(poly, angle=65)
        poly_2 = basic.rotate(poly, angle=65, origin='centroid')
        poly_3 = basic.rotate(poly, angle=65, origin='centroid', use_radians=True)

        actual_1 = list(poly_1.exterior.coords)
        actual_2 = list(poly_2.exterior.coords)
        actual_3 = list(poly_3.exterior.coords)

        my_elements = [[actual_1, expected_1], [actual_2, expected_2], [actual_3, expected_3]]
        for actual, expected in my_elements:
            self.assertEqual(len(actual), len(expected))
            for i in range(len(actual)):
                for j in range(2):
                    self.assertAlmostEqualRel(actual[i][j], expected[i][j], rel_tol=1e-6)

    def test_draw_basic_translate(self):
        """
        Test translate in basic.py
        """
        poly = Polygon([(0, 0), (0.5, 0), (0.25, 0.5)])

        expected_1 = [(0.0, 0.0), (0.5, 0.0), (0.25, 0.5), (0.0, 0.0)]
        expected_2 = [(1.1, 0.0), (1.6, 0.0), (1.35, 0.5), (1.1, 0.0)]
        expected_3 = [(1.1, 2.2), (1.6, 2.2), (1.35, 2.7), (1.1, 2.2)]
        expected_4 = [(1.1, 2.2), (1.6, 2.2), (1.35, 2.7), (1.1, 2.2)]
        expected_5 = [(1.1, 2.2), (1.6, 2.2), (1.35, 2.7), (1.1, 2.2)]
        orig_poly = [(0.0, 0.0), (0.5, 0.0), (0.25, 0.5), (0.0, 0.0)]

        poly_1 = basic.translate(poly)
        poly_2 = basic.translate(poly, xoff=1.1)
        poly_3 = basic.translate(poly, xoff=1.1, yoff=2.2)
        poly_4 = basic.translate(poly, xoff=1.1, yoff=2.2, zoff=3.3)
        poly_5 = basic.translate(poly, xoff=1.1, yoff=2.2, zoff=3.3, overwrite=True)

        actual_1 = list(poly_1.exterior.coords)
        actual_2 = list(poly_2.exterior.coords)
        actual_3 = list(poly_3.exterior.coords)
        actual_4 = list(poly_4.exterior.coords)
        actual_5 = list(poly_5.exterior.coords)
        new_poly = list(poly.exterior.coords)

        my_elements = [[actual_1, expected_1], [actual_2, expected_2], [actual_3, expected_3], [actual_4, expected_4], [actual_5, expected_5], [orig_poly, new_poly]]
        for actual, expected in my_elements:
            self.assertEqual(len(actual), len(expected))
            for i in range(len(actual)):
                for j in range(2):
                    self.assertAlmostEqualRel(actual[i][j], expected[i][j], rel_tol=1e-6)

    def test_draw_basic_scale(self):
        """
        Test scale in basic.py
        """
        poly = Polygon([(0, 0), (0.5, 0), (0.25, 0.5)])

        expected_1 = [(0.0, 0.0), (0.5, 0.0), (0.25, 0.5), (0.0, 0.0)]
        expected_2 = [(-0.025, 0.0), (0.525, 0.0), (0.25, 0.5), (-0.025, 0.0)]
        expected_3 = [(-0.025, -0.3), (0.525, -0.3), (0.25, 0.8), (-0.025, -0.3)]
        expected_4 = [(-0.025, -0.3), (0.525, -0.3), (0.25, 0.8), (-0.025, -0.3)]
        expected_5 = [(-0.025, -0.3), (0.525, -0.3), (0.25, 0.8), (-0.025, -0.3)]
        orig_poly = [(0.0, 0.0), (0.5, 0.0), (0.25, 0.5), (0.0, 0.0)]

        poly_1 = basic.scale(poly)
        poly_2 = basic.scale(poly, xfact=1.1)
        poly_3 = basic.scale(poly, xfact=1.1, yfact=2.2)
        poly_4 = basic.scale(poly, xfact=1.1, yfact=2.2, zfact=3.3)
        poly_5 = basic.scale(poly, xfact=1.1, yfact=2.2, zfact=3.3, overwrite=True)

        actual_1 = list(poly_1.exterior.coords)
        actual_2 = list(poly_2.exterior.coords)
        actual_3 = list(poly_3.exterior.coords)
        actual_4 = list(poly_4.exterior.coords)
        actual_5 = list(poly_5.exterior.coords)
        new_poly = list(poly.exterior.coords)

        my_elements = [[actual_1, expected_1], [actual_2, expected_2], [actual_3, expected_3], [actual_4, expected_4], [actual_5, expected_5], [orig_poly, new_poly]]
        for actual, expected in my_elements:
            self.assertEqual(len(actual), len(expected))
            for i in range(len(actual)):
                for j in range(2):
                    self.assertAlmostEqualRel(actual[i][j], expected[i][j], rel_tol=1e-6)

    def test_draw_basic_rotate_position(self):
        """
        Test rotate_position in basic.py
        """
        poly = Polygon([(0, 0), (0.5, 0), (0.25, 0.5)])

        expected_1 = [(2.0, 5.0), (2.433012701892219, 5.25), (1.9665063509461098, 5.55801270189222), (2.0, 5.0)]
        expected_2 = [(10.839745962155611, 2.00961894323342), (11.27275866404783, 2.25961894323342), (10.806252313101721, 2.567631645125639), (10.839745962155611, 2.00961894323342)]
        expected_3 = [(10.839745962155611, 2.00961894323342), (11.27275866404783, 2.25961894323342), (10.806252313101721, 2.567631645125639), (10.839745962155611, 2.00961894323342)]
        orig_poly = [(0.0, 0.0), (0.5, 0.0), (0.25, 0.5), (0.0, 0.0)]

        poly_1 = basic.rotate_position(poly, 30, (2,5))
        poly_2 = basic.rotate_position(poly, 30, (2,5), pos_rot=(10, 15))
        poly_3 = basic.rotate_position(poly, 30, (2,5), pos_rot=(10, 15), overwrite=True)

        actual_1 = list(poly_1.exterior.coords)
        actual_2 = list(poly_2.exterior.coords)
        actual_3 = list(poly_3.exterior.coords)
        new_poly = list(poly.exterior.coords)

        my_elements = [[actual_1, expected_1], [actual_2, expected_2], [actual_3, expected_3], [orig_poly, new_poly]]
        for actual, expected in my_elements:
            self.assertEqual(len(actual), len(expected))
            for i in range(len(actual)):
                for j in range(2):
                    self.assertAlmostEqualRel(actual[i][j], expected[i][j], rel_tol=1e-6)


    #def buffer(qgeometry,
    #       distance: float,
    #       resolution=None,
    #       cap_style=CAP_STYLE.flat,
    #       join_style=JOIN_STYLE.mitre,
    #       mitre_limit=None,
    #       overwrite=False):

if __name__ == '__main__':
    unittest.main(verbosity=2)
