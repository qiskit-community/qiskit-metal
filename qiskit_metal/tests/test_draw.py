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

# pylint: disable-msg=unnecessary-pass
# pylint: disable-msg=broad-except
# pylint: disable-msg=too-many-public-methods
# pylint: disable-msg=import-error
"""Qiskit Metal unit tests analyses functionality."""

import unittest

import numpy as np

from shapely.geometry import Polygon
from shapely.geometry import LineString
from shapely.geometry import CAP_STYLE
from shapely.geometry import JOIN_STYLE

from qiskit_metal.draw import basic
from qiskit_metal.draw import utility
from qiskit_metal.draw.utility import Vector
from qiskit_metal.tests.assertions import AssertionsMixin


class TestDraw(unittest.TestCase, AssertionsMixin):
    """Unit test class."""

    def setUp(self):
        """Setup unit test."""
        pass

    def tearDown(self):
        """Tie any loose ends."""
        pass

    def test_draw_instantiate_vector(self):
        """Test instantiation of Vector class."""
        try:
            Vector
        except Exception:
            self.fail("Vector failed")

    def test_draw_basic_rectangle(self):
        """Test rectangle in basic.py."""
        polygon_actual = basic.rectangle(0.5, 1.5, 2.1, 3.2)
        polygon_expected = Polygon([[1.85, 2.45], [2.35, 2.45], [2.35, 3.95],
                                    [1.85, 3.95], [1.85, 2.45]])

        coords_actual = list(polygon_actual.exterior.coords)
        coords_expected = list(polygon_expected.exterior.coords)
        self.assertEqual(len(coords_actual), len(coords_expected))
        my_range = len(coords_actual)
        for i in range(my_range):
            for j in range(2):
                self.assertEqual(coords_actual[i][j], coords_expected[i][j])

    def test_draw_basic_is_rectangle(self):
        """Test is_rectangle in basic.py."""
        my_rectangle = basic.rectangle(0.5, 1.5, 2.1, 3.2)

        self.assertTrue(basic.is_rectangle(my_rectangle))
        self.assertFalse(basic.is_rectangle(7))

    def test_draw_basic_subtract(self):
        """Test subtract in basic.py."""
        first = basic.rectangle(0.5, 1.5, 2.1, 3.2)
        second = basic.rectangle(0.1, 1.3, 1.9, 2.2)

        subtract_results = basic.subtract(first, second)
        actual_subtract = list(subtract_results.exterior.coords)
        expected_subtract = [(1.85, 2.85), (1.85, 3.95), (2.35, 3.95),
                             (2.35, 2.45), (1.95, 2.45), (1.95, 2.85),
                             (1.85, 2.85)]

        self.assertEqual(len(actual_subtract), len(expected_subtract))

        # the shape resulting from a subtract could use as origin point any of the vertices.
        for idx, point in enumerate(expected_subtract):
            if actual_subtract[0] == point:
                offset = idx

        my_range = len(
            actual_subtract) - 1  #first and last elements are the same. Ignore.
        for i in range(my_range):
            exp_i = (i + offset) % (my_range)
            for j in range(2):
                self.assertEqual(actual_subtract[i][j],
                                 expected_subtract[exp_i][j])

    def test_draw_basic_union(self):
        """Test union in basic.py."""
        first = basic.rectangle(0.5, 1.5, 2.1, 3.2)
        second = basic.rectangle(0.1, 1.3, 1.9, 2.2)

        expected = [[(1.85, 2.45), (2.35, 2.45), (2.35, 3.95), (1.85, 3.95),
                     (1.85, 2.45)],
                    [(1.85, 2.85), (1.85, 3.95), (2.35, 3.95), (2.35, 2.45),
                     (1.95, 2.45), (1.95, 1.55), (1.85, 1.55), (1.85, 2.85),
                     (1.85, 2.85)]]

        union_results_1 = basic.union(first)
        union_results_2 = basic.union(first, second)

        actual = [
            list(union_results_1.exterior.coords),
            list(union_results_2.exterior.coords)
        ]

        for x in range(2):
            self.assertEqual(len(actual[x]), len(expected[x]))

            # the shape resulting from a union could use as origin point any of the vertices.
            for idx, point in enumerate(expected[x]):
                if actual[x][0] == point:
                    offset = idx

            my_range = len(actual[x]) - 1  #last element repeats first. Ignore.
            for i in range(my_range):
                exp_i = (i + offset) % (my_range)
                for j in range(2):
                    self.assertAlmostEqualRel(actual[x][i][j],
                                              expected[x][exp_i][j],
                                              rel_tol=1e-3)

    def test_draw_basic_flip_merge(self):
        """Test flip_merge in basic.py."""
        my_line_string = LineString([(0, 0), (1, 1), (1, 2), (2, 2)])

        expected = [[(0.0, 0.0), (1.0, 1.0), (1.0, 2.0), (2.0, 2.0),
                     (-2.0, 2.0), (-1.0, 2.0), (-1.0, 1.0), (0.0, 0.0)],
                    [(0.0, 0.0), (1.0, 1.0), (1.0, 2.0), (2.0, 2.0), (2.0, 2.0),
                     (7.0, 2.0), (7.0, -3.0), (12.0, -8.0)]]

        flip_results_1 = basic.flip_merge(my_line_string)
        flip_results_2 = basic.flip_merge(my_line_string,
                                          xfact=-5,
                                          yfact=5,
                                          origin=(2, 2))
        actual = [flip_results_1, flip_results_2]

        for x in range(2):
            self.assertEqual(len(actual[x]), len(expected[x]))
            for i in range(len(actual[x])):
                for j in range(2):
                    self.assertAlmostEqualRel(actual[x][i][j],
                                              expected[x][i][j],
                                              rel_tol=1e-3)

    def test_draw_basic_rotate(self):
        """Test rotate in basic.py."""
        poly = Polygon([(0, 0), (0.5, 0), (0.25, 0.5)])

        expected = [[(0.3709223813239876, -0.08223151219433734),
                     (0.5822315121943373, 0.37092238132398764),
                     (0.023423053240837488, 0.3556545654351749),
                     (0.3709223813239876, -0.08223151219433734)],
                    [(0.2953967324042668, -0.13034665704927906),
                     (0.5067058632746165, 0.3228072364690459),
                     (-0.05210259567888331, 0.30753942058023315),
                     (0.2953967324042668, -0.13034665704927906)],
                    [(0.5284182427245603, 0.053701805333836145),
                     (0.24719131710547426, 0.4671161450788879),
                     (-0.025609559830034434, -0.020817950412724023),
                     (0.5284182427245603, 0.053701805333836145)]]

        poly_1 = basic.rotate(poly, angle=65)
        poly_2 = basic.rotate(poly, angle=65, origin='centroid')
        poly_3 = basic.rotate(poly,
                              angle=65,
                              origin='centroid',
                              use_radians=True)

        actual = [
            list(poly_1.exterior.coords),
            list(poly_2.exterior.coords),
            list(poly_3.exterior.coords)
        ]

        for x in range(3):
            self.assertEqual(len(actual[x]), len(expected[x]))
            for i in range(len(actual[x])):
                for j in range(2):
                    self.assertAlmostEqualRel(actual[x][i][j],
                                              expected[x][i][j],
                                              rel_tol=1e-3)

    def test_draw_basic_translate(self):
        """Test translate in basic.py."""
        poly = Polygon([(0, 0), (0.5, 0), (0.25, 0.5)])

        expected = [[(0.0, 0.0), (0.5, 0.0), (0.25, 0.5), (0.0, 0.0)],
                    [(1.1, 0.0), (1.6, 0.0), (1.35, 0.5), (1.1, 0.0)],
                    [(1.1, 2.2), (1.6, 2.2), (1.35, 2.7), (1.1, 2.2)],
                    [(1.1, 2.2), (1.6, 2.2), (1.35, 2.7), (1.1, 2.2)],
                    [(1.1, 2.2), (1.6, 2.2), (1.35, 2.7), (1.1, 2.2)]]

        poly_1 = basic.translate(poly)
        poly_2 = basic.translate(poly, xoff=1.1)
        poly_3 = basic.translate(poly, xoff=1.1, yoff=2.2)
        poly_4 = basic.translate(poly, xoff=1.1, yoff=2.2, zoff=3.3)
        poly_5 = basic.translate(poly,
                                 xoff=1.1,
                                 yoff=2.2,
                                 zoff=3.3,
                                 overwrite=True)

        actual = [
            list(poly_1.exterior.coords),
            list(poly_2.exterior.coords),
            list(poly_3.exterior.coords),
            list(poly_4.exterior.coords),
            list(poly_5.exterior.coords)
        ]

        for x in range(5):
            self.assertEqual(len(actual[x]), len(expected[x]))
            for i in range(len(actual[x])):
                for j in range(2):
                    self.assertAlmostEqualRel(actual[x][i][j],
                                              expected[x][i][j],
                                              rel_tol=1e-3)

    def test_draw_basic_scale(self):
        """Test scale in basic.py."""
        poly = Polygon([(0, 0), (0.5, 0), (0.25, 0.5)])

        expected = [[(0.0, 0.0), (0.5, 0.0), (0.25, 0.5), (0.0, 0.0)],
                    [(-0.025, 0.0), (0.525, 0.0), (0.25, 0.5), (-0.025, 0.0)],
                    [(-0.025, -0.3), (0.525, -0.3), (0.25, 0.8),
                     (-0.025, -0.3)],
                    [(-0.025, -0.3), (0.525, -0.3), (0.25, 0.8),
                     (-0.025, -0.3)],
                    [(-0.025, -0.3), (0.525, -0.3), (0.25, 0.8),
                     (-0.025, -0.3)]]

        poly_1 = basic.scale(poly)
        poly_2 = basic.scale(poly, xfact=1.1)
        poly_3 = basic.scale(poly, xfact=1.1, yfact=2.2)
        poly_4 = basic.scale(poly, xfact=1.1, yfact=2.2, zfact=3.3)
        poly_5 = basic.scale(poly,
                             xfact=1.1,
                             yfact=2.2,
                             zfact=3.3,
                             overwrite=True)

        actual = [
            list(poly_1.exterior.coords),
            list(poly_2.exterior.coords),
            list(poly_3.exterior.coords),
            list(poly_4.exterior.coords),
            list(poly_5.exterior.coords)
        ]

        for x in range(5):
            self.assertEqual(len(actual[x]), len(expected[x]))
            for i in range(len(actual[x])):
                for j in range(2):
                    self.assertAlmostEqualRel(actual[x][i][j],
                                              expected[x][i][j],
                                              rel_tol=1e-3)

    def test_draw_basic_rotate_position(self):
        """Test rotate_position in basic.py."""
        poly = Polygon([(0, 0), (0.5, 0), (0.25, 0.5)])

        expected = [[(2.0, 5.0), (2.433012701892219, 5.25),
                     (1.9665063509461098, 5.55801270189222), (2.0, 5.0)],
                    [(10.839745962155611, 2.00961894323342),
                     (11.27275866404783, 2.25961894323342),
                     (10.806252313101721, 2.567631645125639),
                     (10.839745962155611, 2.00961894323342)],
                    [(10.839745962155611, 2.00961894323342),
                     (11.27275866404783, 2.25961894323342),
                     (10.806252313101721, 2.567631645125639),
                     (10.839745962155611, 2.00961894323342)]]

        poly_1 = basic.rotate_position(poly, 30, (2, 5))
        poly_2 = basic.rotate_position(poly, 30, (2, 5), pos_rot=(10, 15))
        poly_3 = basic.rotate_position(poly,
                                       30, (2, 5),
                                       pos_rot=(10, 15),
                                       overwrite=True)

        actual = [
            list(poly_1.exterior.coords),
            list(poly_2.exterior.coords),
            list(poly_3.exterior.coords)
        ]

        for x in range(2):
            self.assertEqual(len(actual[x]), len(expected[x]))
            for i in range(len(actual[x])):
                for j in range(2):
                    self.assertAlmostEqualRel(actual[x][i][j],
                                              expected[x][i][j],
                                              rel_tol=1e-3)

    def test_draw_basic_buffer(self):
        """Test buffer in basic.py."""
        poly = Polygon([(0, 0), (0.5, 0), (0.25, 0.5)])

        expected = [[(-0.16180339887498948, -0.1), (0.25, 0.7236067977499789),
                     (0.6618033988749895, -0.1), (-0.16180339887498948, -0.1)],
                    [(-0.16180339887498948, -0.1), (0.25, 0.7236067977499789),
                     (0.6618033988749895, -0.1), (-0.16180339887498948, -0.1)],
                    [(-0.16180339887498948, -0.1), (0.25, 0.7236067977499789),
                     (0.6618033988749895, -0.1), (-0.16180339887498948, -0.1)],
                    [(-0.08944271909999159, 0.044721359549995794),
                     (0.16055728090000843, 0.5447213595499958),
                     (0.3394427190999916, 0.5447213595499958),
                     (0.5894427190999916, 0.044721359549995794), (0.5, -0.1),
                     (0.0, -0.1), (-0.08944271909999159, 0.044721359549995794)],
                    [(-0.06980083939497377, 0.05587673960663148),
                     (0.16341640786499884, 0.5300000000000004),
                     (0.3365835921350014, 0.5299999999999997),
                     (0.5698008393949741, 0.05587673960663103),
                     (0.4812382091061482, -0.08742060633377921),
                     (0.018761790893851275, -0.08742060633377935),
                     (-0.06980083939497377, 0.05587673960663148)]]

        poly_1 = basic.buffer(poly, 0.1)
        poly_2 = basic.buffer(poly, 0.1, resolution=2)
        poly_3 = basic.buffer(poly,
                              0.1,
                              resolution=2,
                              cap_style=CAP_STYLE.round)
        poly_4 = basic.buffer(poly,
                              0.1,
                              resolution=2,
                              cap_style=CAP_STYLE.round,
                              join_style=JOIN_STYLE.bevel)
        poly_5 = basic.buffer(poly, 0.1, resolution=2, mitre_limit=0.3)

        actual = [
            list(poly_1.exterior.coords),
            list(poly_2.exterior.coords),
            list(poly_3.exterior.coords),
            list(poly_4.exterior.coords),
            list(poly_5.exterior.coords)
        ]

        for x in range(5):
            self.assertEqual(len(actual[x]), len(expected[x]))
            for i in range(len(actual[x])):
                for j in range(2):
                    self.assertAlmostEqualRel(actual[x][i][j],
                                              expected[x][i][j],
                                              rel_tol=1e-3)

    def test_draw_utility_get_poly_pts(self):
        """Test get_poly_pts in utility.py."""
        poly = Polygon([(0, 0), (0.5, 0), (0.25, 0.5)])

        expected_list = [[0., 0.], [0.5, 0.], [0.25, 0.5]]
        expected = np.array(expected_list)

        actual = utility.get_poly_pts(poly)

        self.assertEqual(len(actual), len(expected))
        for i in range(3):
            for j in range(2):
                self.assertAlmostEqualRel(actual[i][j],
                                          expected[i][j],
                                          rel_tol=1e-3)

    def test_draw_utility_get_all_geoms(self):
        """Test get_all_geoms in utility.py."""
        poly = Polygon([(0, 0), (0.5, 0), (0.25, 0.5)])

        expected = [(0.0, 0.0), (0.5, 0.0), (0.25, 0.5), (0.0, 0.0)]

        actual_raw = utility.get_all_geoms(poly)
        actual = list(actual_raw.exterior.coords)

        self.assertEqual(len(actual), len(expected))
        my_range = len(actual)
        for i in range(my_range):
            for j in range(2):
                self.assertAlmostEqualRel(actual[i][j],
                                          expected[i][j],
                                          rel_tol=1e-3)

    def test_draw_utility_flatten_all_filter(self):
        """Test flatten_all_filter in utility.py."""
        poly_1 = Polygon([(0, 0), (0.5, 0), (0.25, 0.5)])
        poly_2 = Polygon([(1, 1), (1.5, 1), (1.25, 1.5)])
        poly_3 = Polygon([(2, 2), (2.5, 2), (2.25, 2.5)])
        my_dict = {'first': poly_1, 'second': poly_2, 'third': poly_3}

        expected = [[(0.0, 0.0), (0.5, 0.0), (0.25, 0.5), (0.0, 0.0)],
                    [(1.0, 1.0), (1.5, 1.0), (1.25, 1.5), (1.0, 1.0)],
                    [(2.0, 2.0), (2.5, 2.0), (2.25, 2.5), (2.0, 2.0)]]

        result_raw = utility.flatten_all_filter(my_dict)
        actual = []
        for x in range(3):
            actual.append(list(result_raw[x].exterior.coords))

        self.assertEqual(len(actual), len(expected))
        my_range = len(actual)
        for i in range(my_range):
            for j in range(2):
                self.assertAlmostEqualRel(actual[i][j],
                                          expected[i][j],
                                          rel_tol=1e-3)

    def test_draw_utility_check_duplicate_list(self):
        """Test check_duplicate_list in utility.py."""
        list_1 = [1, 2, 3, 4, 5]
        list_2 = [1, 2, 3, 1, 5]

        self.assertFalse(utility.check_duplicate_list(list_1))
        self.assertTrue(utility.check_duplicate_list(list_2))

    def test_draw_utility_array_chop(self):
        """Test array_chop in utility.py."""
        my_list = [0, 1, 0.02, 2, -1, 3, 0.11, 4, 5]

        expected_list = [0., 0., 0.02, 2., -1., 3., 0.11, 4., 5.]
        expected = np.array(expected_list)

        actual = utility.array_chop(my_list, zero=1)

        self.assertEqual(len(actual), len(expected))
        my_range = len(actual)
        for i in range(my_range):
            self.assertAlmostEqualRel(actual[i], expected[i], rel_tol=1e-3)

    def test_draw_utility_remove_colinear_pts(self):
        """Test remove_colinear_pts in utility.py."""
        points_list = [[0, 0], [
            1,
            1,
        ], [
            1,
            1,
        ], [1.5, 1.5], [2, 2]]
        points = np.array(points_list)

        expected_list = [[0, 0], [1, 1], [2, 2]]
        expected = np.array(expected_list)

        actual = utility.remove_colinear_pts(points)

        self.assertEqual(len(actual), len(expected))
        my_range = len(actual)
        for i in range(my_range):
            for j in range(2):
                self.assertAlmostEqualRel(actual[i][j],
                                          expected[i][j],
                                          rel_tol=1e-3)

    def test_draw_utility_intersect(self):
        """Test intersect in utility.py."""
        self.assertEqual(utility.intersect(0, 0, 2, 2, 1, 1), 1)
        self.assertEqual(utility.intersect(0, 0, 2, 2, 3, 3), 0)

    def test_draw_utility_vec_unit_planar(self):
        """Test vec_unit_planar in utility.py."""
        # error
        points_list = [[0, 0], [0, 1], [1.5, 1.5], [1, 1.5]]
        points = np.array(points_list)
        with self.assertRaises(Exception):
            actual = utility.vec_unit_planar(points)

        # 2d
        points_list = [[0, 0], [1, 1]]
        points = np.array(points_list)
        expected_list = [[0., 0.], [0.70710678, 0.70710678]]
        expected = np.array(expected_list)
        actual = utility.vec_unit_planar(points)
        self.assertEqual(len(actual), len(expected))
        my_range = len(actual)
        for i in range(my_range):
            for j in range(2):
                self.assertAlmostEqualRel(actual[i][j],
                                          expected[i][j],
                                          rel_tol=1e-3)

        # 3d
        points_list = [[0, 0, 5], [1, 1, 10]]
        points = np.array(points_list)
        expected_list = [[0., 0., 0.44367825],
                         [0.08873565, 0.08873565, 0.88735651]]
        expected = np.array(expected_list)
        actual = utility.vec_unit_planar(points)
        self.assertEqual(len(actual), len(expected))
        my_range = len(actual)
        for i in range(my_range):
            for j in range(3):
                self.assertAlmostEqualRel(actual[i][j],
                                          expected[i][j],
                                          rel_tol=1e-3)

    def test_draw_vector_normal_z(self):
        """Test that normal_z in Vector class was not accidentally changed."""
        expected_list = [0, 0, 1]
        expected = np.array(expected_list)
        actual = Vector.normal_z

        self.assertEqual(len(actual), len(expected))
        for i in range(3):
            self.assertAlmostEqualRel(actual[i], expected[i], rel_tol=1e-3)

    def test_draw_vector_rotate_around_point(self):
        """Test rotate_around_point in the Vector class in utility.py."""
        vector = Vector()

        expected = [(2.130314698073308, -0.6795287243176937),
                    (-1.1764850602505073, 1.9015475021695778),
                    (1.5611824021515244, 6.655591972503418),
                    (4.125841082615048, 0.3966454487621853)]

        actual = []
        actual.append(vector.rotate_around_point([1, 2], radians=30))
        actual.append(vector.rotate_around_point([1, 2], radians=45))
        actual.append(
            vector.rotate_around_point([1, 2], radians=30, origin=(4, 4)))
        actual.append(
            vector.rotate_around_point([1, 2], radians=45, origin=(4, 4)))

        for i in range(4):
            for j in range(2):
                self.assertAlmostEqualRel(actual[i][j],
                                          expected[i][j],
                                          rel_tol=1e-3)

    def test_draw_vector_rotate(self):
        """Test rotate in the Vector class in utility.py."""
        vector = Vector()

        expected = [(2.130314698073308, -0.6795287243176937),
                    (-1.1764850602505073, 1.9015475021695778)]

        actual = []
        actual.append(vector.rotate_around_point([1, 2], radians=30))
        actual.append(vector.rotate_around_point([1, 2], radians=45))

        for i in range(2):
            for j in range(2):
                self.assertAlmostEqualRel(actual[i][j],
                                          expected[i][j],
                                          rel_tol=1e-3)

    def test_draw_vector_angle_between(self):
        """Test angle_between in Vector class in utility.py."""
        vector = Vector()

        expected = 0.6435011087932843
        actual = vector.angle_between([0, 10], [15, 20])
        self.assertAlmostEqualRel(actual, expected, rel_tol=1e-3)

    def test_draw_vector_add_z(self):
        """Test add_z in Vector class in utility.py."""
        vector = Vector()

        expected = [[10.0, 15.0, 0.0], [22.0, 7.0, 2.5]]

        actual = []
        actual.append(list(vector.add_z([10, 15])))
        actual.append(list(vector.add_z([22, 7], 2.5)))

        for i in range(2):
            for j in range(3):
                self.assertAlmostEqualRel(actual[i][j],
                                          expected[i][j],
                                          rel_tol=1e-3)

    def test_draw_normed(self):
        """Test functionality of normed in utility.py."""
        vector = Vector()

        result = vector.normed([12, 16])
        self.assertEqual(result[0], 0.6)
        self.assertEqual(result[1], 0.8)

    def test_draw_vector_norm(self):
        """Test norm in Vector class in utility.py."""
        vector = Vector()

        expected = 18.138357147217054
        actual = vector.norm([10, 15, 2])
        self.assertAlmostEqualRel(actual, expected, rel_tol=1e-3)

    def test_draw_vector_are_same(self):
        """Test are_same in Vector class in utility.py."""
        points_list_1 = [10., 15., 2.]
        points_list_2 = [10., 15., 2.]
        points_list_3 = [20., 25., 30.]

        vect_1 = np.array(points_list_1)
        vect_2 = np.array(points_list_2)
        vect_3 = np.array(points_list_3)

        self.assertEqual(Vector.are_same(vect_1, vect_2), True)
        self.assertEqual(Vector.are_same(vect_1, vect_3), False)

    def test_draw_vector_is_zero(self):
        """Test is_zero in Vector class in utility.py."""
        vector = Vector()

        points_list_1 = [10., 15., 2.]
        points_list_2 = [0, 0, 0]

        vect_1 = np.array(points_list_1)
        vect_2 = np.array(points_list_2)

        self.assertFalse(vector.is_zero(vect_1))
        self.assertTrue(vector.is_zero(vect_2))

    def test_draw_vector_two_points_described(self):
        """Test two_points_described in Vector class in utility.py."""
        vector = Vector()

        expected = ([-8.0, 15.0], [-0.47058823529411764, 0.8823529411764706],
                    [-0.88235294118, -0.47058823529])

        points_list_1 = [10., 15.]
        points_list_2 = [2, 30]

        vect_1 = np.array(points_list_1)
        vect_2 = np.array(points_list_2)

        my_list = [vect_1, vect_2]

        actual = vector.two_points_described(my_list)
        actual = tuple(map(list, actual))

        for i in range(3):
            for j in range(2):
                self.assertAlmostEqualRel(actual[i][j],
                                          expected[i][j],
                                          rel_tol=1e-3)

    def test_draw_vector_snap_unit_vector(self):
        """Test snap_unit_vector in Vector class in utility.py."""
        vector = Vector()

        expected = ([0, 1], [1, 0])

        points_list_1 = [10., 15.]
        vect = np.array(points_list_1)

        actual = []
        actual.append(vector.snap_unit_vector(vect))
        actual.append(vector.snap_unit_vector(vect, flip=True))
        actual = tuple(map(list, actual))

        for i in range(2):
            for j in range(2):
                self.assertAlmostEqualRel(actual[i][j],
                                          expected[i][j],
                                          rel_tol=1e-3)

    def test_draw_get_distance(self):
        """Test the functionality of get_distance in utility.py."""
        vector = Vector()

        expected = [1.41, 24.187]

        actual = []
        actual.append(vector.get_distance((1, 1), (2, 2), precision=2))
        actual.append(vector.get_distance((10, 15), (22, -6), precision=3))

        for i in range(2):
            self.assertAlmostEqualRel(actual[i], expected[i], rel_tol=1e-3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
