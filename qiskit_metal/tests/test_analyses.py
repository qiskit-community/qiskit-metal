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
#pylint: disable-msg=invalid-name

"""
Qiskit Metal unit tests analyses functionality.

Created on Wed Apr 22 09:28:05 2020
@author: Jeremy D. Drysdale
"""

import unittest
import pandas as pd
import numpy as np

from qiskit_metal.analyses import lumped_capacitive
from qiskit_metal.analyses import cpw_calculations

class TestAnalyses(unittest.TestCase):
    """
    Unit test class
    """

    def setUp(self):
        """
        Setup unit test

        Args: None

        Returns: None
        """
        pass

    def tearDown(self):
        """
        Tie any loose ends

        Args: None

        Returns: None
        """
        pass

    def test_analyses_cpw_guided_wavelength(self):
        """
        Test the functionality of guided_wavelength in cpw_calculations.py

        Args: None

        Returns: None
        """
        # Test general functionality, edge cases, bad input, out of range
        self.assertEqual("TEST NOT IMPLEMENTED", 1)

    def test_analyses_cpw_lumped_cpw(self):
        """
        Test the functionality of lumped_cpw in cpw_calculations.py

        Args: None

        Returns: None
        """
        # Setup expected test results
        test_a_expected = (1.0800538577735159e-13, 3.8582810449211895e-07, 2.887792953700545e-11,
                           0.0)
        test_b_expected = (1.0800538577735159e-13, 3.858281044369713e-07, 2.887792953700545e-11,
                           0.0)
        test_c_expected = (1.0800538577735159e-13, 3.858281044369713e-07, 2.887792953700545e-11,
                           0.0)
        test_d_expected = (0.03756048636141296, 3.858281044369713e-07, 2.887792953700545e-11, 0.0)

        # Generate actual result data
        test_a_result = cpw_calculations.lumped_cpw(1000000.75, 0.25, 0.1, 0.002, 0.003)
        test_b_result = cpw_calculations.lumped_cpw(1000000.75, 0.25, 0.1, 0.002, 0.003,
                                                    dielectric_constant=15.1)
        test_c_result = cpw_calculations.lumped_cpw(1000000.75, 0.25, 0.1, 0.002, 0.003,
                                                    dielectric_constant=15.1, loss_tangent=0.1)
        test_d_result = cpw_calculations.lumped_cpw(1000000.75, 0.25, 0.1, 0.002, 0.003,
                                                    dielectric_constant=15.1, loss_tangent=0.1,
                                                    london_penetration_depth=1*10**.7)

        # Test all elements of the result data against expected data
        self.assertAlmostEqual(test_a_expected, test_a_result, places=13)
        self.assertAlmostEqual(test_b_expected, test_b_result, places=13)
        self.assertAlmostEqual(test_c_expected, test_c_result, places=13)
        self.assertAlmostEqual(test_d_expected, test_d_result, places=13)

    def test_analyses_cpw_effective_dielectric_constant(self):
        """
        Test the functionality of effective_dielectric_constant in cpw_calculations.py

        Args: None

        Returns: None
        """
        # Test general functionality, edge cases, bad input, out of range
        self.assertEqual("TEST NOT IMPLEMENTED", 1)

    def test_analyses_cpw_elliptic_int_constants(self):
        """
        Test the functionality of elliptic_int_constants in cpw_calculations.py

        Args: None

        Returns: None
        """
        # Test general functionality, edge cases, bad input, out of range
        self.assertEqual("TEST NOT IMPLEMENTED", 1)

    def test_analyses_lumped_transmon_props(self):
        """
        Test the functionality of lumped_transmon_props in lumped_capacitives.py

        Args: None

        Returns: None
        """
        # Setup expected test results
        test_a_expected = (3.2897326737094774e-12, 311949615351887.6, 0.00018137620223473302,
                           1.2170673260260538, 55134023.405734204, 55134024.62280153, 0.0)
        test_b_expected = (3.2897326737094773e-13, 3119496153518876.0, 1.81376202234733e-05,
                           0.12170673260260537, 55134024.501094796, 55134024.62280153, 0.0)
        test_c_expected = (3.289732673709477e-14, 3.1194961535188764e+16, 1.8137620223473303e-06,
                           0.012170673260260537, 55134024.610630855, 55134024.62280153, 0.0)
        test_d_expected = (3.2897326737094774e-15, 3.119496153518876e+17, 1.8137620223473301e-07,
                           0.0012170673260260537, 55134024.62158446, 55134024.62280153, 0.0)
        test_e_expected = (3.2897326737094773e-16, 3.119496153518876e+18, 1.8137620223473303e-08,
                           0.00012170673260260537, 55134024.62267982, 55134024.62280153, 0.0)
        test_f_expected = (3.289732673709477e-17, 3.1194961535188763e+19, 1.8137620223473302e-09,
                           1.2170673260260537e-05, 55134024.62278935, 55134024.62280153, 0.0)

        # Generate actual result data
        test_a_result = lumped_capacitive.transmon_props(0.0001, 0.0001)
        test_b_result = lumped_capacitive.transmon_props(0.001, 0.001)
        test_c_result = lumped_capacitive.transmon_props(0.01, 0.01)
        test_d_result = lumped_capacitive.transmon_props(0.1, 0.1)
        test_e_result = lumped_capacitive.transmon_props(1, 1)
        test_f_result = lumped_capacitive.transmon_props(10, 10)

        # Test all elements of the result data against expected data
        for i in range(7):
            self.assertEqual(test_a_expected[i], test_a_result[i])
            self.assertEqual(test_b_expected[i], test_b_result[i])
            self.assertEqual(test_c_expected[i], test_c_result[i])
            self.assertEqual(test_d_expected[i], test_d_result[i])
            self.assertEqual(test_e_expected[i], test_e_result[i])
            self.assertEqual(test_f_expected[i], test_f_result[i])

    def test_analyses_lumped_chi(self):
        """
        Test the functionality of chi in lumped_capacitives.py

        Args: None

        Returns: None
        """
        # Setup expected test results
        test_a_expected = -137.5
        test_b_expected = -275.0

        # Generate actual result data
        test_a_result = lumped_capacitive.chi(50, 30, 20, 10)
        test_b_result = lumped_capacitive.chi(100, 60, 40, 20)

        # Test all elements of the result data against expected data
        self.assertEqual(test_a_expected, test_a_result)
        self.assertEqual(test_b_expected, test_b_result)

        # need separate with's because if one works the with will bail
        with self.assertRaises(ZeroDivisionError):
            test_a_result = lumped_capacitive.chi(50, 30, 30, 10)

        with self.assertRaises(ZeroDivisionError):
            test_a_result = lumped_capacitive.chi(50, 30, 20, 30)

    #pylint: disable-msg=too-many-locals
    def test_analyses_lumped_levels_vs_ng_real_units(self):
        """
        Test the functionality of levels_vs_ng_real_units in lumped_capacitives.py

        Args: None

        Returns: None
        """
        # Setup expected test results
        test_a_expected = (8.574834762837432, -204.4199285887568, 0.00017261505126953125,
                           5869776876.184971)
        test_b_expected = (8.753670427734068, -19.467410255551684, 0.4794178009033203,
                           2113421.3926021964)
        test_c_expected = (388691.64789067156, 383543414.14295447, 774809178857568.5,
                           1.3076920925450654e-09)
        test_d_expected = (8.574834762837417, -204.41992858872464, 4.00543212890625e-05,
                           25295943204.511417)
        test_e_expected = (8.753670427746364, -19.467409975097922, 0.4790630340576172,
                           2114986.472326141)
        test_f_expected = (402900.7730357366, 340916038.71322423, 774809178857568.5,
                           1.3076920925450654e-09)

        # Generate actual result data
        test_a_results = lumped_capacitive.levels_vs_ng_real_units(100, 100)
        test_b_results = lumped_capacitive.levels_vs_ng_real_units(1000, 1000)
        test_c_results = lumped_capacitive.levels_vs_ng_real_units(0.0001, 0.0001)
        test_d_results = lumped_capacitive.levels_vs_ng_real_units(100, 100, N=25)
        test_e_results = lumped_capacitive.levels_vs_ng_real_units(1000, 1000, N=25)
        test_f_results = lumped_capacitive.levels_vs_ng_real_units(0.0001, 0.0001, N=25)

        # Test all elements of the result data against expected data
        for k in [test_a_results, test_b_results, test_c_results, test_d_results, test_e_results]:
            self.assertEqual(len(k), 4)

        for (i, j) in [(test_a_results, test_a_expected), (test_b_results, test_b_expected),
                       (test_c_results, test_c_expected), (test_d_results, test_d_expected),
                       (test_e_results, test_e_expected), (test_f_results, test_f_expected)]:
            for k in range(4):
                self.assertAlmostEqual(i[k], j[k])

        with self.assertRaises(IndexError):
            lumped_capacitive.levels_vs_ng_real_units(100, 100, N=0)

        with self.assertRaises(ValueError):
            lumped_capacitive.levels_vs_ng_real_units(100, 100, N=-10)

    def test_analyses_lumped_get_C_and_Ic(self):
        """
        Test the functionality of get_C_and_Ic in lumped_capacitives.py

        Args: None

        Returns: None
        """
        # Setup expected test results
        test_a_expected = [25639.02207938, 702.26214061]
        test_b_expected = [2866.13506128, -190.1903427]

        # Generate actual result data
        test_a_result = lumped_capacitive.get_C_and_Ic(100, 2000, 1.25, 1.75)
        test_b_result = lumped_capacitive.get_C_and_Ic(500, 1000, 1.85, 2.65)

        # Test all elements of the result data against expected data
        self.assertEqual(len(test_a_result), 2)
        self.assertEqual(len(test_b_result), 2)
        self.assertAlmostEqual(test_a_expected[0], test_a_result[0])
        self.assertAlmostEqual(test_a_expected[1], test_a_result[1])
        self.assertAlmostEqual(test_b_expected[0], test_b_result[0])
        self.assertAlmostEqual(test_b_expected[1], test_b_result[1])

    def test_analyses_lumped_cos_to_mega_and_delta(self):
        """
        Test the functionality of cos_to_mega_and_delta in lumped_capacitives.py

        Args: None

        Returns: None
        """
        # Setup expected test results
        test_a_expected = 278.9538182848156
        test_b_expected = 197.27085868098266

        # Generate actual result data
        test_a_result = lumped_capacitive.cos_to_mega_and_delta(1000, 100, 200, 200)
        test_b_result = lumped_capacitive.cos_to_mega_and_delta(1000, -100, 0.258, 200)

        # Test all elements of the result data against expected data
        self.assertAlmostEqual(test_a_expected, test_a_result)
        self.assertAlmostEqual(test_b_expected, test_b_result)

        with self.assertRaises(ZeroDivisionError):
            test_a_result = lumped_capacitive.cos_to_mega_and_delta(0, 100, 200, 200)

    def test_analyses_lumped_chargeline_T1(self):
        """
        Test the functionality of chargeline_T1 in lumped_capacitives.py

        Args: None

        Returns: None
        """
        # Setup expected test results
        test_a_expected = 1.1257909293593088e-09
        test_b_expected = 0.00012178026880088676

        # Generate actual result data
        test_a_result = lumped_capacitive.chargeline_T1(100, 20, 30)
        test_b_result = lumped_capacitive.chargeline_T1(13, 104, 1.6)

        # Test all elements of the result data against expected data
        self.assertAlmostEqual(test_a_expected, test_a_result, places=13)
        self.assertAlmostEqual(test_b_expected, test_b_result, places=13)

        with self.assertRaises(ZeroDivisionError):
            lumped_capacitive.chargeline_T1(1, 55, 0)

    def test_analyses_lumped_readin_q3d_matrix(self):
        """
        Test the functionality of readin_q3d_matrix in lumped_capacitives.py

        Args: None

        Returns: None
        """
        # Setup expected test results
        units_expected = 'farad'
        design_variation_expected = ("$BBoxL='650um' $boxH='750um' $boxL='2mm' $QubitGap='30um'" +
                                     " $QubitH='90um' $QubitL='450um' Lj_1='13nH'")

        data = {'ground_plane':[2.882900e-13, -3.254000e-14, -3.197800e-14, -4.006300e-14,
                                -4.384200e-14, -3.005300e-14],
                'Q1_bus_Q0_connector_pad':[-3.254000e-14, 4.725700e-14, -2.276500e-16,
                                           -1.269000e-14, -1.335100e-15, -1.451000e-16],
                'Q1_bus_Q2_connector_pad':[-3.197800e-14, -2.276500e-16, 4.532700e-14,
                                           -1.218000e-15, -1.155200e-14, -5.041400e-17],
                'Q1_pad_bot':[-4.006300e-14, -1.269000e-14, -1.218000e-15, 9.583100e-14,
                              -3.241500e-14, -8.366500e-15],
                'Q1_pad_top1':[-4.384200e-14, -1.335100e-15, -1.155200e-14, -3.241500e-14,
                               9.132000e-14, -1.019900e-15],
                'Q1_readout_connector_pad':[-3.005300e-14, -1.451000e-16, -5.041400e-17,
                                            -8.366500e-15, -1.019900e-15, 3.988400e-14]}
        df_cmat_expected = pd.DataFrame(data, index=['ground_plane', 'Q1_bus_Q0_connector_pad',
                                                     'Q1_bus_Q2_connector_pad', 'Q1_pad_bot',
                                                     'Q1_pad_top1', 'Q1_readout_connector_pad'])

        data = {'ground_plane':[0, 0, 0, 0, 0, 0],
                'Q1_bus_Q0_connector_pad':[0, 0, 0, 0, 0, 0],
                'Q1_bus_Q2_connector_pad':[0, 0, 0, 0, 0, 0],
                'Q1_pad_bot':[0, 0, 0, 0, 0, 0],
                'Q1_pad_top1':[0, 0, 0, 0, 0, 0],
                'Q1_readout_connector_pad':[0, 0, 0, 0, 0, 0]}
        df_cond_expected = pd.DataFrame(data, index=['ground_plane', 'Q1_bus_Q0_connector_pad',
                                                     'Q1_bus_Q2_connector_pad', 'Q1_pad_bot',
                                                     'Q1_pad_top1', 'Q1_readout_connector_pad'])

        # Generate actual result data
        generated = lumped_capacitive.readin_q3d_matrix(r'test_data\q3d_example.txt')
        return_size_result = len(generated)
        df_cmat_result = generated[0]
        units_result = generated[1]
        design_variation_result = generated[2]
        df_cond_result = generated[3]

        # Test all elements of the result data against expected data
        self.assertEqual(4, return_size_result)
        self.assertEqual(units_expected, units_result)
        self.assertEqual(design_variation_expected, design_variation_result)

        data_points = df_cmat_expected['ground_plane'].size
        for i in range(data_points):
            for j in ['ground_plane', 'Q1_bus_Q0_connector_pad', 'Q1_bus_Q2_connector_pad',
                      'Q1_pad_bot', 'Q1_pad_top1', 'Q1_readout_connector_pad']:
                self.assertAlmostEqual(df_cmat_expected[j][i], df_cmat_result[j][i], places=12)

        data_points = df_cond_expected['ground_plane'].size
        for i in range(data_points):
            for j in ['ground_plane', 'Q1_bus_Q0_connector_pad', 'Q1_bus_Q2_connector_pad',
                      'Q1_pad_bot', 'Q1_pad_top1', 'Q1_readout_connector_pad']:
                self.assertAlmostEqual(df_cond_expected[j][i], df_cond_result[j][i], places=12)

    #pylint: disable-msg=too-many-locals
    def test_analyses_lumped_load_q3d_capacitance_matrix(self):
        """
        Test the functionality of load_q3d_capacitance_matrix in lumped_capacitives.py

        Args: None

        Returns: None
        """
        # Setup expected test results
        test_a_return_size_expected = 4
        test_a_user_units_expected = 'fF'
        test_a_design_variation_expected = ("$BBoxL='650um' $boxH='750um' $boxL='2mm' " +
                                            "$QubitGap='30um' $QubitH='90um' $QubitL='450um' " +
                                            "Lj_1='13nH'")

        test_b_return_size_expected = 4
        test_b_user_units_expected = 'pF'
        test_b_design_variation_expected = ("$BBoxL='650um' $boxH='750um' $boxL='2mm' " +
                                            "$QubitGap='30um' $QubitH='90um' $QubitL='450um' " +
                                            "Lj_1='13nH'")

        data = {'ground_plane':[288.290, -32.540, -31.978, -40.063, -43.842, -30.053],
                'Q1_bus_Q0_connector_pad':[-32.54000, 47.25700, -0.22765, -12.69000, -1.33510,
                                           -0.14510],
                'Q1_bus_Q2_connector_pad':[-31.978000, -0.227650, 45.327000, -1.218000, -11.552000,
                                           -0.050414],
                'Q1_pad_bot':[-40.0630, -12.6900, -1.2180, 95.8310, -32.4150, -8.3665],
                'Q1_pad_top1':[-43.8420, -1.3351, -11.5520, -32.4150, 91.3200, -1.0199],
                'Q1_readout_connector_pad':[-30.053000, -0.145100, -0.050414, -8.366500, -1.019900,
                                            39.884000]}
        test_a_df_cmat_expected = pd.DataFrame(data, index=['ground_plane',
                                                            'Q1_bus_Q0_connector_pad',
                                                            'Q1_bus_Q2_connector_pad',
                                                            'Q1_pad_bot', 'Q1_pad_top1',
                                                            'Q1_readout_connector_pad'])

        data = {'ground_plane':[0, 0, 0, 0, 0, 0],
                'Q1_bus_Q0_connector_pad':[0, 0, 0, 0, 0, 0],
                'Q1_bus_Q2_connector_pad':[0, 0, 0, 0, 0, 0],
                'Q1_pad_bot':[0, 0, 0, 0, 0, 0],
                'Q1_pad_top1':[0, 0, 0, 0, 0, 0],
                'Q1_readout_connector_pad':[0, 0, 0, 0, 0, 0]}
        test_a_df_cond_expected = pd.DataFrame(data, index=['ground_plane',
                                                            'Q1_bus_Q0_connector_pad',
                                                            'Q1_bus_Q2_connector_pad',
                                                            'Q1_pad_bot', 'Q1_pad_top1',
                                                            'Q1_readout_connector_pad'])

        data = {'ground_plane':[0.288290, -0.032540, -0.031978, -0.040063, -0.043842, -0.030053],
                'Q1_bus_Q0_connector_pad':[-0.032540, 0.047257, -0.000228, -0.012690, -0.001335,
                                           -0.000145],
                'Q1_bus_Q2_connector_pad':[-0.031978, -0.000228, 0.045327, -0.001218, -0.011552,
                                           -0.000050],
                'Q1_pad_bot':[-0.040063, -0.012690, -0.001218, 0.095831, -0.032415, -0.008367],
                'Q1_pad_top1':[-0.043842, -0.001335, -0.011552, -0.032415, 0.091320, -0.001020],
                'Q1_readout_connector_pad':[-0.030053, -0.000145, -0.000050, -0.008367, -0.001020,
                                            0.039884]}
        test_b_df_cmat_expected = pd.DataFrame(data, index=['ground_plane',
                                                            'Q1_bus_Q0_connector_pad',
                                                            'Q1_bus_Q2_connector_pad',
                                                            'Q1_pad_bot', 'Q1_pad_top1',
                                                            'Q1_readout_connector_pad'])

        data = {'ground_plane':[0, 0, 0, 0, 0, 0],
                'Q1_bus_Q0_connector_pad':[0, 0, 0, 0, 0, 0],
                'Q1_bus_Q2_connector_pad':[0, 0, 0, 0, 0, 0],
                'Q1_pad_bot':[0, 0, 0, 0, 0, 0],
                'Q1_pad_top1':[0, 0, 0, 0, 0, 0],
                'Q1_readout_connector_pad':[0, 0, 0, 0, 0, 0]}
        test_b_df_cond_expected = pd.DataFrame(data, index=['ground_plane',
                                                            'Q1_bus_Q0_connector_pad',
                                                            'Q1_bus_Q2_connector_pad',
                                                            'Q1_pad_bot', 'Q1_pad_top1',
                                                            'Q1_readout_connector_pad'])

        # Generate actual result data
        test_a_result = lumped_capacitive.load_q3d_capacitance_matrix(r'test_data\q3d_example.txt',
                                                                      _disp=False)
        test_b_result = lumped_capacitive.load_q3d_capacitance_matrix(r'test_data\q3d_example.txt',
                                                                      user_units='pF', _disp=False)

        test_a_return_size_result = len(test_a_result)
        test_a_df_cmat_result = test_a_result[0]
        test_a_user_units_result = test_a_result[1]
        test_a_design_variation_result = test_a_result[2]
        test_a_df_cond_result = test_a_result[3]

        test_b_return_size_result = len(test_b_result)
        test_b_df_cmat_result = test_b_result[0]
        test_b_user_units_result = test_b_result[1]
        test_b_design_variation_result = test_b_result[2]
        test_b_df_cond_result = test_b_result[3]

        # Test all elements of the result data against expected data
        self.assertEqual(test_a_return_size_expected, test_a_return_size_result)
        self.assertEqual(test_a_user_units_expected, test_a_user_units_result)
        self.assertEqual(test_a_design_variation_expected, test_a_design_variation_result)

        self.assertEqual(test_b_return_size_expected, test_b_return_size_result)
        self.assertEqual(test_b_user_units_expected, test_b_user_units_result)
        self.assertEqual(test_b_design_variation_expected, test_b_design_variation_result)

        data_points = test_a_df_cmat_expected['ground_plane'].size
        for i in range(data_points):
            for j in ['ground_plane', 'Q1_bus_Q0_connector_pad', 'Q1_bus_Q2_connector_pad',
                      'Q1_pad_bot', 'Q1_pad_top1', 'Q1_readout_connector_pad']:
                self.assertAlmostEqual(test_a_df_cmat_expected[j][i], test_a_df_cmat_result[j][i],
                                       places=3)

        data_points = test_a_df_cond_expected['ground_plane'].size
        for i in range(data_points):
            for j in ['ground_plane', 'Q1_bus_Q0_connector_pad', 'Q1_bus_Q2_connector_pad',
                      'Q1_pad_bot', 'Q1_pad_top1', 'Q1_readout_connector_pad']:
                self.assertAlmostEqual(test_a_df_cond_expected[j][i], test_a_df_cond_result[j][i],
                                       places=3)

        data_points = test_b_df_cmat_expected['ground_plane'].size
        for i in range(data_points):
            for j in ['ground_plane', 'Q1_bus_Q0_connector_pad', 'Q1_bus_Q2_connector_pad',
                      'Q1_pad_bot', 'Q1_pad_top1', 'Q1_readout_connector_pad']:
                self.assertAlmostEqual(test_b_df_cmat_expected[j][i], test_b_df_cmat_result[j][i],
                                       places=3)

        data_points = test_b_df_cond_expected['ground_plane'].size
        for i in range(data_points):
            for j in ['ground_plane', 'Q1_bus_Q0_connector_pad', 'Q1_bus_Q2_connector_pad',
                      'Q1_pad_bot', 'Q1_pad_top1', 'Q1_readout_connector_pad']:
                self.assertAlmostEqual(test_b_df_cond_expected[j][i], test_b_df_cond_result[j][i],
                                       places=3)

    def test_analyses_lumped_move_index_to(self):
        """
        Test the functionality of move_index_to in lumped_capacitives.py

        Args: None

        Returns: None
        """
        # Setup expected test results
        test_a_expected = [0, 2, 3, 1, 4]
        test_b_expected = [1, 2, 3, 4, 0]
        test_c_expected = [0, 3, 1, 2, 4]

        # Generate actual result data
        test_a_result = lumped_capacitive.move_index_to(1, 3, 5)
        test_b_result = lumped_capacitive.move_index_to(0, 4, 5)
        test_c_result = lumped_capacitive.move_index_to(3, 1, 5)

        # Test all elements of the result data against expected data
        self.assertTrue(np.array_equal(test_a_expected, test_a_result))
        self.assertTrue(np.array_equal(test_b_expected, test_b_result))
        self.assertTrue(np.array_equal(test_c_expected, test_c_result))

        with self.assertRaises(IndexError):
            lumped_capacitive.move_index_to(3, 1, -5)

        with self.assertRaises(TypeError):
            lumped_capacitive.move_index_to(3, 1.5, 5)

    def test_analyses_lumped_df_reorder_matrix_basis(self):
        """
        Test the functionality of df_reorder_matrix_basis in lumped_capacitives.py

        Args: None

        Returns: None
        """
        # Setup expected test results
        data = {'ground_plane':[2.882900e-13, -3.254000e-14, -3.197800e-14, -4.006300e-14,
                                -4.384200e-14, -3.005300e-14],
                'Q1_bus_Q2_connector_pad':[-3.197800e-14, -2.276500e-16, 4.532700e-14,
                                           -1.218000e-15, -1.155200e-14, -5.041400e-17],
                'Q1_pad_bot':[-4.006300e-14, -1.269000e-14, -1.218000e-15, 9.583100e-14,
                              -3.241500e-14, -8.366500e-15],
                'Q1_bus_Q0_connector_pad':[-3.254000e-14, 4.725700e-14, -2.276500e-16,
                                           -1.269000e-14, -1.335100e-15, -1.451000e-16],
                'Q1_pad_top1':[-4.384200e-14, -1.335100e-15, -1.155200e-14, -3.241500e-14,
                               9.132000e-14, -1.019900e-15],
                'Q1_readout_connector_pad':[-3.005300e-14, -1.451000e-16, -5.041400e-17,
                                            -8.366500e-15, -1.019900e-15, 3.988400e-14]}
        test_a_expected = pd.DataFrame(data, index=['ground_plane', 'Q1_bus_Q0_connector_pad',
                                                    'Q1_bus_Q2_connector_pad', 'Q1_pad_bot',
                                                    'Q1_pad_top1', 'Q1_readout_connector_pad'])

        data = {'Q1_pad_top1':[-4.384200e-14, -1.335100e-15, -1.155200e-14, -3.241500e-14,
                               9.132000e-14, -1.019900e-15],
                'ground_plane':[2.882900e-13, -3.254000e-14, -3.197800e-14, -4.006300e-14,
                                -4.384200e-14, -3.005300e-14],
                'Q1_bus_Q0_connector_pad':[-3.254000e-14, 4.725700e-14, -2.276500e-16,
                                           -1.269000e-14, -1.335100e-15, -1.451000e-16],
                'Q1_bus_Q2_connector_pad':[-3.197800e-14, -2.276500e-16, 4.532700e-14,
                                           -1.218000e-15, -1.155200e-14, -5.041400e-17],
                'Q1_pad_bot':[-4.006300e-14, -1.269000e-14, -1.218000e-15, 9.583100e-14,
                              -3.241500e-14, -8.366500e-15],
                'Q1_readout_connector_pad':[-3.005300e-14, -1.451000e-16, -5.041400e-17,
                                            -8.366500e-15, -1.019900e-15, 3.988400e-14]}
        test_b_expected = pd.DataFrame(data, index=['ground_plane', 'Q1_bus_Q0_connector_pad',
                                                    'Q1_bus_Q2_connector_pad', 'Q1_pad_bot',
                                                    'Q1_pad_top1', 'Q1_readout_connector_pad'])

        # Generate actual result data
        df_a = lumped_capacitive.readin_q3d_matrix(r'test_data\q3d_example.txt')[0]
        df_b = lumped_capacitive.readin_q3d_matrix(r'test_data\q3d_example.txt')[0]

        test_a_result = lumped_capacitive.df_reorder_matrix_basis(df_a, 1, 3)
        test_b_result = lumped_capacitive.df_reorder_matrix_basis(df_b, 4, 0)

        # Test all elements of the result data against expected data
        data_points = test_a_result['ground_plane'].size
        for i in range(data_points):
            for j in ['ground_plane', 'Q1_bus_Q0_connector_pad', 'Q1_bus_Q2_connector_pad',
                      'Q1_pad_bot', 'Q1_pad_top1', 'Q1_readout_connector_pad']:
                self.assertAlmostEqual(test_a_expected[j][i], test_a_result[j][i], places=12)

        data_points = test_b_result['ground_plane'].size
        for i in range(data_points):
            for j in ['ground_plane', 'Q1_bus_Q0_connector_pad', 'Q1_bus_Q2_connector_pad',
                      'Q1_pad_bot', 'Q1_pad_top1', 'Q1_readout_connector_pad']:
                self.assertAlmostEqual(test_b_expected[j][i], test_b_result[j][i], places=12)

        with self.assertRaises(IndexError):
            test_a_result = lumped_capacitive.df_reorder_matrix_basis(df_a, 1, 35)

if __name__ == '__main__':
    unittest.main(verbosity=2)
