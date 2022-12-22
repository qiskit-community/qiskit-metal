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
# pylint: disable-msg=protected-access
# pylint: disable-msg=broad-except
# pylint: disable-msg=import-error
"""Qiskit Metal unit tests analyses functionality."""

import unittest
import numpy as np
from typing import Union

from qiskit_metal.toolbox_metal import about
from qiskit_metal.toolbox_metal import parsing
from qiskit_metal.toolbox_metal import math_and_overrides
from qiskit_metal.toolbox_metal import bounds_for_path_and_poly_tables
from qiskit_metal.toolbox_metal.bounds_for_path_and_poly_tables import BoundsForPathAndPolyTables
from qiskit_metal.toolbox_metal.layer_stack_handler import LayerStackHandler
from qiskit_metal.toolbox_metal.exceptions import QiskitMetalExceptions
from qiskit_metal.toolbox_metal.exceptions import QiskitMetalDesignError
from qiskit_metal.toolbox_metal.exceptions import IncorrectQtException
from qiskit_metal.toolbox_metal.exceptions import QLibraryGUIException
from qiskit_metal.toolbox_metal.exceptions import InputError
from qiskit_metal.tests.assertions import AssertionsMixin
from qiskit_metal.qlibrary.qubits.transmon_concentric import TransmonConcentric
from qiskit_metal.designs.design_multiplanar import MultiPlanar
from qiskit_metal.qlibrary.qubits.transmon_pocket_6 import TransmonPocket6
from qiskit_metal.tests.test_data.quad_coupler import QuadCoupler


