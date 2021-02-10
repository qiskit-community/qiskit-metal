# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# pylint: disable-msg=unnecessary-pass
#pylint: disable-msg=too-many-public-methods
#pylint: disable-msg=protected-access
"""
Qiskit Metal unit tests components functionality.

Created on Wed Apr 22 09:58:35 2020
@author: Jeremy D. Drysdale
"""

import unittest
import numpy as np

from qiskit_metal.qlibrary.base import _parsed_dynamic_attrs
from qiskit_metal import Dict
from qiskit_metal import draw
from qiskit_metal.qlibrary._template import MyQComponent
from qiskit_metal.qlibrary.base.base import QComponent
from qiskit_metal.qlibrary.base.qroute import QRoute
from qiskit_metal.qlibrary.base.qubit import BaseQubit
from qiskit_metal.qlibrary.connectors.cpw_hanger_t import CPWHangerT
from qiskit_metal.qlibrary.connectors import open_to_ground
from qiskit_metal.qlibrary.connectors import short_to_ground
from qiskit_metal.qlibrary.interconnects.framed_path import RouteFramed
from qiskit_metal.qlibrary.interconnects.meandered import RouteMeander
from qiskit_metal.qlibrary.interconnects import straight_path
from qiskit_metal import designs
from qiskit_metal.qlibrary.qubits import transmon_pocket_cl
from qiskit_metal.qlibrary.qubits import transmon_pocket
from qiskit_metal.qlibrary.qubits import transmon_cross
from qiskit_metal.tests.assertions import AssertionsMixin

#pylint: disable-msg=line-too-long
from qiskit_metal.qlibrary.interconnects.resonator_rectangle_spiral import ResonatorRectangleSpiral


