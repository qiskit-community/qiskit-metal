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
# pylint: disable-msg=pointless-statement
# pylint: disable-msg=too-many-public-methods
# pylint: disable-msg=broad-except
# pylint: disable-msg=invalid-name
# pylint: disable-msg=import-error
"""Qiskit Metal unit tests analyses functionality."""

import unittest
import pandas as pd

from qiskit_metal.designs.design_base import QDesign
from qiskit_metal.designs.design_planar import DesignPlanar
from qiskit_metal.designs.interface_components import Components
from qiskit_metal.designs.net_info import QNet
from qiskit_metal.qlibrary.core import QComponent
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.tests.assertions import AssertionsMixin

from qiskit_metal.qlibrary.lumped.resonator_coil_rect import ResonatorCoilRect


class TestDesign(unittest.TestCase, AssertionsMixin):
    """Unit test class."""

    def setUp(self):
        """Setup unit test."""
        pass

    def tearDown(self):
        """Tie any loose ends."""
        pass

    def test_design_instantiate_qdesign(self):
        """Test the instantiation of QDesign."""
        try:
            QDesign()
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
        """Test the instantiation of DesignPlanar."""
        try:
            DesignPlanar()
        except Exception:
            self.fail("DesignPlanar failed")

        try:
            DesignPlanar(metadata={})
        except Exception:
            self.fail("DesignPlanar(metadata={}) failed")

        try:
            DesignPlanar(metadata={}, overwrite_enabled=True)
        except Exception:
            self.fail(
                "DesignPlanar(metadata={}, overwrite_enabled=True) failed")

    def test_design_instantiate_design_components(self):
        """Test the instantiation of Components."""
        design = QDesign()
        try:
            Components(design)
        except Exception:
            self.fail("Components(design) failed")

    def test_design_instantiate_qnet(self):
        """Test the instantiation of QNet."""
        try:
            QNet()
        except Exception:
            self.fail("QNet failed")

    def test_design_get_chip_layer(self):
        """Test getting chip size in design_base.py."""
        design = QDesign(metadata={})
        self.assertEqual(design.get_chip_layer('main'), 0)

    def test_design_rename_variable(self):
        """Test rename_variable in QDesign class"""
        design = QDesign(metadata={})
        design.rename_variable('cpw_gap', 'new_name')
        my_keys = design._variables.keys()

        self.assertEqual(len(my_keys), 2)
        self.assertTrue('cpw_width' in my_keys)
        self.assertTrue('new_name' in my_keys)

    def test_design_update_metadata(self):
        """Test the update of metadata in design_base.py."""
        design = DesignPlanar(metadata={})
        data = design.metadata

        design.update_metadata({'new-key': 'new-value'})
        design.update_metadata({'time_created': '07/23/2020, 17:00:00'})
        data = design.metadata

        self.assertEqual(len(data), 4)
        self.assertEqual(data['design_name'], 'my_design')
        self.assertEqual(data['notes'], '')
        self.assertEqual(data['time_created'], '07/23/2020, 17:00:00')
        self.assertEqual(data['new-key'], 'new-value')

    def test_design_get_chip_size(self):
        """Test getting chip size in design_base.py."""
        design = DesignPlanar(metadata={})

        main_expected = {
            'center_x': '0.0mm',
            'center_y': '0.0mm',
            'center_z': '0.0mm',
            'size_x': '9mm',
            'size_y': '6mm',
            'size_z': '-750um',
            'sample_holder_top': '890um',
            'sample_holder_bottom': '1650um'
        }

        self.assertEqual(design.get_chip_size(), main_expected)
        self.assertEqual(design.get_chip_size('main'), main_expected)
        self.assertEqual(design.get_chip_size('dead'), {})

    def test_design_get_chip_z(self):
        """Test getting chip z in design_base.py."""
        design = DesignPlanar(metadata={})

        actual = design.get_chip_z()
        self.assertEqual(actual, '0.0mm')

    def test_design_rename_variables(self):
        """Test variable renaming in design_base.py."""
        design = DesignPlanar(metadata={})
        design.rename_variable('cpw_gap', 'new-name')

        with self.assertRaises(ValueError):
            design.rename_variable('i-do-not-exist', 'uh-oh')

        self.assertEqual('new-name' in design.variables.keys(), True)
        self.assertEqual('cpw_gap' in design.variables.keys(), False)

    def test_design_rename_component(self):
        """Test renaming component in design_base.py."""
        design = DesignPlanar(metadata={})
        QComponent(design, 'my_name-1', make=False)
        QComponent(design, 'my_name-2', make=False)

        design.rename_component('my_name-1', 'new-name')

        self.assertEqual('new-name' in design.name_to_id, True)
        self.assertEqual('my_name-1' in design.name_to_id, False)
        self.assertEqual('my_name-2' in design.name_to_id, True)

    def test_design_default_component_name(self):
        """Test automatic naming of components."""
        design = DesignPlanar(metadata={})

        ResonatorCoilRect(design, make=False)
        self.assertEqual('res_1' in design.components, True)
        ResonatorCoilRect(design, make=False)
        self.assertEqual('res_2' in design.components, True)

        # Manually add the next automatic name to check it doesn't get repeated
        ResonatorCoilRect(design, 'res_3', make=False)
        ResonatorCoilRect(design, make=False)
        self.assertEqual('res_3' in design.components, True)
        self.assertEqual('res_4' in design.components, True)

        # Add a different component
        TransmonPocket(design, make=False)
        self.assertEqual('Q_1' in design.components, False)

        # Add a component with no predefined prefix
        QComponent(design, make=False)
        self.assertEqual('QComponent_1' in design.components, True)

    def test_design_delete_component(self):
        """Test deleteing a component in design_base.py."""
        design = DesignPlanar(metadata={})
        QComponent(design, 'my_name-1', make=False)
        QComponent(design, 'my_name-2', make=False)

        design.delete_component('my_name-1')
        self.assertEqual('my_name-1' in design.name_to_id, False)
        self.assertEqual('my_name-2' in design.name_to_id, True)

    def test_design_delete_all_components(self):
        """Test deleteing a component in design_base.py."""
        design = DesignPlanar(metadata={})
        QComponent(design, 'my_name-1', make=False)
        QComponent(design, 'my_name-2', make=False)

        design.delete_all_components()
        self.assertEqual('my_name-1' in design.name_to_id, False)
        self.assertEqual('my_name-2' in design.name_to_id, False)

    def test_design_get_and_set_design_name(self):
        """Test getting the design name in design_base.py."""
        design = DesignPlanar(metadata={})
        self.assertEqual(design.get_design_name(), 'my_design')

        design.set_design_name('new-name')
        self.assertEqual(design.get_design_name(), 'new-name')

    def test_design_get_units(self):
        """Test get units in design_base.py."""
        design = DesignPlanar(metadata={})
        self.assertEqual(design.get_units(), 'mm')

    def test_design_get_new_qcomponent_name_id(self):
        """Test _get_new_qcomponent_name_id in design_base.py."""
        design = DesignPlanar(metadata={})
        QComponent(design, make=False)
        QComponent(design, make=False)

        self.assertEqual(design._get_new_qcomponent_name_id('QComponent'), 3)
        self.assertEqual(design._get_new_qcomponent_name_id('Not-there'), 1)

    def test_design_planar_get_x_y_for_chip(self):
        """Test get_x_y_for_chip in design_planar.py."""
        design = DesignPlanar(metadata={})
        QComponent(design, make=False)
        QComponent(design, make=False)

        expected = ((-4.5, -3.0, 4.5, 3.0), 0)
        actual = design.get_x_y_for_chip('main')

        self.assertEqual(len(expected), len(actual))
        self.assertEqual(len(expected[0]), len(actual[0]))
        for i in range(4):
            self.assertEqual(expected[0][i], actual[0][i])

        self.assertEqual(expected[1], actual[1])

    def test_design_interface_components_get_list_ints(self):
        """Test geting the list ints in interface_components.py."""
        design = DesignPlanar(metadata={})
        QComponent(design, 'my_name-1', make=False)
        QComponent(design, 'my_name-2', make=False)
        components = Components(design)

        self.assertListEqual(components.get_list_ints(['my_name-1']), [1])
        self.assertListEqual(
            components.get_list_ints(['my_name-1', 'my_name-2']), [1, 2])
        self.assertListEqual(
            components.get_list_ints(['my_name-1', 'my_name-2', 'nope']),
            [1, 2, 0])

    def test_design_interface_components_find_id(self):
        """Test finding the id from the name in interface_components.py."""
        design = DesignPlanar(metadata={})
        QComponent(design, 'my_name-1', make=False)
        QComponent(design, 'my_name-2', make=False)
        components = Components(design)

        self.assertEqual(components.find_id('my_name-1'), 1)
        self.assertEqual(components.find_id('my_name-2'), 2)
        self.assertEqual(components.find_id('my_name-3'), 0)

    def test_design_qnet_add_pins_to_table(self):
        """Test add_pins_to_table in net_info.py."""
        design = DesignPlanar(metadata={})
        QComponent(design, 'my_name-1', make=False)
        QComponent(design, 'my_name-2', make=False)
        Components(design)
        qnet = QNet()

        qnet.add_pins_to_table(1, 'my_name-1', 2, 'my_name-2')
        df = qnet.net_info

        data = {
            'net_id': [1, 1],
            'component_id': [1, 2],
            'pin_name': ['my_name-1', 'my_name-2']
        }
        df_expected = pd.DataFrame(data, index=[0, 1])

        self.assertEqual(len(df), len(df_expected))
        data_points = df_expected['net_id'].size
        for i in range(data_points):
            for j in ['net_id', 'component_id', 'pin_name']:
                self.assertEqual(df_expected[j][i], df[j][i])

    def test_design_qnet_delete_net_id(self):
        """Test delete a given net id in net_info.py."""
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
        """Test delete all pins for a given component id in net_info.py."""
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

        data = {
            'net_id': [2, 2],
            'component_id': [3, 4],
            'pin_name': ['my_name-3', 'my_name-4']
        }
        df_expected = pd.DataFrame(data, index=[2, 3])

        self.assertEqual(len(df), len(df_expected))
        for i in [2, 3]:
            for j in ['net_id', 'component_id', 'pin_name']:
                self.assertEqual(df_expected[j][i], df[j][i])

    def test_design_qnet_get_components_and_pins_for_netid(self):
        """Test get_components_Sand_pins_for_netid in net_info.py."""
        design = DesignPlanar(metadata={})
        QComponent(design, 'my_name-1', make=False)
        QComponent(design, 'my_name-2', make=False)
        QComponent(design, 'my_name-3', make=False)
        QComponent(design, 'my_name-4', make=False)
        Components(design)
        qnet = QNet()

        net_id_1 = qnet.add_pins_to_table(1, 'my_name-1', 2, 'my_name-2')
        net_id_2 = qnet.add_pins_to_table(3, 'my_name-3', 4, 'my_name-4')

        data = {
            'net_id': [1, 1],
            'component_id': [1, 2],
            'pin_name': ['my_name-1', 'my_name-2']
        }
        df_expected_1 = pd.DataFrame(data, index=[0, 1])

        data = {
            'net_id': [2, 2],
            'component_id': [3, 4],
            'pin_name': ['my_name-3', 'my_name-4']
        }
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

    def test_design_copy_qcomponent(self):
        """Test the functionlaity of copy_qcomponent in design_base.py."""
        design = DesignPlanar()
        design.overwrite_enabled = True
        q_1 = TransmonPocket(design, 'Q1')
        q1_copy = design.copy_qcomponent(q_1, 'Q1_copy')

        self.assertEqual(q_1.name, 'Q1')
        self.assertEqual(q1_copy.name, 'Q1_copy')
        self.assertEqual(q_1.id, 1)
        self.assertEqual(q1_copy.id, 2)
        self.assertEqual(q_1.class_name, q1_copy.class_name)
        self.assertEqual(q_1.options['pos_x'], q1_copy.options['pos_x'])

        q1_copy.options['pos_x'] = '1.0mm'
        self.assertEqual(q_1.options['pos_x'], '0.0um')
        self.assertEqual(q1_copy.options['pos_x'], '1.0mm')

    def test_design_copy_multiple_qcomponents(self):
        """Test the functionality of copy_multiple_qcomponents in
        design_base.py."""
        design = DesignPlanar()
        design.overwrite_enabled = True
        q_1 = TransmonPocket(design, 'Q1')
        q_2 = TransmonPocket(design, 'Q2')
        q_3 = TransmonPocket(design, 'Q3')

        design.copy_multiple_qcomponents(
            [q_1, q_2, q_3], ['q1_copy', 'q2_copy', 'q3_copy'],
            [dict(pos_y='-1.0mm'),
             dict(pos_y='-2.0mm'),
             dict(pos_y='-3.0mm')])

        q1_copy = design._components[4]
        q2_copy = design._components[5]
        q3_copy = design._components[6]

        self.assertEqual(q_1.name, 'Q1')
        self.assertEqual(q_2.name, 'Q2')
        self.assertEqual(q_3.name, 'Q3')
        self.assertEqual(q1_copy.name, 'q1_copy')
        self.assertEqual(q2_copy.name, 'q2_copy')
        self.assertEqual(q3_copy.name, 'q3_copy')
        self.assertEqual(q_1.id, 1)
        self.assertEqual(q_2.id, 2)
        self.assertEqual(q_3.id, 3)
        self.assertEqual(q1_copy.id, 4)
        self.assertEqual(q2_copy.id, 5)
        self.assertEqual(q3_copy.id, 6)

        self.assertEqual(q_1.class_name, q1_copy.class_name)
        self.assertEqual(q_2.class_name, q2_copy.class_name)
        self.assertEqual(q_3.class_name, q3_copy.class_name)
        self.assertEqual(q_1.options['pos_x'], q1_copy.options['pos_x'])
        self.assertEqual(q_2.options['pos_x'], q2_copy.options['pos_x'])
        self.assertEqual(q_3.options['pos_x'], q3_copy.options['pos_x'])

        self.assertEqual(q1_copy.options['pos_y'], '-1.0mm')
        self.assertEqual(q2_copy.options['pos_y'], '-2.0mm')
        self.assertEqual(q3_copy.options['pos_y'], '-3.0mm')

    def test_design_connect_pins(self):
        """Test connect_pins functionality in design_base.py."""
        design = DesignPlanar()
        design.overwrite_enabled = True

        TransmonPocket(design, 'Q1')
        TransmonPocket(design, 'Q2')

        design.connect_pins(1, 'p1', 2, 'p2')
        pf = design._qnet._net_info

        self.assertFalse(pf.empty)
        self.assertEqual(pf['net_id'][0], 1)
        self.assertEqual(pf['net_id'][1], 1)
        self.assertEqual(pf['component_id'][0], 1)
        self.assertEqual(pf['component_id'][1], 2)
        self.assertEqual(pf['pin_name'][0], 'p1')
        self.assertEqual(pf['pin_name'][1], 'p2')

    def test_design_delete_all_pins(self):
        """Test delete_all_pins functionality in design_base.py."""
        design = DesignPlanar()
        design.overwrite_enabled = True

        TransmonPocket(design, 'Q1')
        TransmonPocket(design, 'Q2')

        design.connect_pins(1, 'p1', 2, 'p2')
        pf = design._qnet._net_info
        self.assertFalse(pf.empty)

        design.delete_all_pins()
        pf = design._qnet._net_info
        self.assertTrue(pf.empty)

    def test_design_all_component_names_id(self):
        """Test all_component_names_id functionality in design_base.py."""
        design = DesignPlanar()
        design.overwrite_enabled = True

        TransmonPocket(design, 'Q1')
        TransmonPocket(design, 'Q2')

        expected = [('Q1', 1), ('Q2', 2)]
        actual = design.all_component_names_id()

        for i in range(2):
            self.assertEqual(expected[i], actual[i])

    def test_design_get_list_of_tables_in_metadata(self):
        """Tests the get_list_of_tables_in_metadata function in design_base.py
        by exeucting get_table_values_form_renderers in a component."""
        design = DesignPlanar()
        q1 = TransmonPocket(design, 'Q1')

        result = q1._get_table_values_from_renderers(design)

        self.assertEqual(len(result), 18)
        self.assertEqual(result['hfss_inductance'], '10nH')
        self.assertEqual(result['hfss_capacitance'], 0)
        self.assertEqual(result['hfss_resistance'], 0)
        self.assertAlmostEqual(result['hfss_mesh_kw_jj'], 7e-06, places=6)
        self.assertEqual(result['q3d_inductance'], '10nH')
        self.assertEqual(result['q3d_capacitance'], 0)
        self.assertEqual(result['q3d_resistance'], 0)
        self.assertAlmostEqual(result['q3d_mesh_kw_jj'], 7e-06, places=6)
        self.assertEqual(result['gds_cell_name'], 'my_other_junction')
        self.assertEqual(result['hfss_wire_bonds'], False)
        self.assertEqual(result['q3d_wire_bonds'], False)
        self.assertEqual(result['aedt_hfss_inductance'], 10e-9)
        self.assertEqual(result['aedt_hfss_capacitance'], 0)
        self.assertEqual(result['gds_make_airbridge'], False)


if __name__ == '__main__':
    unittest.main(verbosity=2)
