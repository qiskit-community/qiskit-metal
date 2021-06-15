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

from qiskit_metal.toolbox_metal import about
from qiskit_metal.toolbox_metal import parsing
from qiskit_metal.toolbox_metal import math_and_overrides
from qiskit_metal.toolbox_metal.exceptions import QiskitMetalExceptions
from qiskit_metal.toolbox_metal.exceptions import QiskitMetalDesignError
from qiskit_metal.toolbox_metal.exceptions import IncorrectQtException
from qiskit_metal.toolbox_metal.exceptions import QLibraryGUIException
from qiskit_metal.tests.assertions import AssertionsMixin


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

    def test_toolbox_metal_instantiation_qlibrary_gui__excpetion(self):
        """Test instantiation of QLibraryGUIException."""
        try:
            QLibraryGUIException("test message")
        except Exception:
            self.fail("QLibraryGUIException failed.")

    def test_toolbox_metal_about(self):
        """Test that about in about.py produces about text without any
        errors."""
        try:
            about.about()
        except Exception:
            self.fail("about() failed")

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


if __name__ == '__main__':
    unittest.main(verbosity=2)