class TestComponentFunctionality(unittest.TestCase, AssertionsMixin):
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

    def test_component_get_nested_dict_item(self):
        """
        Test the functionality of get_nested_dict_item in _parsed_dynamic_attrs.py
        """
        # Setup expected test results
        my_dict = Dict(aa=Dict(x1={'dda': '34fF'}, y1='Y', z='10um'),
                       bb=Dict(x2=5, y2='YYYsdg', z='100um'),
                       cc='100nm')

        # Generate actual result data
        _test_a = _parsed_dynamic_attrs.get_nested_dict_item(my_dict, ['cc'])
        _test_b = _parsed_dynamic_attrs.get_nested_dict_item(
            my_dict, ['aa', 'x1', 'dda'])
        _test_c = _parsed_dynamic_attrs.get_nested_dict_item(my_dict, ['aa'])
        _test_d = _parsed_dynamic_attrs.get_nested_dict_item(my_dict, ['empty'])

        # Test all elements of the result data against expected data
        self.assertEqual('100nm', _test_a)
        self.assertEqual('34fF', _test_b)
        self.assertEqual({
            'x1': {
                'dda': '34fF'
            },
            'y1': 'Y',
            'z': '10um'
        }, _test_c)
        self.assertEqual({}, _test_d)

    def test_component_get_and_set_qcomponent_name(self):
        """
        Test the getting and setting of a QComponent name
        """
        design = designs.DesignPlanar()
        my_qcomponent_local = None

        my_qcomponent_local = QComponent(design, "my_name", make=False)
        self.assertEqual(my_qcomponent_local.name, "my_name")

        my_qcomponent_local.name = "another-name"
        self.assertEqual(my_qcomponent_local.name, "another-name")

    #pylint: disable-msg=too-many-statements
    def test_component_qcomponent_add_pins(self):
        """
        Test pin addition
        """
        design = designs.DesignPlanar()
        my_q_component = QComponent(design, "my_name-add-pins", make=False)

        spiral_list_0 = self.generate_spiral_list(0, 0)
        spiral_list_1 = self.generate_spiral_list(1, 2)

        my_q_component.add_pin('pin1-name',
                               np.array(spiral_list_0.coords)[-2:], 0.1)
        my_q_component.add_pin('pin2-name',
                               np.array(spiral_list_1.coords)[-2:], 0.1)

        my_pins = my_q_component.pins

        self.assertEqual(len(my_pins), 2)
        self.assertEqual(len(my_pins['pin1-name']), 10)
        self.assertEqual(len(my_pins['pin1-name']['points']), 2)
        self.assertEqual(len(my_pins['pin1-name']['points'][0]), 2)
        self.assertEqual(len(my_pins['pin1-name']['points'][1]), 2)
        self.assertEqual(my_pins['pin1-name']['points'][0][0], -35.)
        self.assertEqual(my_pins['pin1-name']['points'][0][1], 30.)
        self.assertEqual(my_pins['pin1-name']['points'][1][0], -35.)
        self.assertEqual(my_pins['pin1-name']['points'][1][1], -35.)
        self.assertEqual(len(my_pins['pin1-name']['middle']), 2)
        self.assertEqual(my_pins['pin1-name']['middle'][0], -35.)
        self.assertEqual(my_pins['pin1-name']['middle'][1], -2.5)
        self.assertEqual(len(my_pins['pin1-name']['normal']), 2)
        self.assertEqual(my_pins['pin1-name']['normal'][0], 1.)
        self.assertEqual(my_pins['pin1-name']['normal'][1], -0.)
        self.assertEqual(len(my_pins['pin1-name']['tangent']), 2)
        self.assertEqual(my_pins['pin1-name']['tangent'][0], 0.)
        self.assertEqual(my_pins['pin1-name']['tangent'][1], -1.)
        self.assertEqual(my_pins['pin1-name']['width'], 65.0)
        self.assertEqual(my_pins['pin1-name']['gap'], 0.06)
        self.assertEqual(my_pins['pin1-name']['chip'], 'main')
        self.assertEqual(my_pins['pin1-name']['parent_name'], 1)
        self.assertEqual(my_pins['pin1-name']['net_id'], 0)
        self.assertEqual(my_pins['pin1-name']['length'], 0)

        self.assertEqual(len(my_pins['pin2-name']), 10)
        self.assertEqual(len(my_pins['pin2-name']['points']), 2)
        self.assertEqual(len(my_pins['pin2-name']['points'][0]), 2)
        self.assertEqual(len(my_pins['pin2-name']['points'][1]), 2)
        self.assertEqual(my_pins['pin2-name']['points'][0][0], -34.)
        self.assertEqual(my_pins['pin2-name']['points'][0][1], 32.)
        self.assertEqual(my_pins['pin2-name']['points'][1][0], -34.)
        self.assertEqual(my_pins['pin2-name']['points'][1][1], -33.)
        self.assertEqual(len(my_pins['pin2-name']['middle']), 2)
        self.assertEqual(my_pins['pin2-name']['middle'][0], -34.)
        self.assertEqual(my_pins['pin2-name']['middle'][1], -0.5)
        self.assertEqual(len(my_pins['pin2-name']['normal']), 2)
        self.assertEqual(my_pins['pin2-name']['normal'][0], 1.)
        self.assertEqual(my_pins['pin2-name']['normal'][1], -0.)
        self.assertEqual(len(my_pins['pin2-name']['tangent']), 2)
        self.assertEqual(my_pins['pin2-name']['tangent'][0], 0.)
        self.assertEqual(my_pins['pin2-name']['tangent'][1], -1.)
        self.assertEqual(my_pins['pin2-name']['width'], 65.0)
        self.assertEqual(my_pins['pin2-name']['gap'], 0.06)
        self.assertEqual(my_pins['pin2-name']['chip'], 'main')
        self.assertEqual(my_pins['pin2-name']['parent_name'], 1)
        self.assertEqual(my_pins['pin2-name']['net_id'], 0)
        self.assertEqual(my_pins['pin2-name']['length'], 0)
        my_q_component.delete()

    def test_component_template_component_metadata(self):
        """
        Test component_metadata in _template.py
        """
        component = MyQComponent
        self.assertEqual(component.component_metadata,
                         {'short_name': 'component'})

    def test_component_base_component_metadata(self):
        """
        Test component_metadata in base/base.py
        """
        component = QComponent
        self.assertEqual(component.component_metadata, {})

    def test_component_base_get_template_options(self):
        """
        Test get_template_options in base.py
        """
        design = designs.DesignPlanar()

        self.assertEqual(QComponent.get_template_options(design), {})

        expected = {
            'pos_x': '0um',
            'pos_y': '0um',
            'connection_pads': {},
            '_default_connection_pads': {}
        }
        self.assertEqual(BaseQubit.get_template_options(design), expected)

    def test_component_qubit_component_metadata(self):
        """
        Test component_metadata in base/qubit.py
        """
        component = BaseQubit
        metadata = component.component_metadata
        self.assertEqual(len(metadata), 2)
        self.assertEqual(metadata['short_name'], 'Q')
        self.assertEqual(metadata['_qgeometry_table_poly'], 'True')

    def test_component_cpw_hanger_t_component_metadata(self):
        """
        Test component_metadata in component/cpw_hanger_t.py
        """
        component = CPWHangerT
        self.assertEqual(component.component_metadata, {'short_name': 'cpw'})

    def test_component_open_to_ground_component_metadata(self):
        """
        Test component_metadata in component/open_to_ground.py
        """
        component = open_to_ground.OpenToGround
        self.assertEqual(component.component_metadata, {'short_name': 'term'})

    def test_component_short_to_ground_component_metadata(self):
        """
        Test component_metadata in component/short_to_ground.py
        """
        component = short_to_ground.ShortToGround
        self.assertEqual(component.component_metadata, {'short_name': 'term'})

    def test_component_framed_path_component_metadata(self):
        """
        Test component_metadata in interconnects/framed_path.py
        """
        component = RouteFramed
        self.assertEqual(component.component_metadata, {'short_name': 'cpw'})

    def test_component_straight_path_component_metadata(self):
        """
        Test component_metadata in interconnects/straight_path.py
        """
        component = straight_path.RouteStraight
        self.assertEqual(component.component_metadata, {'short_name': 'cpw'})

    def test_component_meander_path_component_metadata(self):
        """
        Test component_metadata in interconnects/meandered.py
        """
        component = RouteMeander
        self.assertEqual(component.component_metadata, {'short_name': 'cpw'})

    def test_component_qroute_base_component_metadata(self):
        """
        Test component_metadata in interconnects/qroute_base.py
        """
        component = QRoute
        self.assertEqual(component.component_metadata, {'short_name': 'route'})

    def test_component_resonator_rectangle_spiral_component_metadata(self):
        """
        Test component_metadata in interconnects/resonator_rectangle_spiral.py
        """
        component = ResonatorRectangleSpiral
        self.assertEqual(component.component_metadata, {'short_name': 'res'})

    def test_component_transmon_pocket_cl_component_metadata(self):
        """
        Test component_metadata in qubits/transmon_pocket_cl.py
        """
        component = transmon_pocket_cl.TransmonPocketCL
        metadata = component.component_metadata
        self.assertEqual(len(metadata), 2)
        self.assertEqual(metadata['short_name'], 'Q')
        self.assertEqual(metadata['_qgeometry_table_poly'], 'True')

    def test_component_transmon_pocket_component_metadata(self):
        """
        Test component_metadata in qubits.transmon_pocket.py
        """
        component = transmon_pocket.TransmonPocket
        metadata = component.component_metadata
        self.assertEqual(len(metadata), 4)
        self.assertEqual(metadata['short_name'], 'Pocket')
        self.assertEqual(metadata['_qgeometry_table_path'], 'True')
        self.assertEqual(metadata['_qgeometry_table_poly'], 'True')

    def test_component_transmon_cross_component_metadata(self):
        """
        Test component_metadata in qubits.transmon_cross.py
        """
        component = transmon_cross.TransmonCross
        metadata = component.component_metadata
        self.assertEqual(len(metadata), 3)
        self.assertEqual(metadata['short_name'], 'Cross')
        self.assertEqual(metadata['_qgeometry_table_poly'], 'True')
        self.assertEqual(metadata['_qgeometry_table_junction'], 'True')

    def test_component_qcomponent_get_pin_names(self):
        """
        Test getting all the pin names
        """
        design = designs.DesignPlanar()
        my_q_component = QComponent(design, "my_name-get-pin-names", make=False)

        spiral_list_0 = self.generate_spiral_list(0, 0)
        spiral_list_1 = self.generate_spiral_list(1, 2)

        my_q_component.add_pin('pin1-name',
                               np.array(spiral_list_0.coords)[-2:], 0.1)
        my_q_component.add_pin('pin2-name',
                               np.array(spiral_list_1.coords)[-2:], 0.1)

        my_pin_names = list(my_q_component.pin_names)
        my_pin_names.sort()
        self.assertEqual(len(my_pin_names), 2)
        self.assertEqual(my_pin_names[0], 'pin1-name')
        self.assertEqual(my_pin_names[1], 'pin2-name')
        my_q_component.delete()

    def test_component_qcomponent_add_and_get_pin(self):
        """
        Test getting a pin by name
        """
        design = designs.DesignPlanar()
        my_q_component = QComponent(design, "my_name-get-pin", make=False)

        spiral_list_0 = self.generate_spiral_list(0, 0)
        spiral_list_1 = self.generate_spiral_list(1, 2)

        my_q_component.add_pin('pin1-name',
                               np.array(spiral_list_0.coords)[-2:], 0.1)
        my_q_component.add_pin('pin2-name',
                               np.array(spiral_list_1.coords)[-2:], 0.1)

        my_pin = my_q_component.get_pin('pin2-name')
        self.assertEqual(len(my_pin), 10)
        self.assertEqual(len(my_pin['points']), 2)
        self.assertEqual(len(my_pin['points'][0]), 2)
        self.assertEqual(len(my_pin['points'][1]), 2)
        self.assertEqual(my_pin['points'][0][0], -34.)
        self.assertEqual(my_pin['points'][0][1], 32.)
        self.assertEqual(my_pin['points'][1][0], -34.)
        self.assertEqual(my_pin['points'][1][1], -33.)
        self.assertEqual(len(my_pin['middle']), 2)
        self.assertEqual(my_pin['middle'][0], -34.)
        self.assertEqual(my_pin['middle'][1], -0.5)
        self.assertEqual(len(my_pin['normal']), 2)
        self.assertEqual(my_pin['normal'][0], 1.)
        self.assertEqual(my_pin['normal'][1], -0.)
        self.assertEqual(len(my_pin['tangent']), 2)
        self.assertEqual(my_pin['tangent'][0], 0.)
        self.assertEqual(my_pin['tangent'][1], -1.)
        self.assertEqual(my_pin['width'], 65.0)
        self.assertEqual(my_pin['gap'], 0.06)
        self.assertEqual(my_pin['chip'], 'main')
        self.assertEqual(my_pin['parent_name'], 1)
        self.assertEqual(my_pin['net_id'], 0)
        self.assertEqual(my_pin['length'], 0)
        my_q_component.delete()

    def test_qlibrary_get_component_geometry_dict(self):
        """
        Test get_component_geometry_dict in qgeometries_handler.py
        """
        design = designs.DesignPlanar()
        transmon_pocket.TransmonPocket(design, 'Q1')
        transmon_pocket.TransmonPocket(design, 'Q2')

        q1_actual = (-0.2275, 0.015, 0.2275, 0.105)
        q2_actual = (-0.2275, -0.105, 0.2275, -0.015)

        q1_dict = design._qgeometry.get_component_geometry_dict('Q1')
        q2_dict = design._qgeometry.get_component_geometry_dict('Q2')
        q1_result = q1_dict['poly'][0].bounds
        q2_result = q2_dict['poly'][1].bounds

        self.assertEqual(len(q1_actual), len(q1_result))
        self.assertEqual(len(q2_actual), len(q2_result))

        for x, _ in enumerate(q1_actual):
            self.assertEqual(_, q1_result[x])

        for x, _ in enumerate(q2_actual):
            self.assertEqual(_, q2_result[x])

    def test_qlibrary_get_component_geometry_list(self):
        """
        Test get_component_geometry_list in qgeometries_handler.py
        """
        design = designs.DesignPlanar()
        transmon_pocket.TransmonPocket(design, 'Q1')

        expected = [(-0.2275, 0.015, 0.2275, 0.105),
                    (-0.2275, -0.105, 0.2275, -0.015),
                    (-0.325, -0.325, 0.325, 0.325), (0.0, -0.015, 0.0, 0.015)]
        actual = design._qgeometry.get_component_geometry_list('Q1')
        self.assertEqual(len(actual), len(expected))
        length = len(expected)
        for x in range(length):
            self.assertEqual(len(expected[x]), len(actual[x].bounds))
            sub_length = len(expected[x])
            for y in range(sub_length):
                self.assertEqual(actual[x].bounds[y], expected[x][y])

    def test_qlibrary_get_component_geometry(self):
        """
        Test get_component_geometry in qgeometries_handler.py
        """
        design = designs.DesignPlanar()
        transmon_pocket.TransmonPocket(design, 'Q1')

        expected = [(-0.2275, 0.015, 0.2275, 0.105),
                    (-0.2275, -0.105, 0.2275, -0.015),
                    (-0.325, -0.325, 0.325, 0.325), (0.0, -0.015, 0.0, 0.015)]
        actual = design._qgeometry.get_component_geometry('Q1')

        self.assertEqual(len(expected), len(actual))
        length = len(expected)
        for x in range(length):
            self.assertEqual(len(expected[x]), len(actual[x].bounds))
            sub_length = len(expected[x])
            for y in range(sub_length):
                self.assertEqual(actual[x].bounds[y], expected[x][y])

    def test_qlibrary_rename_component(self):
        """
        Test rename_component in element_handler.py
        """
        design = designs.DesignPlanar()
        transmon_pocket.TransmonPocket(design, 'Q1')

        component_id = design.components['Q1'].id
        design.rename_component(component_id, 'Q1_new_name')

        self.assertEqual(design.components.keys(), ['Q1_new_name'])

    def test_qlibrary_delete_component(self):
        """
        Test delete_component in element_handler.py
        """
        design = designs.DesignPlanar()
        transmon_pocket.TransmonPocket(design, 'Q1')
        transmon_pocket.TransmonPocket(design, 'Q2')
        transmon_pocket.TransmonPocket(design, 'Q3')

        before_junction_list = design.qgeometry.tables['junction'][
            'component'].tolist()
        before_poly_list = design.qgeometry.tables['poly']['component'].tolist()

        component_id = design.components['Q2'].id
        design.qgeometry.delete_component_id(component_id)

        after_junction_list = design.qgeometry.tables['junction'][
            'component'].tolist()
        after_poly_list = design.qgeometry.tables['poly']['component'].tolist()

        self.assertTrue(component_id in before_junction_list)
        self.assertTrue(component_id in before_poly_list)
        self.assertFalse(component_id in after_junction_list)
        self.assertFalse(component_id in after_poly_list)

    @staticmethod
    def generate_spiral_list(x: int, y: int):
        """Helper function to generate a sprital list

        Args:
            x (int): x-coordinate
            y (int): y-coordinate

        Returns:
            list: list of points
        """
        spiral_list = []

        for step in range(3):
            point_value = 20 + step * 5
            spiral_list.append((-point_value, -point_value))
            spiral_list.append((point_value, -point_value))
            spiral_list.append((point_value, point_value))
            spiral_list.append((-point_value - (1 + 4), point_value))

        point_value = 20 + (step + 1) * 5
        spiral_list.append((-point_value, -point_value))
        spiral_list = draw.LineString(spiral_list)

        spiral_list = draw.rotate(spiral_list, 0, origin=(x, y))
        spiral_list = draw.translate(spiral_list, x, y)

        return spiral_list


if __name__ == '__main__':
    unittest.main(verbosity=2)
