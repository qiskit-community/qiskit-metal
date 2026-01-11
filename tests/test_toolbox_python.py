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

#pylint: disable-msg=unnecessary-pass
#pylint: disable-msg=protected-access
#pylint: disable-msg=broad-except
"""Qiskit Metal unit tests analyses functionality."""

import unittest
from qiskit_metal.toolbox_python.display import Headings
from qiskit_metal.toolbox_python.display import Color
from qiskit_metal.toolbox_python.display import MetalTutorialMagics
from qiskit_metal.toolbox_python import display
from qiskit_metal.toolbox_python import utility_functions
from qiskit_metal.toolbox_python._logging import LogStore


class TestToolboxPython(unittest.TestCase):
    """Unit test class."""

    def setUp(self):
        """Setup unit test."""
        pass

    def tearDown(self):
        """Tie any loose ends."""
        pass

    def test_instantiate_log_store(self):
        """Test instantiation of LogStore class."""
        try:
            LogStore('my title', 100)
        except Exception:
            self.fail("LogStore failed")

    def test_instantiate_headings(self):
        """Test instantiation of Headings class."""
        try:
            Headings()
        except Exception:
            self.fail("Headings failed")

    def test_instantiate_metal_tutorial_magics(self):
        """Test instantiation of MetalTutorialMagics class."""
        try:
            MetalTutorialMagics()
        except Exception:
            self.fail("MetalTutorialMagics failed")

    def test_instantiate_color(self):
        """Test instantiation of Color class."""
        try:
            Color()
        except Exception:
            self.fail("Color failed")

    def test_display_style_colon_list(self):
        """Test style_colon_list in display.py."""
        actual = display.style_colon_list("text:more:still")
        expected = "text:\033[94mmore:still\033[0m"

        self.assertEqual(actual, expected)

    def test_display_format_dict_ala_z(self):
        """Test functionality of format_dict_ala_z in display.py."""
        my_dict = {'first': 1}
        expected = "  'first'             : 1,                            "
        actual = display.format_dict_ala_z(my_dict)

        self.assertEqual(expected, actual)

    def test_utility_defaults(self):
        """Test defaults in utility_functions.py."""
        self.assertEqual(utility_functions._old_warn, None)

    def test_utility_dict_start_with(self):
        """Test dict_start_with in utility_functions.py."""
        my_dict = {
            'first': 1,
            'second': 2,
            'third': {
                'third-one': '3-1',
                'third-two': {
                    'third-two-only': 'uh'
                }
            },
            'fourth': 4
        }

        expected = [[{
            'third-one': '3-1',
            'third-two': {
                'third-two-only': 'uh'
            }
        }], {
            'third': {
                'third-one': '3-1',
                'third-two': {
                    'third-two-only': 'uh'
                }
            }
        }, [], {}]

        actual = []
        actual.append(utility_functions.dict_start_with(my_dict, 'third'))
        actual.append(
            utility_functions.dict_start_with(my_dict, 'third', as_=dict))
        actual.append(utility_functions.dict_start_with(my_dict, 'nope'))
        actual.append(
            utility_functions.dict_start_with(my_dict, 'nope', as_=dict))

        for i in range(4):
            self.assertEqual(actual[i], expected[i])

    def test_utility_data_frame_empty_typed(self):
        """Test data_frame_empty_typed in utility_functions.py."""
        base = dict(col1=bool, col2=object)

        df = utility_functions.data_frame_empty_typed(base)

        self.assertEqual(df.dtypes['col1'], bool)
        self.assertEqual(df.dtypes['col2'], object)

    def test_utility_copy_update(self):
        """Test functionality of copy_update in utility_functions.py."""
        self.assertEqual(utility_functions.copy_update({'a': 1}, {}), {'a': 1})
        self.assertEqual(utility_functions.copy_update({'a': 1}, {'b': 2}), {
            'a': 1,
            'b': 2
        })
        self.assertEqual(utility_functions.copy_update({'a': 1}, {'a': 2}),
                         {'a': 2})

    def test_utility_bad_fillet_idxs(self):
        """Test functionality of bad_fillet_idxs in utility_functions.py."""
        results = utility_functions.bad_fillet_idxs([(1.0, 1.0), (1.5, 1.5),
                                                     (1.51, 1.5), (2.0, 2.0)],
                                                    0.1)
        self.assertEqual(results, [1, 2])

    def test_utility_clean_name(self):
        """Test clean_name in utility_function.py."""
        self.assertEqual(
            utility_functions.clean_name('32v2 g #Gmw845h$W b53wi '),
            '_32v2_g__Gmw845h_W_b53wi_')
        self.assertEqual(utility_functions.clean_name('halestorm rulz!'),
                         'halestorm_rulz_')

    def test_utility_toggle_numbers(self):
        """Test functionality of toggle_numbers in utility_functions.py."""
        self.assertEqual(utility_functions.toggle_numbers([3, 5, 9, 1], 14),
                         [0, 1, 2, 4, 6, 7, 8, 11, 12, 13])

    def test_utility_get_range_of_vertex_to_not_fillet(self):
        """Test functionality of get_range_of_vertex_to_not_fillet in
        utility_functions.py."""
        my_list = [(1, 1), (1, 2), (1, 2), (2, 2), (5, 5), (3, 2), (11, 11),
                   (11, 11), (11, 21), (12, 21)]
        result = utility_functions.get_range_of_vertex_to_not_fillet(
            my_list, 0.25)
        self.assertEqual(result, [(0, 2), (6, 7)])

    def test_utility_compress_vertex_list(self):
        """Test functionality of compress_vertex_list in
        utility_functions.py."""
        my_list = [1, 2, 5, 2, 6, 7, 10, 4, 7, 1]
        expected = [(1, 1), (1, 2), (2, 2), (4, 7), (7, 7), (10, 10)]
        self.assertEqual(utility_functions.compress_vertex_list(my_list),
                         expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
