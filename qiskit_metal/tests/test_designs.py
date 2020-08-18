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
#pylint: disable-msg=too-many-public-methods
#pylint: disable-msg=broad-except

"""
Qiskit Metal unit tests analyses functionality.

Created on Wed Apr 22 10:03:35 2020
@author: Jeremy D. Drysdale
"""

import unittest
import pandas as pd

from qiskit_metal.designs.design_base import QDesign
from qiskit_metal.designs.design_planar import DesignPlanar
from qiskit_metal.designs.interface_components import Components
from qiskit_metal.designs.net_info import QNet

from qiskit_metal.components.base.base import QComponent

from qiskit_metal.components.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.components.interconnects.resonator_rectangle_spiral import ResonatorRectangleSpiral

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

    def test_design_instantiate_qdesign(self):
        """
        Test the instantiation of QDesign
        """
        try:
            QDesign
        except Exception:
            self.fail("QDesign failed")

        try:
            QDesign(metadata={})
        except Exception:
            self.fail("QDesign(metadata={}) failed")

        try:
            QDesign(metadata={}, overwrite_enabled=True)
        except Exception:
            self.fail("QDesign(metadata={}, overwrite_enabled=True) failed")

    def test_design_instantiate_design_planar(self):
        """
        Test the instantiation of DesignPlanar
        """
        try:
            DesignPlanar
        except Exception:
            self.fail("DesignPlanar failed")

        try:
            DesignPlanar(metadata={})
        except Exception:
            self.fail("DesignPlanar(metadata={}) failed")

        try:
            DesignPlanar(metadata={}, overwrite_enabled=True)
        except Exception:
            self.fail("DesignPlanar(metadata={}, overwrite_enabled=True) failed")

    def test_design_instantiate_design_components(self):
        """
        Test the instantiation of Components
        """
        design = QDesign()
        try:
            Components(design)
        except Exception:
            self.fail("Components(design) failed")

    def test_design_instantiate_qnet(self):
        """
        Test the instantiation of QNet
        """
        try:
            QNet
        except Exception:
            self.fail("QNet failed")

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

        self.assertEqual('new-name' in design.variables.keys(), True)
        self.assertEqual('cpw_gap' in design.variables.keys(), False)

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

    def test_design_default_component_name(self):
        """
        Test automatic naming of components
        """
        design = DesignPlanar(metadata={})

        ResonatorRectangleSpiral(design, make=False)
        self.assertEqual('res_1' in design.components, True)
        ResonatorRectangleSpiral(design, make=False)
        self.assertEqual('res_2' in design.components, True)

        # Manually add the next automatic name to check it doesn't get repeated
        ResonatorRectangleSpiral(design, 'res_3', make=False)
        ResonatorRectangleSpiral(design, make=False)
        self.assertEqual('res_3' in design.components, True)
        self.assertEqual('res_4' in design.components, True)

        # Add a different component
        TransmonPocket(design, make=False)
        self.assertEqual('Q_1' in design.components, True)

        # Add a component with no predefined prefix
        QComponent(design, make=False)
        self.assertEqual('QComponent_1' in design.components, True)

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

    def test_design_interface_components_get_list_ints(self):
        """
        Test geting the list ints in interface_components.py
        """
        design = DesignPlanar(metadata={})
        QComponent(design, 'my_name-1', make=False)
        QComponent(design, 'my_name-2', make=False)
        components = Components(design)

        self.assertListEqual(components.get_list_ints(['my_name-1']), [1])
        self.assertListEqual(components.get_list_ints(['my_name-1', 'my_name-2']), [1, 2])
        self.assertListEqual(components.get_list_ints(['my_name-1', 'my_name-2', 'nope']),
                             [1, 2, 0])

    def test_design_interface_components_find_id(self):
        """
        Test finding the id from the name in interface_components.py
        """
        design = DesignPlanar(metadata={})
        QComponent(design, 'my_name-1', make=False)
        QComponent(design, 'my_name-2', make=False)
        components = Components(design)

        self.assertEqual(components.find_id('my_name-1'), 1)
        self.assertEqual(components.find_id('my_name-2'), 2)
        self.assertEqual(components.find_id('my_name-3'), 0)

    def test_design_qnet_add_pins_to_table(self):
        """
        Test add_pins_to_table in net_info.py
        """
        design = DesignPlanar(metadata={})
        QComponent(design, 'my_name-1', make=False)
        QComponent(design, 'my_name-2', make=False)
        Components(design)
        qnet = QNet()

        qnet.add_pins_to_table(1, 'my_name-1', 2, 'my_name-2')
        df = qnet.net_info

        data = {'net_id':[1, 1],
                'component_id':[1, 2],
                'pin_name':['my_name-1', 'my_name-2']}
        df_expected = pd.DataFrame(data, index=[0, 1])

        self.assertEqual(len(df), len(df_expected))
        data_points = df_expected['net_id'].size
        for i in range(data_points):
            for j in ['net_id', 'component_id', 'pin_name']:
                self.assertEqual(df_expected[j][i], df[j][i])

    def test_design_qnet_delete_net_id(self):
        """
        Test delete a given net id in net_info.py
        """
        design = DesignPlanar(metadata={})
        QComponent(design, 'my_name-1', make=False)
        QComponent(design, 'my_name-2', make=False)
        Components(design)
        qnet = QNet()

        net_id = qnet.add_pins_to_table(1, 'my_name-1', 2, 'my_name-2')
        qnet.delete_net_id(net_id)
        df = qnet.net_info
        self.assertEqual(df.empty, True)

    def test_design_qnet_delete_all_pins_for_component_id(self):
        """
        Test delete all pins for a given component id in net_info.py
        """
        design = DesignPlanar(metadata={})
        QComponent(design, 'my_name-1', make=False)
        QComponent(design, 'my_name-2', make=False)
        QComponent(design, 'my_name-3', make=False)
        QComponent(design, 'my_name-4', make=False)
        Components(design)
        qnet = QNet()

        qnet.add_pins_to_table(1, 'my_name-1', 2, 'my_name-2')
        qnet.add_pins_to_table(3, 'my_name-3', 4, 'my_name-4')
        qnet.delete_all_pins_for_component(2)
        df = qnet.net_info

        data = {'net_id':[2, 2],
                'component_id':[3, 4],
                'pin_name':['my_name-3', 'my_name-4']}
        df_expected = pd.DataFrame(data, index=[2, 3])

        self.assertEqual(len(df), len(df_expected))
        for i in [2, 3]:
            for j in ['net_id', 'component_id', 'pin_name']:
                self.assertEqual(df_expected[j][i], df[j][i])

    def test_design_qnet_get_components_and_pins_for_netid(self):
        """
        Test get_components_Sand_pins_for_netid in net_info.py
        """
        design = DesignPlanar(metadata={})
        QComponent(design, 'my_name-1', make=False)
        QComponent(design, 'my_name-2', make=False)
        QComponent(design, 'my_name-3', make=False)
        QComponent(design, 'my_name-4', make=False)
        Components(design)
        qnet = QNet()

        net_id_1 = qnet.add_pins_to_table(1, 'my_name-1', 2, 'my_name-2')
        net_id_2 = qnet.add_pins_to_table(3, 'my_name-3', 4, 'my_name-4')

        data = {'net_id':[1, 1],
                'component_id':[1, 2],
                'pin_name':['my_name-1', 'my_name-2']}
        df_expected_1 = pd.DataFrame(data, index=[0, 1])

        data = {'net_id':[2, 2],
                'component_id':[3, 4],
                'pin_name':['my_name-3', 'my_name-4']}
        df_expected_2 = pd.DataFrame(data, index=[2, 3])

        df = qnet.get_components_and_pins_for_netid(net_id_1)
        self.assertEqual(len(df), len(df_expected_1))
        data_points = df_expected_1['net_id'].size
        for i in range(data_points):
            for j in ['net_id', 'component_id', 'pin_name']:
                self.assertEqual(df_expected_1[j][i], df[j][i])

        df = qnet.get_components_and_pins_for_netid(net_id_2)
        self.assertEqual(len(df), len(df_expected_2))
        for i in [2, 3]:
            for j in ['net_id', 'component_id', 'pin_name']:
                self.assertEqual(df_expected_2[j][i], df[j][i])


if __name__ == '__main__':
    unittest.main(verbosity=2)
