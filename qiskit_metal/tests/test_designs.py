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

Created on Wed Apr 22 10:03:35 2020
@author: Jeremy D. Drysdale
"""

import unittest

from qiskit_metal.designs.design_base import QDesign
from qiskit_metal.designs.design_planar import DesignPlanar
from qiskit_metal.designs.interface_components import Components
from qiskit_metal.designs.net_info import QNet

from qiskit_metal.components.base.base import QComponent

class TestDesign(unittest.TestCase):
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

    @staticmethod
    def test_design_instantiate_QDesign():
        """
        Test the instantiation of QDesign
        """
        QDesign
        QDesign(metadata={})
        QDesign(metadata={}, overwrite_enabled=True)

    @staticmethod
    def test_design_instantiate_design_planar():
        """
        Test the instantiation of DesignPlanar
        """
        DesignPlanar

    @staticmethod
    def test_design_instantiate_design_components():
        """
        Test the instantiation of Components
        """
        Components

    @staticmethod
    def test_design_instantiate_qnet():
        """
        Test the instantiation of QNet
        """
        QNet

    def test_design_update_metadata(self):
        """
        Test the update of metadata in design_base.py
        """
        design = DesignPlanar(metadata={})
        data = design.metadata

        design.update_metadata({'new-key':'new-value'})
        design.update_metadata({'time_created':'07/23/2020, 17:00:00'})
        data = design.metadata

        self.assertEqual(len(data), 4)
        self.assertEqual(data['design_name'], 'my_design')
        self.assertEqual(data['notes'], '')
        self.assertEqual(data['time_created'], '07/23/2020, 17:00:00')
        self.assertEqual(data['new-key'], 'new-value')
        
    def test_design_get_chip_size(self):
        """
        Test getting chip size in design_base.py
        """
        design = DesignPlanar(metadata={})
        with self.assertRaises(NotImplementedError):
            design.get_chip_size()

    def test_design_get_chip_z(self):
        """
        Test getting chip z in design_base.py
        """
        design = DesignPlanar(metadata={})
        with self.assertRaises(NotImplementedError):
            design.get_chip_z()

    def test_design_rename_variables(self):
        """
        Test variable renaming in design_base.py
        """
        design = DesignPlanar(metadata={})
        design.rename_variable('cpw_gap', 'new-name')
        
        with self.assertRaises(ValueError):
            design.rename_variable('i-do-not-exist', 'uh-oh')

        self.assertEqual('new-name' in design._variables.keys(), True)
        self.assertEqual('cpw_gap' in design._variables.keys(), False)

    def test_design_rename_component(self):
        """
        Test renaming component in design_base.py
        """
        design = DesignPlanar(metadata={})
        QComponent(design, 'my_name-1', make=False)
        QComponent(design, 'my_name-2', make=False)

        design.rename_component('my_name-1', 'new-name')

        self.assertEqual('new-name' in design.name_to_id, True)
        self.assertEqual('my_name-1' in design.name_to_id, False)
        self.assertEqual('my_name-2' in design.name_to_id, True)

    def test_design_delete_component(self):
        """
        Test deleteing a component in design_base.py
        """
        design = DesignPlanar(metadata={})
        QComponent(design, 'my_name-1', make=False)
        QComponent(design, 'my_name-2', make=False)

        design.delete_component('my_name-1')
        self.assertEqual('my_name-1' in design.name_to_id, False)
        self.assertEqual('my_name-2' in design.name_to_id, True)

    def test_design_delete_all_components(self):
        """
        Test deleteing a component in design_base.py
        """
        design = DesignPlanar(metadata={})
        QComponent(design, 'my_name-1', make=False)
        QComponent(design, 'my_name-2', make=False)

        design.delete_all_components()
        self.assertEqual('my_name-1' in design.name_to_id, False)
        self.assertEqual('my_name-2' in design.name_to_id, False)

    def test_design_get_and_set_design_name(self):
        """
        Test getting the design name in design_base.py
        """
        design = DesignPlanar(metadata={})
        self.assertEqual(design.get_design_name(), 'my_design')

        design.set_design_name('new-name')
        self.assertEqual(design.get_design_name(), 'new-name')

    def test_design_get_units(self):
        """
        Test get units in design_base.py
        """
        design = DesignPlanar(metadata={})
        self.assertEqual(design.get_units(), 'mm')

    def test_design_get_list_ints(self):
        """
        Test geting the list ints in interface_components.py
        """
        design = DesignPlanar(metadata={})
        QComponent(design, 'my_name-1', make=False)
        QComponent(design, 'my_name-2', make=False)
        components = Components(design)

        self.assertListEqual(components.get_list_ints(['my_name-1']), [1])
        self.assertListEqual(components.get_list_ints(['my_name-1', 'my_name-2']), [1, 2])
        self.assertListEqual(components.get_list_ints(['my_name-1', 'my_name-2', 'nope']), [1, 2, 0])

    def test_design_find_id(self):
        """
        Test finding the id from the name
        """
        design = DesignPlanar(metadata={})
        QComponent(design, 'my_name-1', make=False)
        QComponent(design, 'my_name-2', make=False)
        components = Components(design)

        self.assertEqual(components.find_id('my_name-1'), 1)
        self.assertEqual(components.find_id('my_name-2'), 2)
        self.assertEqual(components.find_id('my_name-3'), 0)






if __name__ == '__main__':
    unittest.main(verbosity=2)
