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
#pylint: disable-msg=protected-access
#pylint: disable-msg=broad-except

"""
Qiskit Metal unit tests analyses functionality.

Created on Wed Apr 22 10:00:29 2020
@author: Jeremy D. Drysdale
"""

# Note - Tests not written for these functions:
# display/test_display_format_dict_ala_z
# utility_functions/copy_update

import unittest
from qiskit_metal.toolbox_python.display import Headings
from qiskit_metal.toolbox_python import utility_functions

class TestToolboxPython(unittest.TestCase):
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

    def test_instantiate_headings(self):
        """
        Test instantiation of Headings class
        """
        try:
            Headings
        except Exception:
            self.fail("Headings failed")

    def test_utility_defaults(self):
        """
        Test defaults in utility_functions.py
        """
        self.assertEqual(utility_functions._old_warn, None)

    def test_utility_dict_start_with(self):
        """
        Test dict_start_with in utility_functions.py
        """
        my_dict = {'first':1, 'second':2,
                   'third':{'third-one':'3-1', 'third-two':{'third-two-only':'uh'}},
                   'fourth':4}

        expected = [[{'third-one': '3-1', 'third-two': {'third-two-only': 'uh'}}],
                    {'third': {'third-one': '3-1', 'third-two': {'third-two-only': 'uh'}}}, [], {}]

        actual = []
        actual.append(utility_functions.dict_start_with(my_dict, 'third'))
        actual.append(utility_functions.dict_start_with(my_dict, 'third', as_=dict))
        actual.append(utility_functions.dict_start_with(my_dict, 'nope'))
        actual.append(utility_functions.dict_start_with(my_dict, 'nope', as_=dict))

        for i in range(4):
            self.assertEqual(actual[i], expected[i])

    def test_utility_data_frame_empty_typed(self):
        """
        Test data_frame_empty_typed in utility_functions.py
        """
        base = dict(
            col1=bool,
            col2=object
        )

        df = utility_functions.data_frame_empty_typed(base)

        self.assertEqual(df.dtypes['col1'], bool)
        self.assertEqual(df.dtypes['col2'], object)

    def test_utility_clean_name(self):
        """
        Test clean_name in utility_function.py
        """
        self.assertEqual(utility_functions.clean_name('32v2 g #Gmw845h$W b53wi '),
                         '_32v2_g__Gmw845h_W_b53wi_')
        self.assertEqual(utility_functions.clean_name('halestorm rulz!'), 'halestorm_rulz_')

if __name__ == '__main__':
    unittest.main(verbosity=2)