class TestToolboxMetal(unittest.TestCase, AssertionsMixin):
    """Unit test class."""

    def setUp(self):
        """Setup unit test."""
        pass

    def tearDown(self):
        """Tie any loose ends."""
        math_and_overrides.set_decimal_precision(10)

    def test_toolbox_metal_instantiation_qiskit_metal_exceptions(self):
        """Test instantiation of QiskitMetalExceptions."""
        try:
            QiskitMetalExceptions("test message")
        except Exception:
            self.fail("QiskitMetalExceptions failed.")

    def test_toolbox_metal_instantiation_qiskit_metal_design_error(self):
        """Test instantiation of QiskitMetalDesignError."""
        try:
            QiskitMetalDesignError("test message")
        except Exception:
            self.fail("QiskitMetalDesignError failed.")

    def test_toolbox_metal_instantiation_incorrect_qt_exception(self):
        """Test instantiation of IncorrectQtException."""
        try:
            IncorrectQtException("test message")
        except Exception:
            self.fail("IncorrectQtException failed.")

    def test_toolbox_metal_instantiation_qlibrary_gui_exception(self):
        """Test instantiation of QLibraryGUIException."""
        try:
            QLibraryGUIException("test message")
        except Exception:
            self.fail("QLibraryGUIException failed.")

    def test_toolbox_metal_instantiation_input_error(self):
        """Test instantiation of InputError."""
        try:
            InputError("test message")
        except Exception:
            self.fail("InputError failed.")

    def test_toolbox_metal_about(self):
        """Test that about in about.py produces about text without any
        errors."""
        try:
            about.about()
        except Exception:
            self.fail("about() failed")

    def test_toolbox_metal_open_docs(self):
        """Test that open_docs in about.py opens qiskit_metal documentation in HTML without any
        errors."""
        try:
            about.open_docs()
        except Exception:
            self.fail("open_docs() failed")

    def test_toolbox_metal_orient_me(self):
        """Test that orient_me in about.py produces detailed information about the user without any
        errors."""
        try:
            about.orient_me(True)
        except Exception:
            self.fail("orient_me() failed")
        try:
            about.orient_me(False)
        except Exception:
            self.fail("orient_me() failed")

    def test_toolbox_metal_get_platform_info(self):
        """Test that get_platform_info in about.py returns a string with the platform information without any errors."""
        try:
            return about.get_platform_info()
        except Exception:
            self.fail("get_platform_info() failed")

    # pylint: disable-msg=unused-variable
    def test_toolbox_metal_parsing_true_str(self):
        """Test that TRUE_STR in parsing.py has not accidentally changed."""
        expected = [
            'True', 'true', 'TRUE', True, '1', 't', 'y', 'Y', 'YES', 'yes',
            'yeah', 1, 1.0
        ]
        actual = parsing.TRUE_STR

        self.assertEqual(len(actual), len(expected))

        for x, _ in enumerate(expected):
            self.assertTrue(_ in actual)

    def test_toolbox_metal_is_true(self):
        """Test is_true in toolbox_metal.py."""
        self.assertTrue(parsing.is_true('true'))
        self.assertTrue(parsing.is_true('True'))
        self.assertTrue(parsing.is_true('TRUE'))
        self.assertTrue(parsing.is_true('1'))
        self.assertTrue(parsing.is_true('t'))
        self.assertTrue(parsing.is_true('y'))
        self.assertTrue(parsing.is_true('Y'))
        self.assertTrue(parsing.is_true('YES'))
        self.assertTrue(parsing.is_true('yes'))
        self.assertTrue(parsing.is_true('yeah'))
        self.assertTrue(parsing.is_true(True))
        self.assertTrue(parsing.is_true(1))
        self.assertTrue(parsing.is_true(1.0))

        self.assertFalse(parsing.is_true('false'))
        self.assertFalse(parsing.is_true('False'))
        self.assertFalse(parsing.is_true('FALSE'))
        self.assertFalse(parsing.is_true('0'))
        self.assertFalse(parsing.is_true('f'))
        self.assertFalse(parsing.is_true(False))
        self.assertFalse(parsing.is_true(78))
        self.assertFalse(parsing.is_true('gibberish'))
        self.assertFalse(parsing.is_true({'key': 'val'}))

    def test_toolbox_metal_parse_string_to_float(self):
        """Test _parse_string_to_float in toolbox_metal.py."""
        self.assertAlmostEqualRel(parsing._parse_string_to_float('1um'),
                                  0.001,
                                  rel_tol=1e-3)
        self.assertAlmostEqualRel(parsing._parse_string_to_float('2mm'),
                                  2,
                                  rel_tol=1e-3)
        self.assertAlmostEqualRel(parsing._parse_string_to_float('3m'),
                                  3000.0,
                                  rel_tol=1e-3)
        self.assertAlmostEqualRel(parsing._parse_string_to_float('4km'),
                                  4000000.0,
                                  rel_tol=1e-3)
        self.assertAlmostEqualRel(parsing._parse_string_to_float('5cm'),
                                  50.0,
                                  rel_tol=1e-3)
        self.assertAlmostEqualRel(parsing._parse_string_to_float('6mm'),
                                  6,
                                  rel_tol=1e-3)
        self.assertAlmostEqualRel(parsing._parse_string_to_float('2 mile'),
                                  3218688.0,
                                  rel_tol=1e-3)
        self.assertAlmostEqualRel(parsing._parse_string_to_float('3 yard'),
                                  2743.2,
                                  rel_tol=1e-3)
        self.assertAlmostEqualRel(parsing._parse_string_to_float('4 inch'),
                                  101.6,
                                  rel_tol=1e-3)

        self.assertEqual(parsing._parse_string_to_float('not-a-number'),
                         'not-a-number')
        self.assertEqual(parsing._parse_string_to_float(12), 12)
        self.assertEqual(parsing._parse_string_to_float('12.2.3'), '12.2.3')

    def test_toolbox_metal_is_variable_name(self):
        """Test is_variable_name in toolbox_metal.py."""
        self.assertTrue(parsing.is_variable_name('ok'))
        self.assertTrue(parsing.is_variable_name('still_ok'))
        self.assertTrue(parsing.is_variable_name('EXPAT'))
        self.assertTrue(parsing.is_variable_name('for'))
        self.assertTrue(parsing.is_variable_name('CamelCase'))

        self.assertFalse(parsing.is_variable_name('1_fix'))
        self.assertFalse(parsing.is_variable_name('12'))

    def test_toolbox_metal_is_for_ast_eval(self):
        """Test is_for_ast_eval in toolbox_metal.py."""
        self.assertTrue(parsing.is_for_ast_eval('[1, 2, 3]'))
        self.assertTrue(parsing.is_for_ast_eval('[[1, 2], [3, 4]]'))
        self.assertTrue(parsing.is_for_ast_eval('{1, 2}'))
        self.assertTrue(parsing.is_for_ast_eval('[{1, 2}]'))
        self.assertTrue(parsing.is_for_ast_eval('[{1, 2}, [3, 4]]'))
        self.assertTrue(parsing.is_for_ast_eval('[{1, 2}, {3, 4}]'))

        self.assertFalse(parsing.is_for_ast_eval('text'))
        self.assertFalse(parsing.is_for_ast_eval('12'))
        self.assertFalse(parsing.is_for_ast_eval('[1, 2}'))

    def test_toolbox_metal_is_numeric_possible(self):
        """Test is_numeric_possible in toolbox_metal.py."""
        self.assertTrue(parsing.is_numeric_possible('123'))
        self.assertTrue(parsing.is_numeric_possible('12mm'))
        self.assertTrue(parsing.is_numeric_possible('123.456'))
        self.assertTrue(parsing.is_numeric_possible('127.0.0.1'))
        self.assertTrue(parsing.is_numeric_possible('12.2um'))
        self.assertTrue(parsing.is_numeric_possible('-8um'))
        self.assertTrue(parsing.is_numeric_possible('+8um'))

        self.assertFalse(parsing.is_numeric_possible('abc'))
        self.assertFalse(parsing.is_numeric_possible('mm12'))
        self.assertFalse(parsing.is_numeric_possible('explode'))

    def test_toolbox_metal_parse_value(self):
        """Test parse_value in toolbox_metal.py."""
        var_dict = {'data_a': '4 miles', 'data_b': '1um'}

        self.assertAlmostEqualRel(parsing.parse_value('1 meter', var_dict),
                                  1000.0,
                                  rel_tol=1e-3)
        self.assertAlmostEqualRel(parsing.parse_value('2 um', var_dict),
                                  0.002,
                                  rel_tol=1e-3)
        self.assertAlmostEqualRel(parsing.parse_value('3 miles', var_dict),
                                  4828032.0,
                                  rel_tol=1e-3)
        self.assertAlmostEqualRel(parsing.parse_value('4 feet', var_dict),
                                  1219.1999999999998,
                                  rel_tol=1e-3)
        self.assertAlmostEqualRel(parsing.parse_value('5 km', var_dict),
                                  5000000.0,
                                  rel_tol=1e-3)
        self.assertAlmostEqualRel(parsing.parse_value('6 pm', var_dict),
                                  6.000000000000001e-09,
                                  rel_tol=1e-10)
        self.assertAlmostEqualRel(parsing.parse_value('-12 inches', var_dict),
                                  -304.79999999999995,
                                  rel_tol=1e-3)
        self.assertAlmostEqualRel(parsing.parse_value('data_a', var_dict),
                                  6437376.0,
                                  rel_tol=1e-3)
        self.assertAlmostEqualRel(parsing.parse_value('data_b', var_dict),
                                  0.001,
                                  rel_tol=1e-3)
        self.assertAlmostEqualRel(parsing.parse_value('1 um', None),
                                  0.001,
                                  rel_tol=1e-3)
        self.assertAlmostEqualRel(parsing.parse_value('1 um', 'None'),
                                  0.001,
                                  rel_tol=1e-3)

    def test_toolbox_metal_parse_options(self):
        """Test parse_options in toolbox_metal.py."""
        dict_1 = {'data_a': '2mm', 'data_b': '1um'}
        dict_2 = {
            'data_a': '20mm',
            'data_b': '15um',
            'data_c': '4 miles',
            'data_d': '2 mm'
        }

        expected = [[2], [0.001], [20, 0.015, 6437376.0, 2]]

        actual = []
        actual.append(parsing.parse_options(dict_1, 'data_a'))
        actual.append(parsing.parse_options(dict_1, 'data_b'))
        actual.append(
            parsing.parse_options(dict_2, 'data_a,data_b,data_c,data_d',
                                  dict_1))

        for x in range(3):
            self.assertEqual(len(actual[x]), len(expected[x]))
            my_range = len(actual[x])
            for i in range(my_range):
                self.assertAlmostEqualRel(actual[x][i],
                                          expected[x][i],
                                          rel_tol=1e-3)

    def test_toolbox_metal_extract_value_unit(self):
        """Test functionality of extract_value_unit in toolbox_metal.py."""
        self.assertEqual(parsing.extract_value_unit("200mm", "mm"), 200.0)
        self.assertEqual(parsing.extract_value_unit("20.5", "units"), 20.5)

    def test_toolbox_metal_fix_units(self):
        """Test functionality of fix_units in toolbox_metal.py."""
        self.assertIsInstance(parsing.fix_units(2.5, "mm"), str)
        self.assertEqual(parsing.fix_units(10.5, None), "10.5mm")

    def test_toolbox_metal_parse_entry(self):
        """Test functionality of parse_entry in toolbox_metal.py."""
        self.assertIsInstance(parsing.parse_entry([2, "two"]), list)
        self.assertEqual(parsing.parse_entry(5.5), 5.5)
        self.assertIsInstance(parsing.parse_entry("test"), str)

    def test_toolbox_metal_parse_units(self):
        """Test functionality of parse_units in toolbox_metal.py."""
        self.assertEqual(parsing.parse_units(8), 0.008)
        self.assertEqual(parsing.parse_units("two"), "two")
        self.assertEqual(parsing.parse_units([2, 3.5, 5]),
                         [0.002, 0.0035, 0.005])

    def test_toolbox_metal_set_decimal_precision(self):
        """Test functionality of set_decimal_precision in toolbox_metal.py."""
        self.assertEqual(math_and_overrides.DECIMAL_PRECISION, 10)
        math_and_overrides.set_decimal_precision(15)
        self.assertEqual(math_and_overrides.DECIMAL_PRECISION, 15)

    def test_toolbox_metal_dot(self):
        """Test functionality of dot in toolbox_metal.py."""
        math_and_overrides.set_decimal_precision(3)
        my_array_1 = np.array([3, 4])
        my_array_2 = np.array([12, 14])
        self.assertEqual(math_and_overrides.dot(my_array_1, my_array_2), 92)

    def test_toolbox_metal_round(self):
        """Test functionality of round in toolbox_metal.py."""
        math_and_overrides.set_decimal_precision(2)
        self.assertEqual(math_and_overrides.round(12.349), 12.35)

    def test_toolbox_metal_cross(self):
        """Test functionality of cross in toolbox_metal.py."""
        math_and_overrides.set_decimal_precision(3)
        my_array_1 = np.array([3, 4])
        my_array_2 = np.array([12, 14])
        self.assertEqual(math_and_overrides.cross(my_array_1, my_array_2), -6)

    def test_toolbox_metal_aligned_pts(self):
        """Test functionality of aligned_pts in toolbox_metal.py."""
        self.assertTrue(math_and_overrides.aligned_pts([0, 1, 2]))
        self.assertFalse(math_and_overrides.aligned_pts([7, 1, 2]))

    def test_toolbox_metal_determine_larger_box(self):
        """Test functionality of determine_larger_box in toolbox_metal.py."""
        self.assertEqual(
            bounds_for_path_and_poly_tables.determine_larger_box(
                0.0, 0.0, 11.0, 11.0, (0.0, 0.0, 10.0, 10.0)),
            (0.0, 0.0, 10.0, 10.0))

    def test_toolbox_metal_get_bounds_of_path_and_poly_tables(self):
        """Test functionality of get_bounds_of_path_and_poly_tables in toolbox_metal.py"""
        ls_file_path = ("./qiskit_metal/tests/test_data/planar_chip.txt")
        multiplanar_design = MultiPlanar(metadata={},
                                         overwrite_enabled=True,
                                         layer_stack_filename=ls_file_path)
        conn_pads = dict(connection_pads=dict(coup1=dict(loc_W=-1, loc_H=1),
                                              coup2=dict(loc_W=1, loc_H=1)))
        q1 = TransmonPocket6(multiplanar_design,
                             "Q1",
                             options=dict(**conn_pads, chip="c_chip", layer=1))
        qc1 = QuadCoupler(multiplanar_design,
                          "qc1",
                          options=dict(pos_x="0mm",
                                       pos_y="-0.08mm",
                                       pad_width="120um",
                                       pad_height="30um",
                                       cpw_stub_height="250um",
                                       chip="c_chip",
                                       layer=1))

        self.assertIsInstance(
            BoundsForPathAndPolyTables(
                multiplanar_design).get_bounds_of_path_and_poly_tables(
                    False, [], 1, 0, 0), tuple)

        self.assertEqual(
            len(
                BoundsForPathAndPolyTables(
                    multiplanar_design).get_bounds_of_path_and_poly_tables(
                        False, [], 1, 0, 0)), 5)

    def test_toolbox_metal_ensure_component_box_smaller_than_chip_box_(self):
        """Test functionality of ensure_component_box_smaller_than_chip_box in toolbox_metal.py"""
        ls_file_path = ("./qiskit_metal/tests/test_data/planar_chip.txt")
        multiplanar_design = MultiPlanar(metadata={},
                                         overwrite_enabled=True,
                                         layer_stack_filename=ls_file_path)
        conn_pads = dict(connection_pads=dict(coup1=dict(loc_W=-1, loc_H=1),
                                              coup2=dict(loc_W=1, loc_H=1)))
        q1 = TransmonPocket6(multiplanar_design,
                             "Q1",
                             options=dict(**conn_pads, chip="c_chip", layer=1))
        qc1 = QuadCoupler(multiplanar_design,
                          "qc1",
                          options=dict(pos_x="0mm",
                                       pos_y="-0.08mm",
                                       pad_width="120um",
                                       pad_height="30um",
                                       cpw_stub_height="250um",
                                       chip="c_chip",
                                       layer=1))
        chip = getattr(multiplanar_design, "_chips")
        for main in chip.items():
            coords = main[1]
        for item in coords.values():
            x_0 = item['center_x']
            y_0 = item['center_y']
            x_1 = item['size_x']
            y_1 = item['size_y']
        x_0 = int(float(x_0[:-2]))
        y_0 = int(float(y_0[:-2]))
        x_1 = int(x_1[:-2])
        y_1 = int(y_1[:-2])
        self.assertEqual(
            BoundsForPathAndPolyTables(
                multiplanar_design).ensure_component_box_smaller_than_chip_box_(
                    (0, 0, 2, 3), (x_0, y_0, x_1, y_1)), (0, 0, 2, 3))
        self.assertEqual(
            BoundsForPathAndPolyTables(
                multiplanar_design).ensure_component_box_smaller_than_chip_box_(
                    (0, 0, 9, 7), (None, None, None, None)), (0, 0, 9, 7))

    def test_toolbox_metal_get_box_for_xy_bounds(self):
        """Test functionality of get_box_for_xy_bounds in toolbox_metal.py."""
        ls_file_path = ("./qiskit_metal/tests/test_data/planar_chip.txt")
        multiplanar_design = MultiPlanar(metadata={},
                                         overwrite_enabled=True,
                                         layer_stack_filename=ls_file_path)
        conn_pads = dict(connection_pads=dict(coup1=dict(loc_W=-1, loc_H=1),
                                              coup2=dict(loc_W=1, loc_H=1)))
        q1 = TransmonPocket6(multiplanar_design,
                             "Q1",
                             options=dict(**conn_pads, chip="c_chip", layer=1))
        qc1 = QuadCoupler(multiplanar_design,
                          "qc1",
                          options=dict(pos_x="0mm",
                                       pos_y="-0.08mm",
                                       pad_width="120um",
                                       pad_height="30um",
                                       cpw_stub_height="250um",
                                       chip="c_chip",
                                       layer=1))
        multiplanar_design.chips['c_chip'] = {
            'size': {
                'center_x': '0.0mm',
                'center_y': '0.0mm',
                'size_x': '9mm',
                'size_y': '7mm'
            }
        }
        self.assertEqual(
            BoundsForPathAndPolyTables(
                multiplanar_design).get_box_for_xy_bounds(),
            (-4.5, -3.5, 4.5, 3.5))

    def test_toolbox_metal_are_all_chipnames_in_design(self):
        """Test functionality of are_all_chipnames_in_design in toolbox_metal.py."""
        ls_file_path = ("./qiskit_metal/tests/test_data/planar_chip.txt")
        multiplanar_design = MultiPlanar(metadata={},
                                         overwrite_enabled=True,
                                         layer_stack_filename=ls_file_path)
        conn_pads = dict(connection_pads=dict(coup1=dict(loc_W=-1, loc_H=1),
                                              coup2=dict(loc_W=1, loc_H=1)))
        q1 = TransmonPocket6(multiplanar_design,
                             "Q1",
                             options=dict(**conn_pads, chip="c_chip", layer=1))
        qc1 = QuadCoupler(multiplanar_design,
                          "qc1",
                          options=dict(pos_x="0mm",
                                       pos_y="-0.08mm",
                                       pad_width="120um",
                                       pad_height="30um",
                                       cpw_stub_height="250um",
                                       chip="c_chip",
                                       layer=1))
        multiplanar_design.chips['c_chip'] = {
            'size': {
                'center_x': '0.0mm',
                'center_y': '0.0mm',
                'size_x': '9mm',
                'size_y': '7mm'
            }
        }
        self.assertEqual(
            BoundsForPathAndPolyTables(
                multiplanar_design).are_all_chipnames_in_design(),
            (True, {'c_chip'}))

    def test_toolbox_metal_get_x_y_for_chip(self):
        """Test functionality of get_x_y_for_chip in toolbox_metal.py."""
        ls_file_path = ("./qiskit_metal/tests/test_data/planar_chip.txt")
        multiplanar_design = MultiPlanar(metadata={},
                                         overwrite_enabled=True,
                                         layer_stack_filename=ls_file_path)
        conn_pads = dict(connection_pads=dict(coup1=dict(loc_W=-1, loc_H=1),
                                              coup2=dict(loc_W=1, loc_H=1)))
        q1 = TransmonPocket6(multiplanar_design,
                             "Q1",
                             options=dict(**conn_pads, chip="c_chip", layer=1))
        qc1 = QuadCoupler(multiplanar_design,
                          "qc1",
                          options=dict(pos_x="0mm",
                                       pos_y="-0.08mm",
                                       pad_width="120um",
                                       pad_height="30um",
                                       cpw_stub_height="250um",
                                       chip="c_chip",
                                       layer=1))
        multiplanar_design.chips['c_chip'] = {
            'size': {
                'center_x': '0.0mm',
                'center_y': '0.0mm',
                'size_x': '9mm',
                'size_y': '7mm'
            }
        }
        self.assertEqual(
            BoundsForPathAndPolyTables(multiplanar_design).get_x_y_for_chip(
                'c_chip'), ((-4.5, -3.5, 4.5, 3.5), 0))
        self.assertEqual(
            BoundsForPathAndPolyTables(multiplanar_design).get_x_y_for_chip(
                'TEST_chip'), ((), 1))

    def test_toolbox_metal_chip_names_not_in_design(self):
        """Test functionality of chip_names_not_in_design in toolbox_metal.py."""
        ls_file_path = ("./qiskit_metal/tests/test_data/planar_chip.txt")
        multiplanar_design = MultiPlanar(metadata={},
                                         overwrite_enabled=True,
                                         layer_stack_filename=ls_file_path)
        conn_pads = dict(connection_pads=dict(coup1=dict(loc_W=-1, loc_H=1),
                                              coup2=dict(loc_W=1, loc_H=1)))
        q1 = TransmonPocket6(multiplanar_design,
                             "Q1",
                             options=dict(**conn_pads, chip="c_chip", layer=1))
        qc1 = QuadCoupler(multiplanar_design,
                          "qc1",
                          options=dict(pos_x="0mm",
                                       pos_y="-0.08mm",
                                       pad_width="120um",
                                       pad_height="30um",
                                       cpw_stub_height="250um",
                                       chip="c_chip",
                                       layer=1))
        self.assertEqual(
            BoundsForPathAndPolyTables(
                multiplanar_design).chip_names_not_in_design(
                    set(multiplanar_design.chips.keys()),
                    multiplanar_design.ls.get_unique_chip_names()), None)

    def test_toolbox_metal_chip_size_not_in_chipname_within_design(self):
        """Test functionality of chip_size_not_in_chipname_within_design in toolbox_metal.py."""
        ls_file_path = ("./qiskit_metal/tests/test_data/planar_chip.txt")
        multiplanar_design = MultiPlanar(metadata={},
                                         overwrite_enabled=True,
                                         layer_stack_filename=ls_file_path)
        conn_pads = dict(connection_pads=dict(coup1=dict(loc_W=-1, loc_H=1),
                                              coup2=dict(loc_W=1, loc_H=1)))
        q1 = TransmonPocket6(multiplanar_design,
                             "Q1",
                             options=dict(**conn_pads, chip="c_chip", layer=1))
        qc1 = QuadCoupler(multiplanar_design,
                          "qc1",
                          options=dict(pos_x="0mm",
                                       pos_y="-0.08mm",
                                       pad_width="120um",
                                       pad_height="30um",
                                       cpw_stub_height="250um",
                                       chip="c_chip",
                                       layer=1))
        self.assertEqual(
            BoundsForPathAndPolyTables(multiplanar_design).
            chip_size_not_in_chipname_within_design('c_chip'), None)

    def test_toolbox_metal_get_layer_datatype_when_fill_is_true(self):
        """Test functionality of get_layer_datatype_when_fill_is_true in toolbox_metal.py."""
        ls_file_path = ("./qiskit_metal/tests/test_data/planar_chip.txt")
        multiplanar_design = MultiPlanar(metadata={},
                                         overwrite_enabled=True,
                                         layer_stack_filename=ls_file_path)
        conn_pads = dict(connection_pads=dict(coup1=dict(loc_W=-1, loc_H=1),
                                              coup2=dict(loc_W=1, loc_H=1)))
        q1 = TransmonPocket6(multiplanar_design,
                             "Q1",
                             options=dict(**conn_pads, chip="c_chip", layer=1))
        qc1 = QuadCoupler(multiplanar_design,
                          "qc1",
                          options=dict(pos_x="0mm",
                                       pos_y="-0.08mm",
                                       pad_width="120um",
                                       pad_height="30um",
                                       cpw_stub_height="250um",
                                       chip="c_chip",
                                       layer=1))
        self.assertEqual(
            LayerStackHandler(
                multiplanar_design,
                (ls_file_path, None)).get_layer_datatype_when_fill_is_true(), {
                    (1, 0): {
                        'layer': 1,
                        'datatype': 0,
                        'thickness': 0.002,
                        'z_coord': 0.01,
                        'material': 'pec',
                        'chip_name': 'c_chip'
                    },
                    (3, 0): {
                        'layer': 3,
                        'datatype': 0,
                        'thickness': -0.5,
                        'z_coord': 0.0,
                        'material': 'silicon',
                        'chip_name': 'c_chip'
                    }
                })

    def test_toolbox_metal_get_properties_for_layer_datatype(self):
        """Test functionality of get_properties_for_layer_datatype in toolbox_metal.py."""
        ls_file_path = ("./qiskit_metal/tests/test_data/planar_chip.txt")
        multiplanar_design = MultiPlanar(metadata={},
                                         overwrite_enabled=True,
                                         layer_stack_filename=ls_file_path)
        conn_pads = dict(connection_pads=dict(coup1=dict(loc_W=-1, loc_H=1),
                                              coup2=dict(loc_W=1, loc_H=1)))
        q1 = TransmonPocket6(multiplanar_design,
                             "Q1",
                             options=dict(**conn_pads, chip="c_chip", layer=1))
        qc1 = QuadCoupler(multiplanar_design,
                          "qc1",
                          options=dict(pos_x="0mm",
                                       pos_y="-0.08mm",
                                       pad_width="120um",
                                       pad_height="30um",
                                       cpw_stub_height="250um",
                                       chip="c_chip",
                                       layer=1))
        self.assertEqual(
            LayerStackHandler(
                multiplanar_design,
                (ls_file_path, None)).get_properties_for_layer_datatype(
                    ['material', 'thickness'], 1, 0), ('pec', 0.002))
        self.assertEqual(
            LayerStackHandler(
                multiplanar_design,
                (ls_file_path, None)).get_properties_for_layer_datatype(
                    ['material', 'thickness'], 3, 0), ('silicon', -0.5))

    def test_toolbox_metal_is_layer_data_unique(self):
        """Test functionality of is_layer_data_unique in toolbox_metal.py."""
        ls_file_path = ("./qiskit_metal/tests/test_data/planar_chip.txt")
        multiplanar_design = MultiPlanar(metadata={},
                                         overwrite_enabled=True,
                                         layer_stack_filename=ls_file_path)
        conn_pads = dict(connection_pads=dict(coup1=dict(loc_W=-1, loc_H=1),
                                              coup2=dict(loc_W=1, loc_H=1)))
        q1 = TransmonPocket6(multiplanar_design,
                             "Q1",
                             options=dict(**conn_pads, chip="c_chip", layer=1))
        qc1 = QuadCoupler(multiplanar_design,
                          "qc1",
                          options=dict(pos_x="0mm",
                                       pos_y="-0.08mm",
                                       pad_width="120um",
                                       pad_height="30um",
                                       cpw_stub_height="250um",
                                       chip="c_chip",
                                       layer=1))
        self.assertEqual(
            LayerStackHandler(multiplanar_design,
                              (ls_file_path, None)).is_layer_data_unique(),
            True)

    def test_toolbox_metal_read_csv_df(self):
        """Test functionality of read_csv_df in toolbox_metal.py."""
        ls_file_path = ("./qiskit_metal/tests/test_data/planar_chip.txt")
        multiplanar_design = MultiPlanar(metadata={},
                                         overwrite_enabled=True,
                                         layer_stack_filename=ls_file_path)
        conn_pads = dict(connection_pads=dict(coup1=dict(loc_W=-1, loc_H=1),
                                              coup2=dict(loc_W=1, loc_H=1)))
        q1 = TransmonPocket6(multiplanar_design,
                             "Q1",
                             options=dict(**conn_pads, chip="c_chip", layer=1))
        qc1 = QuadCoupler(multiplanar_design,
                          "qc1",
                          options=dict(pos_x="0mm",
                                       pos_y="-0.08mm",
                                       pad_width="120um",
                                       pad_height="30um",
                                       cpw_stub_height="250um",
                                       chip="c_chip",
                                       layer=1))
        self.assertEqual(
            LayerStackHandler(multiplanar_design,
                              (ls_file_path, None))._read_csv_df(ls_file_path),
            None)

    def test_toolbox_metal_get_unique_chip_names(self):
        """Test functionality of get_unique_chip_names in toolbox_metal.py."""
        ls_file_path = ("./qiskit_metal/tests/test_data/planar_chip.txt")
        multiplanar_design = MultiPlanar(metadata={},
                                         overwrite_enabled=True,
                                         layer_stack_filename=ls_file_path)
        conn_pads = dict(connection_pads=dict(coup1=dict(loc_W=-1, loc_H=1),
                                              coup2=dict(loc_W=1, loc_H=1)))
        q1 = TransmonPocket6(multiplanar_design,
                             "Q1",
                             options=dict(**conn_pads, chip="c_chip", layer=1))
        qc1 = QuadCoupler(multiplanar_design,
                          "qc1",
                          options=dict(pos_x="0mm",
                                       pos_y="-0.08mm",
                                       pad_width="120um",
                                       pad_height="30um",
                                       cpw_stub_height="250um",
                                       chip="c_chip",
                                       layer=1))
        self.assertEqual(
            LayerStackHandler(multiplanar_design,
                              (ls_file_path, None)).get_unique_chip_names(),
            {'c_chip'})

    def test_toolbox_metal_get_unique_layer_ints(self):
        """Test functionality of get_unique_layer_ints in toolbox_metal.py."""
        ls_file_path = ("./qiskit_metal/tests/test_data/planar_chip.txt")
        multiplanar_design = MultiPlanar(metadata={},
                                         overwrite_enabled=True,
                                         layer_stack_filename=ls_file_path)
        conn_pads = dict(connection_pads=dict(coup1=dict(loc_W=-1, loc_H=1),
                                              coup2=dict(loc_W=1, loc_H=1)))
        q1 = TransmonPocket6(multiplanar_design,
                             "Q1",
                             options=dict(**conn_pads, chip="c_chip", layer=1))
        qc1 = QuadCoupler(multiplanar_design,
                          "qc1",
                          options=dict(pos_x="0mm",
                                       pos_y="-0.08mm",
                                       pad_width="120um",
                                       pad_height="30um",
                                       cpw_stub_height="250um",
                                       chip="c_chip",
                                       layer=1))
        self.assertEqual(
            LayerStackHandler(multiplanar_design,
                              (ls_file_path, None)).get_unique_layer_ints(),
            {1, 3})

    def test_toolbox_metal_warning_properties(self):
        """Test functionality of _warning_properties in toolbox_metal.py."""
        ls_file_path = ("./qiskit_metal/tests/test_data/planar_chip.txt")
        multiplanar_design = MultiPlanar(metadata={},
                                         overwrite_enabled=True,
                                         layer_stack_filename=ls_file_path)
        conn_pads = dict(connection_pads=dict(coup1=dict(loc_W=-1, loc_H=1),
                                              coup2=dict(loc_W=1, loc_H=1)))
        q1 = TransmonPocket6(multiplanar_design,
                             "Q1",
                             options=dict(**conn_pads, chip="c_chip", layer=1))
        qc1 = QuadCoupler(multiplanar_design,
                          "qc1",
                          options=dict(pos_x="0mm",
                                       pos_y="-0.08mm",
                                       pad_width="120um",
                                       pad_height="30um",
                                       cpw_stub_height="250um",
                                       chip="c_chip",
                                       layer=1))
        self.assertEqual(
            LayerStackHandler(multiplanar_design,
                              (ls_file_path, None))._warning_properties(
                                  ['test']), None)

    def test_toolbox_metal_warning_search(self):
        """Test functionality of _warning_search in toolbox_metal.py."""
        ls_file_path = ("./qiskit_metal/tests/test_data/planar_chip.txt")
        multiplanar_design = MultiPlanar(metadata={},
                                         overwrite_enabled=True,
                                         layer_stack_filename=ls_file_path)
        conn_pads = dict(connection_pads=dict(coup1=dict(loc_W=-1, loc_H=1),
                                              coup2=dict(loc_W=1, loc_H=1)))
        q1 = TransmonPocket6(multiplanar_design,
                             "Q1",
                             options=dict(**conn_pads, chip="c_chip", layer=1))
        qc1 = QuadCoupler(multiplanar_design,
                          "qc1",
                          options=dict(pos_x="0mm",
                                       pos_y="-0.08mm",
                                       pad_width="120um",
                                       pad_height="30um",
                                       cpw_stub_height="250um",
                                       chip="c_chip",
                                       layer=1))
        self.assertEqual(
            LayerStackHandler(multiplanar_design,
                              (ls_file_path, None))._warning_search(
                                  'test_chip', 7, 1, "FAIL"), None)

    def test_toolbox_metal_warning_search_minus_chip(self):
        """Test functionality of _warning_search_minus_chip in toolbox_metal.py."""
        ls_file_path = ("./qiskit_metal/tests/test_data/planar_chip.txt")
        multiplanar_design = MultiPlanar(metadata={},
                                         overwrite_enabled=True,
                                         layer_stack_filename=ls_file_path)
        conn_pads = dict(connection_pads=dict(coup1=dict(loc_W=-1, loc_H=1),
                                              coup2=dict(loc_W=1, loc_H=1)))
        q1 = TransmonPocket6(multiplanar_design,
                             "Q1",
                             options=dict(**conn_pads, chip="c_chip", layer=1))
        qc1 = QuadCoupler(multiplanar_design,
                          "qc1",
                          options=dict(pos_x="0mm",
                                       pos_y="-0.08mm",
                                       pad_width="120um",
                                       pad_height="30um",
                                       cpw_stub_height="250um",
                                       chip="c_chip",
                                       layer=1))
        self.assertEqual(
            LayerStackHandler(multiplanar_design,
                              (ls_file_path, None))._warning_search_minus_chip(
                                  5, 1, "FAIL"), None)

    def test_toolbox_metal_layer_stack_handler_pilot_error(self):
        """Test functionality of layer_stack_handler_pilot_error in toolbox_metal.py."""
        ls_file_path = ("./qiskit_metal/tests/test_data/planar_chip.txt")
        multiplanar_design = MultiPlanar(metadata={},
                                         overwrite_enabled=True,
                                         layer_stack_filename=ls_file_path)
        conn_pads = dict(connection_pads=dict(coup1=dict(loc_W=-1, loc_H=1),
                                              coup2=dict(loc_W=1, loc_H=1)))
        q1 = TransmonPocket6(multiplanar_design,
                             "Q1",
                             options=dict(**conn_pads, chip="c_chip", layer=1))
        qc1 = QuadCoupler(multiplanar_design,
                          "qc1",
                          options=dict(pos_x="0mm",
                                       pos_y="-0.08mm",
                                       pad_width="120um",
                                       pad_height="30um",
                                       cpw_stub_height="250um",
                                       chip="c_chip",
                                       layer=1))
        self.assertEqual(
            LayerStackHandler(
                multiplanar_design,
                (ls_file_path, None)).layer_stack_handler_pilot_error(), None)


if __name__ == '__main__':
    unittest.main(verbosity=2)
