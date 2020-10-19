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
#pylint: disable-msg=pointless-statement
#pylint: disable-msg=broad-except

"""
Qiskit Metal unit tests components functionality.

Created on Wed June 17 06:08:27 2020
@author: Jeremy D. Drysdale
"""

import unittest

from qiskit_metal._defaults import DefaultMetalOptions
from qiskit_metal._defaults import DefaultOptionsRenderer

class TestDefautOptions(unittest.TestCase):
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

    def test_default_options_instantiation_default_metal_options(self):
        """
        Test instantiation of DefaultMetalOptions
        """
        try:
            DefaultMetalOptions
        except Exception:
            self.fail("DefaultMetalOptions failed")

        try:
            DefaultMetalOptions({})
        except Exception:
            self.fail("DefaultMetalOptions({}) failed")

    def test_default_options_instantiation_default_options_renderer(self):
        """
        Test instantiation of DefaultOptionsRenderer
        """
        try:
            DefaultOptionsRenderer
        except Exception:
            self.fail("DefaultOptionsRenderer failed")

        try:
            DefaultOptionsRenderer(draw_substrate={})
        except Exception:
            self.fail("DefaultOptionsRenderer(draw_substrate={}) failed")

        try:
            DefaultOptionsRenderer(draw_substrate={}, bounding_box={})
        except Exception:
            self.fail("DefaultOptionsRenderer(draw_substrate={}, bounding_box={}) failed")


    def test_default_options_create(self):
        """
        Test the functionality of initializing default_options in _defaults.py
        """
        # Setup expected test results
        _options = DefaultMetalOptions()

        # Test all elements of the result data against expected data
        self.assertEqual(len(_options), 4)
        self.assertEqual('mm', _options['units'])
        self.assertEqual('main', _options['chip'])

        _qdesign = _options['qdesign']
        self.assertEqual(len(_qdesign), 1)
        _variables = _qdesign['variables']
        self.assertEqual(len(_variables), 2)
        self.assertEqual('10 um', _variables['cpw_width'])
        self.assertEqual('6 um', _variables['cpw_gap'])

        _geometry = _options['geometry']
        self.assertEqual(len(_geometry), 2)
        self.assertEqual(16, _geometry['buffer_resolution'])
        self.assertEqual(5.0, _geometry['buffer_mitre_limit'])

    def test_default_options_update(self):
        """
        Test the functionality of updating default_options in _defaults.py
        """
        # Setup expected test results
        _options = DefaultMetalOptions()

        # Generate actual result data
        with self.assertRaises(TypeError):
            # if these don't fail they exist in the default already so don't use for testing
            _options['garbage_numeric']
            _options['garbage_textual']

        _options.update_default_options('garbage_numeric', 1234567)
        _options.update_default_options('garbage_textual', 'aloha')
        _options.update_default_options('units', 'miles')

        # Test all elements of the result data against expected data
        self.assertEqual(1234567, _options['garbage_numeric'])
        self.assertEqual('aloha', _options['garbage_textual'])
        self.assertEqual('miles', _options['units'])

    def test_default_options_renderer_create(self):
        """
        Test the functionality of initializing default_options_renderer in _defaults.py
        """
        # Setup expected test results
        _options = DefaultOptionsRenderer()

        # Test all elements of the result data against expected data
        self.assertEqual(len(_options.default_options), 2)
        _draw_substrate = _options.default_options['draw_substrate']
        _draw_bounding_box = _options.default_options['draw_bounding_box']

        self.assertEqual(len(_draw_substrate), 9)
        self.assertEqual(_draw_substrate['pos_xy'], "['0um', '0um']")
        self.assertEqual(_draw_substrate['size'], "['8.5mm', '6.5mm', '-0.750mm']")
        self.assertEqual(_draw_substrate['elevation'], 0)
        self.assertEqual(_draw_substrate['ground_plane'], 'ground_plane')
        self.assertEqual(_draw_substrate['substrate'], 'substrate')
        self.assertEqual(_draw_substrate['material'], 'silicon')
        self.assertEqual(_draw_substrate['transparency_plane'], 0)
        self.assertEqual(_draw_substrate['transparency_substrate'], 0)
        self.assertEqual(_draw_substrate['wireframe_substrate'], False)

        self.assertEqual(len(_draw_bounding_box), 3)
        self.assertEqual(_draw_bounding_box[0], [0, 0])
        self.assertEqual(_draw_bounding_box[1], [0, 0])
        self.assertEqual(_draw_bounding_box[2], ['0.890mm', '0.900mm'])

    def test_default_options_renderer_update(self):
        """
        Test the functionality of updating default_options_renderer in _defaults.py
        """
        # Setup expected test results
        _options = DefaultOptionsRenderer()

        # Generate actual result data
        with self.assertRaises(KeyError):
            # if these don't fail they exist in the default already so don't use for testing
            _options.default_options['garbage_numeric']
            _options.default_options['garbage_textual']

        _options.update_default_options('garbage_numeric', 1234567)
        _options.update_default_options('garbage_textual', 'aloha')

        # Test all elements of the result data against expected data
        self.assertEqual(1234567, _options.default_options['garbage_numeric'])
        self.assertEqual('aloha', _options.default_options['garbage_textual'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
