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
# pylint: disable-msg=import-outside-toplevel
# pylint: disable-msg=import-error
"""Qiskit Metal unit tests analyses functionality."""

import unittest
import numpy as np

from geopandas import GeoDataFrame

from qiskit_metal import designs
from qiskit_metal import draw

from qiskit_metal.qgeometries import qgeometries_handler
from qiskit_metal.qgeometries.qgeometries_handler import QGeometryTables
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket


class TestElements(unittest.TestCase):
    """Unit test class."""

    def setUp(self):
        """Setup unit test."""
        pass

    def tearDown(self):
        """Tie any loose ends."""
        pass

    def test_qgeometry_instantiate_q_geometry_tables(self):
        """Test instantiation of QGeometryTables."""
        try:
            design = designs.DesignPlanar()
            QGeometryTables(design)
        except Exception:
            self.fail("QGeometryTables failed")

    def test_qgeometry_is_qgeometry_table(self):
        """Test is_qgeometry_table in qgeometries_handler.py."""
        self.assertEqual(
            qgeometries_handler.is_qgeometry_table(QGeometryTables), True)
        self.assertEqual(
            qgeometries_handler.is_qgeometry_table("i_am_a_string"), False)

    def test_qgeometry_element_columns(self):
        """Test that ELEMENT_COLUMNS was not accidentally changed in
        element_handler.py."""
        import importlib
        importlib.reload(qgeometries_handler)
        e_c = qgeometries_handler.ELEMENT_COLUMNS

        self.assertEqual(len(e_c), 4)

        self.assertEqual(len(e_c['base']), 8)
        self.assertEqual(e_c['base']['component'], str)
        self.assertEqual(e_c['base']['name'], str)
        self.assertEqual(e_c['base']['geometry'], object)
        self.assertEqual(e_c['base']['layer'], int)
        self.assertEqual(e_c['base']['subtract'], bool)
        self.assertEqual(e_c['base']['helper'], bool)
        self.assertEqual(e_c['base']['chip'], str)
        self.assertEqual(e_c['base']['__renderers__'], dict())
        self.assertEqual(len(e_c['base']['__renderers__']), 0)

        self.assertEqual(len(e_c['path']), 3)
        self.assertEqual(e_c['path']['width'], float)
        self.assertEqual(e_c['path']['fillet'], object)
        self.assertEqual(e_c['path']['__renderers__'], dict())
        self.assertEqual(len(e_c['path']['__renderers__']), 0)

        self.assertEqual(len(e_c['poly']), 2)
        self.assertEqual(e_c['poly']['fillet'], object)
        self.assertEqual(e_c['poly']['__renderers__'], dict())
        self.assertEqual(len(e_c['poly']['__renderers__']), 0)

        self.assertEqual(len(e_c['junction']), 2)
        self.assertEqual(e_c['junction']['width'], float)
        self.assertEqual(e_c['junction']['__renderers__'], dict())

    # pylint: disable-msg=unused-variable
    def test_qgeometry_true_bools(self):
        """Test that TRUE_BOOLS was not accidentally changed in
        element_handler.py."""
        expected = [True, 'True', 'true', 'Yes', 'yes', '1', 1]
        actual = qgeometries_handler.TRUE_BOOLS

        self.assertEqual(len(actual), len(expected))

        for x, _ in enumerate(expected):
            self.assertTrue(_ in actual)

    def test_qgeometry_q_element_constants(self):
        """Test that constants in QGeometryTables class in element_handler.py
        were not accidentally changed."""
        design = designs.DesignPlanar()
        qgt = QGeometryTables(design)

        self.assertEqual(qgt.__i_am_qgeometry_table__, True)
        self.assertEqual(qgt.name_delimiter, '_')

    def test_qgeometry_q_element_add_renderer_extension(self):
        """Test add_renderer_extension in QGeometryTables class in
        element_handler.py."""
        design = designs.DesignPlanar()
        qgt = QGeometryTables(design)
        qgt.add_renderer_extension(
            'new_name',
            dict(base=dict(color=str, klayer=int),
                 path=dict(thickness=float),
                 poly=dict(material=str)))

        e_c = qgt.ELEMENT_COLUMNS

        self.assertTrue('color' in e_c['base']['__renderers__']['new_name'])
        self.assertTrue('klayer' in e_c['base']['__renderers__']['new_name'])
        self.assertTrue('thickness' in e_c['path']['__renderers__']['new_name'])
        self.assertTrue('material' in e_c['poly']['__renderers__']['new_name'])

        self.assertEqual(e_c['base']['__renderers__']['new_name']['color'], str)
        self.assertEqual(e_c['base']['__renderers__']['new_name']['klayer'],
                         int)
        self.assertEqual(e_c['path']['__renderers__']['new_name']['thickness'],
                         float)
        self.assertEqual(e_c['poly']['__renderers__']['new_name']['material'],
                         str)

    def test_qgeometry_q_element_get_element_types(self):
        """Test get_element_types in QGeometryTables class in
        element_handler.py."""
        design = designs.DesignPlanar()
        qgt = QGeometryTables(design)

        expected = ['path', 'poly', 'junction']
        actual = qgt.get_element_types()

        self.assertEqual(len(expected), len(actual))

        for x, _ in enumerate(expected):
            self.assertTrue(_ in actual)

    def test_qgeometry_q_element_create_tables(self):
        """Test create_tables in QGeometryTables class in
        element_handler.py."""
        design = designs.DesignPlanar()
        qgt = QGeometryTables(design)
        qgt.create_tables()

        actual = qgt.tables

        self.assertEqual(len(actual), 3)
        self.assertTrue('path' in actual)
        self.assertTrue('poly' in actual)
        self.assertTrue('junction' in actual)

        self.assertEqual(actual['path'].dtypes['component'], object)
        self.assertEqual(actual['path'].dtypes['name'], object)
        self.assertEqual(actual['path'].dtypes['subtract'], bool)
        self.assertEqual(actual['path'].dtypes['helper'], bool)
        self.assertEqual(actual['path'].dtypes['chip'], object)
        self.assertEqual(actual['path'].dtypes['fillet'], object)

        self.assertEqual(actual['poly'].dtypes['component'], object)
        self.assertEqual(actual['poly'].dtypes['name'], object)
        self.assertEqual(actual['poly'].dtypes['subtract'], bool)
        self.assertEqual(actual['poly'].dtypes['helper'], bool)
        self.assertEqual(actual['poly'].dtypes['chip'], object)
        self.assertEqual(actual['poly'].dtypes['fillet'], object)

        self.assertEqual(actual['junction'].dtypes['component'], object)
        self.assertEqual(actual['junction'].dtypes['name'], object)
        self.assertEqual(actual['junction'].dtypes['subtract'], bool)
        self.assertEqual(actual['junction'].dtypes['helper'], bool)
        self.assertEqual(actual['junction'].dtypes['chip'], object)
        self.assertEqual(actual['junction'].dtypes['width'], float)

    def test_qgeometry_q_element_get_rname(self):
        """Test get_rname in QGeometryTables class in element_handler.py."""
        design = designs.DesignPlanar()
        qgt = QGeometryTables(design)

        actual = qgt.get_rname('some_name', 'aloha')

        self.assertEqual(actual, 'some_name_aloha')

    def test_qgeometry_q_element_add_qgeometry(self):
        """Test add_qgeometry in QGeometryTables class in
        element_handler.py."""
        design = designs.DesignPlanar()
        qgt = QGeometryTables(design)
        qgt.clear_all_tables()

        a_poly = draw.rectangle(2, 2, 0, 0)
        qgt.add_qgeometry('poly', 'my_id', dict(cl_metal=a_poly))
        table = qgt.tables

        self.assertTrue('poly' in table)
        self.assertEqual(table['poly']['component'][0], 'my_id')
        self.assertEqual(table['poly']['name'][0], 'cl_metal')
        self.assertEqual(table['poly']['geometry'][0], a_poly)
        self.assertEqual(table['poly']['layer'][0], 1)
        self.assertEqual(table['poly']['subtract'][0], False)
        self.assertEqual(table['poly']['helper'][0], False)
        self.assertEqual(table['poly']['chip'][0], 'main')
        self.assertEqual(str(table['poly']['fillet'][0]), str(np.nan))

    def test_qgeometry_q_element_clear_all_tables(self):
        """Test clear_all_tables in QGeometryTables class in
        element_handler.py."""
        design = designs.DesignPlanar()
        qgt = QGeometryTables(design)
        qgt.clear_all_tables()

        # add something to the tables to check for after clear
        a_poly = draw.rectangle(2, 2, 0, 0)
        qgt.add_qgeometry('poly', 'my_id', dict(cl_metal=a_poly))

        qgt.clear_all_tables()
        self.assertEqual(len(qgt.tables['poly'].geometry), 0)

    def test_qgeometry_q_element_delete_component_id(self):
        """Test delete_component_id in QGeometryTables class in
        element_handler.py."""
        design = designs.DesignPlanar()
        qgt = QGeometryTables(design)
        qgt.clear_all_tables()

        transmon_pocket = TransmonPocket(design, 'my_id')
        transmon_pocket.make()
        transmon_pocket.get_template_options(design)
        a_linestring = draw.LineString([[0, 0], [0, 1]])
        a_poly = draw.rectangle(2, 2, 0, 0)
        qgt.add_qgeometry('path',
                          'my_id', {'n_sprial': a_linestring},
                          width=4000)
        qgt.add_qgeometry('poly',
                          'my_id', {'n_spira_etch': a_poly},
                          subtract=True)

        self.assertEqual(len(qgt.tables['path']), 1)
        self.assertEqual(len(qgt.tables['poly']), 1)

        qgt.delete_component_id('my_id')

        self.assertEqual(len(qgt.tables['path']), 0)
        self.assertEqual(len(qgt.tables['poly']), 0)

    def test_qgeometry_get_all_unique_layers(self):
        """Test get_all_unique_layers functionality in elment_handler.py."""
        design = designs.DesignPlanar()
        qgt = QGeometryTables(design)
        qgt.clear_all_tables()

        transmon_pocket = TransmonPocket(design, 'my_id')
        transmon_pocket.make()
        transmon_pocket.get_template_options(design)
        a_linestring = draw.LineString([[0, 0], [0, 1]])
        a_poly = draw.rectangle(2, 2, 0, 0)
        qgt.add_qgeometry('path',
                          'my_id', {'n_sprial': a_linestring},
                          width=4000)
        qgt.add_qgeometry('poly',
                          'my_id', {'n_spira_etch': a_poly},
                          subtract=True)

        self.assertEqual(qgt.get_all_unique_layers('main'), [1])
        self.assertEqual(qgt.get_all_unique_layers('fake'), [])

    def test_qgeometry_q_element_get_component_bounds(self):
        """Test get_component_bounds in QGeometryTables class in
        element_handler.py."""
        design = designs.DesignPlanar()
        qgt = QGeometryTables(design)
        qgt.clear_all_tables()
        TransmonPocket(design, 'my_id')

        four_zeros = qgt.get_component_bounds('my_id')
        self.assertEqual(len(four_zeros), 4)
        for i in range(4):
            self.assertEqual(four_zeros[i], 0)

    def test_qgeometry_q_element_check_element_type(self):
        """Test check_element_type in QGeometryTables class in
        element_handler.py."""
        design = designs.DesignPlanar()
        qgt = QGeometryTables(design)
        TransmonPocket(design, 'my_id')

        self.assertTrue(qgt.check_element_type('path', log_issue=False))
        self.assertFalse(qgt.check_element_type('not-there', log_issue=False))

    def test_qgeometry_q_element_get_component(self):
        """Test get_component in QGeometryTables class in
        element_handler.py."""
        design = designs.DesignPlanar()
        qgt = QGeometryTables(design)
        qgt.clear_all_tables()
        TransmonPocket(design, 'Q1')

        rect = draw.rectangle(500, 300, 0, 0)
        geom = {'my_polygon': rect}
        qgt.add_qgeometry('poly', 'Q1', geom)

        # success results
        actual = qgt.get_component('Q1')
        self.assertEqual(len(actual), 3)
        self.assertTrue(isinstance(actual['path'], GeoDataFrame))
        self.assertTrue(isinstance(actual['poly'], GeoDataFrame))
        self.assertTrue(isinstance(actual['junction'], GeoDataFrame))

        # failure results
        actual = qgt.get_component('not-real')
        self.assertEqual(len(actual), 3)
        self.assertEqual(actual['path'], None)
        self.assertEqual(actual['poly'], None)
        self.assertEqual(actual['junction'], None)


if __name__ == '__main__':
    unittest.main(verbosity=2)
