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

#pylint: disable-msg=unnecessary-pass
#pylint: disable-msg=broad-except
"""
Qiskit Metal unit tests analyses functionality.

Created on Wed Apr 22 09:28:05 2020
@author: Jeremy D. Drysdale
"""

from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from qiskit_metal.analyses.quantization import lumped_capacitive
from qiskit_metal.analyses.hamiltonian.analytic_transmon import Hcpb
from qiskit_metal.analyses.em import cpw_calculations
from qiskit_metal.analyses.scan_options.scanning import Scanning
from qiskit_metal.tests.assertions import AssertionsMixin
from qiskit_metal import designs

TEST_DATA = Path(__file__).parent / "test_data"


class TestAnalyses(unittest.TestCase, AssertionsMixin):
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

    def test_analyses_instantiate_hcpb(self):
        """
        Test instantiation of Hcpb in analytic_transmon.py
        """
        try:
            Hcpb()
        except Exception:
            self.fail("Hcpb failed")

    def test_analyses_instantiate_scanning(self):
        """
        Test instantiation of Scanning in analytic_transmon.py
        """
        try:
            design = designs.DesignPlanar()
            Scanning(design)
        except Exception:
            self.fail("Scanning failed")

    def test_analyses_cpw_guided_wavelength(self):
        """
        Test the functionality of guided_wavelength in cpw_calculations.py
        """
        # Setup expected test results
        test_a_expected = (0.024356252567915772, 2.4617087473867807,
                           0.49998001152009985)
        test_b_expected = (0.029017096287462227, 2.459879883274635,
                           0.49994733413732906)
        test_c_expected = (0.021364843468278626, 2.8063861122606597,
                           0.49998001152009985)
        test_d_expected = (0.025454109889274948, 2.804206147418523,
                           0.49994733413732906)

        # Generate actual result data
        test_a_actual = cpw_calculations.guided_wavelength(
            5 * 10**9, 10 * 10**-6, 6 * 10**-6, 760 * 10**-6, 200 * 10**-9)
        test_b_actual = cpw_calculations.guided_wavelength(
            4.2 * 10**9, 9.8 * 10**-6, 4.8 * 10**-6, 420 * 10**-6, 180 * 10**-9)
        test_c_actual = cpw_calculations.guided_wavelength(
            5 * 10**9,
            10 * 10**-6,
            6 * 10**-6,
            760 * 10**-6,
            200 * 10**-9,
            dielectric_constant=15.2)
        test_d_actual = cpw_calculations.guided_wavelength(
            4.2 * 10**9,
            9.8 * 10**-6,
            4.8 * 10**-6,
            420 * 10**-6,
            180 * 10**-9,
            dielectric_constant=15.2)

        # Test all elements of the result data against expected data
        for (actual, expected) in [(test_a_actual, test_a_expected),
                                   (test_b_actual, test_b_expected),
                                   (test_c_actual, test_c_expected),
                                   (test_d_actual, test_d_expected)]:
            self.assertIterableAlmostEqual(actual, expected)

    def test_analyses_cpw_lumped_cpw(self):
        """
        Test the functionality of lumped_cpw in cpw_calculations.py
        """
        # Setup expected test results
        test_a_expected = (1.0800538577735159e-13, 3.8582810449211895e-07,
                           2.887792953700545e-11, 0.0, 115.58830719541695,
                           1.000000000244218, 2.887792953700545e-11)
        test_b_expected = (1.0800538577735159e-13, 3.858281044369713e-07,
                           2.887792953700545e-11, 0.0, 115.58830718715625,
                           1.0000000003871512, 2.887792953700545e-11)
        test_c_expected = (1.0800538577735159e-13, 3.858281044369713e-07,
                           2.887792953700545e-11, 0.0, 115.58830718715625,
                           1.0000000003871512, 2.887792953700545e-11)
        test_d_expected = (0.03756048636141296, 3.858281044369713e-07,
                           2.887792953700545e-11, 0.0, 115.58830718715625,
                           1.0000000003871512, 2.887792953700545e-11)

        # Generate actual result data
        test_a_result = cpw_calculations.lumped_cpw(1000000.75, 0.25, 0.1,
                                                    0.002, 0.003)
        test_b_result = cpw_calculations.lumped_cpw(1000000.75,
                                                    0.25,
                                                    0.1,
                                                    0.002,
                                                    0.003,
                                                    dielectric_constant=15.1)
        test_c_result = cpw_calculations.lumped_cpw(1000000.75,
                                                    0.25,
                                                    0.1,
                                                    0.002,
                                                    0.003,
                                                    dielectric_constant=15.1,
                                                    loss_tangent=0.1)
        test_d_result = cpw_calculations.lumped_cpw(1000000.75,
                                                    0.25,
                                                    0.1,
                                                    0.002,
                                                    0.003,
                                                    dielectric_constant=15.1,
                                                    loss_tangent=0.1,
                                                    london_penetration_depth=1 *
                                                    10**.7)

        # Test all elements of the result data against expected data
        self.assertIterableAlmostEqual(test_a_expected, test_a_result)
        self.assertIterableAlmostEqual(test_b_expected, test_b_result)
        self.assertIterableAlmostEqual(test_c_expected, test_c_result)
        self.assertIterableAlmostEqual(test_d_expected, test_d_result)

    def test_analyses_cpw_effective_dielectric_constant(self):
        """
        Test the functionality of effective_dielectric_constant in cpw_calculations.py
        """
        # Generate actual result data
        test_a_actual = cpw_calculations.effective_dielectric_constant(
            5 * 10**9, 10 * 10**-6, 6 * 10**-6, 760 * 10**-6, 200 * 10**-9, 1.3,
            0.2, 1.3)
        test_b_actual = cpw_calculations.effective_dielectric_constant(
            4.8 * 10**9, 9.6 * 10**-6, 5.2 * 10**-6, 420 * 10**-6, 200 * 10**-9,
            1.3, 0.2, 1.3)
        test_c_actual = cpw_calculations.effective_dielectric_constant(
            4.8 * 10**9,
            9.6 * 10**-6,
            5.2 * 10**-6,
            420 * 10**-6,
            200 * 10**-9,
            1.3,
            0.2,
            1.3,
            eRD=200)

        # Test all elements of the result data against expected data
        for (actual, expected) in [(test_a_actual, 3.5771424204599436),
                                   (test_b_actual, 3.5442491595505388),
                                   (test_c_actual, 14.87179231388151)]:
            self.assertAlmostEqual(actual, expected, places=13)

        with self.assertRaises(ZeroDivisionError):
            test_a_actual = cpw_calculations.effective_dielectric_constant(
                5 * 10**9, 10 * 10**-6, 0, 760 * 10**-6, 200 * 10**-9, 1.3, 0.2,
                1.3)

        with self.assertRaises(ZeroDivisionError):
            test_a_actual = cpw_calculations.effective_dielectric_constant(
                5 * 10**9, 10 * 10**-6, 6 * 10**-6, 0, 200 * 10**-9, 1.3, 0.2,
                1.3)

    def test_analyses_cpw_elliptic_int_constants(self):
        """
        Test the functionality of elliptic_int_constants in cpw_calculations.py
        """
        # Setup expected test results
        test_a_expected = (1.8173686928723873, 2.536427762586688,
                           1.8173447681250923, 2.5364957731769597)
        test_b_expected = (1.8451651823831046, 2.462845861327711,
                           1.8451017251588104, 2.4630023824949374)

        # Generate actual result data
        test_a_actual = cpw_calculations.elliptic_int_constants(
            10 * 10**-6, 6 * 10**-6, 760 * 10**-6)
        test_b_actual = cpw_calculations.elliptic_int_constants(
            9.2 * 10**-6, 4.8 * 10**-6, 420 * 10**-6)

        # Test all elements of the result data against expected data
        for (actual, expected) in [(test_a_actual, test_a_expected),
                                   (test_b_actual, test_b_expected)]:
            self.assertIterableAlmostEqual(actual, expected)

        with self.assertRaises(ZeroDivisionError):
            cpw_calculations.elliptic_int_constants(0, 0, 0)

    def test_analyses_lumped_transmon_props(self):
        """
        Test the functionality of lumped_transmon_props in lumped_capacitives.py
        """
        # Setup expected test results
        test_a_expected = (3.2897326737094774e-12, 311949615351887.6,
                           0.00018137620223473302, 1.2170673260260538,
                           55134023.405734204, 55134024.62280153, 0.0)
        test_b_expected = (3.2897326737094773e-13, 3119496153518876.0,
                           1.81376202234733e-05, 0.12170673260260537,
                           55134024.501094796, 55134024.62280153, 0.0)
        test_c_expected = (3.289732673709477e-14, 3.1194961535188764e+16,
                           1.8137620223473303e-06, 0.012170673260260537,
                           55134024.610630855, 55134024.62280153, 0.0)
        test_d_expected = (3.2897326737094774e-15, 3.119496153518876e+17,
                           1.8137620223473301e-07, 0.0012170673260260537,
                           55134024.62158446, 55134024.62280153, 0.0)
        test_e_expected = (3.2897326737094773e-16, 3.119496153518876e+18,
                           1.8137620223473303e-08, 0.00012170673260260537,
                           55134024.62267982, 55134024.62280153, 0.0)
        test_f_expected = (3.289732673709477e-17, 3.1194961535188763e+19,
                           1.8137620223473302e-09, 1.2170673260260537e-05,
                           55134024.62278935, 55134024.62280153, 0.0)

        # Generate actual result data
        test_a_result = lumped_capacitive.transmon_props(0.0001, 0.0001)
        test_b_result = lumped_capacitive.transmon_props(0.001, 0.001)
        test_c_result = lumped_capacitive.transmon_props(0.01, 0.01)
        test_d_result = lumped_capacitive.transmon_props(0.1, 0.1)
        test_e_result = lumped_capacitive.transmon_props(1, 1)
        test_f_result = lumped_capacitive.transmon_props(10, 10)

        # Test all elements of the result data against expected data
        self.assertEqual(test_a_expected, test_a_result)
        self.assertEqual(test_b_expected, test_b_result)
        self.assertEqual(test_c_expected, test_c_result)
        self.assertEqual(test_d_expected, test_d_result)
        self.assertEqual(test_e_expected, test_e_result)
        self.assertEqual(test_f_expected, test_f_result)

    def test_analyses_lumped_chi(self):
        """
        Test the functionality of chi in lumped_capacitives.py
        """
        # Generate actual result data
        test_a_result = lumped_capacitive.chi(50, 30, 20, 10)
        test_b_result = lumped_capacitive.chi(100, 60, 40, 20)

        # Test all elements of the result data against expected data
        self.assertEqual(-137.5, test_a_result)
        self.assertEqual(-275.0, test_b_result)

        # need separate with's because if one works the with will bail
        with self.assertRaises(ZeroDivisionError):
            test_a_result = lumped_capacitive.chi(50, 30, 30, 10)

        with self.assertRaises(ZeroDivisionError):
            test_a_result = lumped_capacitive.chi(50, 30, 20, 30)

    #pylint: disable-msg=too-many-locals
    def test_analyses_lumped_levels_vs_ng_real_units(self):
        """
        Test the functionality of levels_vs_ng_real_units in lumped_capacitives.py
        """
        # Setup expected test results
        test_a_expected = (388.69198590629856, 383542.9078924127,
                           774759511877.3142, 1.30777592387123e-06)
        test_b_expected = (776.6068552699635, 766320.2586084654,
                           1548045428680.8086, 6.545104023767585e-07)
        test_c_expected = (388691.64789067156, 383543414.14295447,
                           774809178857568.5, 1.3076920925450654e-09)
        test_d_expected = (402.9047503275388, 340910.07369285496,
                           774759511877.3142, 1.30777592387123e-06)
        test_e_expected = (804.9985387148533, 681147.9428256081,
                           1548045428680.8086, 6.545104023767585e-07)
        test_f_expected = (402900.7730357366, 340916038.71322423,
                           774809178857568.5, 1.3076920925450654e-09)

        # Generate actual result data
        test_a_results = lumped_capacitive.levels_vs_ng_real_units(0.1, 0.1)
        test_b_results = lumped_capacitive.levels_vs_ng_real_units(
            0.05005, 0.05005)
        test_c_results = lumped_capacitive.levels_vs_ng_real_units(
            0.0001, 0.0001)
        test_d_results = lumped_capacitive.levels_vs_ng_real_units(0.1,
                                                                   0.1,
                                                                   N=25)
        test_e_results = lumped_capacitive.levels_vs_ng_real_units(0.05005,
                                                                   0.05005,
                                                                   N=25)
        test_f_results = lumped_capacitive.levels_vs_ng_real_units(0.0001,
                                                                   0.0001,
                                                                   N=25)

        # Test all elements of the result data against expected data
        for k in [
                test_a_results, test_b_results, test_c_results, test_d_results,
                test_e_results
        ]:
            self.assertEqual(len(k), 4)

        for (i, j) in [(test_a_results, test_a_expected),
                       (test_b_results, test_b_expected),
                       (test_c_results, test_c_expected),
                       (test_d_results, test_d_expected),
                       (test_e_results, test_e_expected),
                       (test_f_results, test_f_expected)]:
            self.assertIterableAlmostEqual(i, j, rel_tol=1e-6)

        with self.assertRaises(IndexError):
            lumped_capacitive.levels_vs_ng_real_units(100, 100, N=0)

        with self.assertRaises(ValueError):
            lumped_capacitive.levels_vs_ng_real_units(100, 100, N=-10)

    def test_analyses_lumped_get_c_and_ic(self):
        """
        Test the functionality of get_C_and_Ic in lumped_capacitives.py
        """
        # Setup expected test results
        test_a_expected = [33.38125825, -0.61217795]

        # Generate actual result data
        test_a_result = lumped_capacitive.get_C_and_Ic(0.1, 0.2, 1.25, 1.75)

        # Test all elements of the result data against expected data
        self.assertEqual(len(test_a_result), 2)
        self.assertAlmostEqualRel(test_a_expected[0],
                                  test_a_result[0],
                                  rel_tol=1e-6)
        self.assertAlmostEqualRel(test_a_expected[1],
                                  test_a_result[1],
                                  rel_tol=1e-6)

    def test_analyses_lumped_cos_to_mega_and_delta(self):
        """
        Test the functionality of cos_to_mega_and_delta in lumped_capacitives.py
        """
        # Generate actual result data
        test_a_result = lumped_capacitive.cos_to_mega_and_delta(
            1000, 100, 200, 200)
        test_b_result = lumped_capacitive.cos_to_mega_and_delta(
            1000, -100, 0.258, 200)

        # Test all elements of the result data against expected data
        self.assertAlmostEqual(278.9538182848156, test_a_result)
        self.assertAlmostEqual(197.27085868098266, test_b_result)

        with self.assertRaises(ZeroDivisionError):
            test_a_result = lumped_capacitive.cos_to_mega_and_delta(
                0, 100, 200, 200)

    def test_analyses_lumped_chargeline_t1(self):
        """
        Test the functionality of chargeline_T1 in lumped_capacitives.py
        """
        # Generate actual result data
        test_a_result = lumped_capacitive.chargeline_T1(100, 20, 30)
        test_b_result = lumped_capacitive.chargeline_T1(13, 104, 1.6)

        # Test all elements of the result data against expected data
        self.assertAlmostEqual(1.1257909293593088e-09, test_a_result, places=13)
        self.assertAlmostEqual(0.00012178026880088676, test_b_result, places=13)

        with self.assertRaises(ZeroDivisionError):
            lumped_capacitive.chargeline_T1(1, 55, 0)

    def test_analyses_lumped_readin_q3d_matrix(self):
        """
        Test the functionality of readin_q3d_matrix in lumped_capacitives.py
        """
        # Setup expected test results
        units_expected = 'farad'
        design_variation_expected = (
            "$BBoxL='650um' $boxH='750um' $boxL='2mm' $QubitGap='30um'" +
            " $QubitH='90um' $QubitL='450um' Lj_1='13nH'")

        data = {
            'ground_plane': [
                2.882900e-13, -3.254000e-14, -3.197800e-14, -4.006300e-14,
                -4.384200e-14, -3.005300e-14
            ],
            'Q1_bus_Q0_connector_pad': [
                -3.254000e-14, 4.725700e-14, -2.276500e-16, -1.269000e-14,
                -1.335100e-15, -1.451000e-16
            ],
            'Q1_bus_Q2_connector_pad': [
                -3.197800e-14, -2.276500e-16, 4.532700e-14, -1.218000e-15,
                -1.155200e-14, -5.041400e-17
            ],
            'Q1_pad_bot': [
                -4.006300e-14, -1.269000e-14, -1.218000e-15, 9.583100e-14,
                -3.241500e-14, -8.366500e-15
            ],
            'Q1_pad_top1': [
                -4.384200e-14, -1.335100e-15, -1.155200e-14, -3.241500e-14,
                9.132000e-14, -1.019900e-15
            ],
            'Q1_readout_connector_pad': [
                -3.005300e-14, -1.451000e-16, -5.041400e-17, -8.366500e-15,
                -1.019900e-15, 3.988400e-14
            ]
        }
        df_cmat_expected = pd.DataFrame(data,
                                        index=[
                                            'ground_plane',
                                            'Q1_bus_Q0_connector_pad',
                                            'Q1_bus_Q2_connector_pad',
                                            'Q1_pad_bot', 'Q1_pad_top1',
                                            'Q1_readout_connector_pad'
                                        ])

        data = {
            'ground_plane': [0, 0, 0, 0, 0, 0],
            'Q1_bus_Q0_connector_pad': [0, 0, 0, 0, 0, 0],
            'Q1_bus_Q2_connector_pad': [0, 0, 0, 0, 0, 0],
            'Q1_pad_bot': [0, 0, 0, 0, 0, 0],
            'Q1_pad_top1': [0, 0, 0, 0, 0, 0],
            'Q1_readout_connector_pad': [0, 0, 0, 0, 0, 0]
        }
        df_cond_expected = pd.DataFrame(data,
                                        index=[
                                            'ground_plane',
                                            'Q1_bus_Q0_connector_pad',
                                            'Q1_bus_Q2_connector_pad',
                                            'Q1_pad_bot', 'Q1_pad_top1',
                                            'Q1_readout_connector_pad'
                                        ])

        # Generate actual result data
        generated = lumped_capacitive.readin_q3d_matrix(TEST_DATA /
                                                        'q3d_example.txt')
        return_size_result = len(generated)
        df_cmat_result = generated[0]
        units_result = generated[1]
        design_variation_result = generated[2]
        df_cond_result = generated[3]

        # Test all elements of the result data against expected data
        self.assertEqual(4, return_size_result)
        self.assertEqual(units_expected, units_result)
        self.assertEqual(design_variation_expected, design_variation_result)

        for j in [
                'ground_plane', 'Q1_bus_Q0_connector_pad',
                'Q1_bus_Q2_connector_pad', 'Q1_pad_bot', 'Q1_pad_top1',
                'Q1_readout_connector_pad'
        ]:
            self.assertIterableAlmostEqual(df_cmat_expected[j],
                                           df_cmat_result[j])

        for j in [
                'ground_plane', 'Q1_bus_Q0_connector_pad',
                'Q1_bus_Q2_connector_pad', 'Q1_pad_bot', 'Q1_pad_top1',
                'Q1_readout_connector_pad'
        ]:
            self.assertIterableAlmostEqual(df_cond_expected[j],
                                           df_cond_result[j])

    #pylint: disable-msg=too-many-locals
    def test_analyses_lumped_load_q3d_capacitance_matrix(self):
        """
        Test the functionality of load_q3d_capacitance_matrix in lumped_capacitives.py
        """
        # Setup expected test results
        test_a_design_variation_expected = (
            "$BBoxL='650um' $boxH='750um' $boxL='2mm' " +
            "$QubitGap='30um' $QubitH='90um' $QubitL='450um' " + "Lj_1='13nH'")

        test_b_design_variation_expected = (
            "$BBoxL='650um' $boxH='750um' $boxL='2mm' " +
            "$QubitGap='30um' $QubitH='90um' $QubitL='450um' " + "Lj_1='13nH'")

        data = {
            'ground_plane': [
                288.290, -32.540, -31.978, -40.063, -43.842, -30.053
            ],
            'Q1_bus_Q0_connector_pad': [
                -32.54000, 47.25700, -0.22765, -12.69000, -1.33510, -0.14510
            ],
            'Q1_bus_Q2_connector_pad': [
                -31.978000, -0.227650, 45.327000, -1.218000, -11.552000,
                -0.050414
            ],
            'Q1_pad_bot': [
                -40.0630, -12.6900, -1.2180, 95.8310, -32.4150, -8.3665
            ],
            'Q1_pad_top1': [
                -43.8420, -1.3351, -11.5520, -32.4150, 91.3200, -1.0199
            ],
            'Q1_readout_connector_pad': [
                -30.053000, -0.145100, -0.050414, -8.366500, -1.019900,
                39.884000
            ]
        }
        test_a_df_cmat_expected = pd.DataFrame(data,
                                               index=[
                                                   'ground_plane',
                                                   'Q1_bus_Q0_connector_pad',
                                                   'Q1_bus_Q2_connector_pad',
                                                   'Q1_pad_bot', 'Q1_pad_top1',
                                                   'Q1_readout_connector_pad'
                                               ])

        data = {
            'ground_plane': [0, 0, 0, 0, 0, 0],
            'Q1_bus_Q0_connector_pad': [0, 0, 0, 0, 0, 0],
            'Q1_bus_Q2_connector_pad': [0, 0, 0, 0, 0, 0],
            'Q1_pad_bot': [0, 0, 0, 0, 0, 0],
            'Q1_pad_top1': [0, 0, 0, 0, 0, 0],
            'Q1_readout_connector_pad': [0, 0, 0, 0, 0, 0]
        }
        test_a_df_cond_expected = pd.DataFrame(data,
                                               index=[
                                                   'ground_plane',
                                                   'Q1_bus_Q0_connector_pad',
                                                   'Q1_bus_Q2_connector_pad',
                                                   'Q1_pad_bot', 'Q1_pad_top1',
                                                   'Q1_readout_connector_pad'
                                               ])

        data = {
            'ground_plane': [
                0.288290, -0.032540, -0.031978, -0.040063, -0.043842, -0.030053
            ],
            'Q1_bus_Q0_connector_pad': [
                -0.032540, 0.047257, -0.000228, -0.012690, -0.001335, -0.000145
            ],
            'Q1_bus_Q2_connector_pad': [
                -0.031978, -0.000228, 0.045327, -0.001218, -0.011552, -0.000050
            ],
            'Q1_pad_bot': [
                -0.040063, -0.012690, -0.001218, 0.095831, -0.032415, -0.008367
            ],
            'Q1_pad_top1': [
                -0.043842, -0.001335, -0.011552, -0.032415, 0.091320, -0.001020
            ],
            'Q1_readout_connector_pad': [
                -0.030053, -0.000145, -0.000050, -0.008367, -0.001020, 0.039884
            ]
        }
        test_b_df_cmat_expected = pd.DataFrame(data,
                                               index=[
                                                   'ground_plane',
                                                   'Q1_bus_Q0_connector_pad',
                                                   'Q1_bus_Q2_connector_pad',
                                                   'Q1_pad_bot', 'Q1_pad_top1',
                                                   'Q1_readout_connector_pad'
                                               ])

        data = {
            'ground_plane': [0, 0, 0, 0, 0, 0],
            'Q1_bus_Q0_connector_pad': [0, 0, 0, 0, 0, 0],
            'Q1_bus_Q2_connector_pad': [0, 0, 0, 0, 0, 0],
            'Q1_pad_bot': [0, 0, 0, 0, 0, 0],
            'Q1_pad_top1': [0, 0, 0, 0, 0, 0],
            'Q1_readout_connector_pad': [0, 0, 0, 0, 0, 0]
        }
        test_b_df_cond_expected = pd.DataFrame(data,
                                               index=[
                                                   'ground_plane',
                                                   'Q1_bus_Q0_connector_pad',
                                                   'Q1_bus_Q2_connector_pad',
                                                   'Q1_pad_bot', 'Q1_pad_top1',
                                                   'Q1_readout_connector_pad'
                                               ])

        # Generate actual result data
        test_a_result = lumped_capacitive.load_q3d_capacitance_matrix(
            TEST_DATA / 'q3d_example.txt', _disp=False)
        test_b_result = lumped_capacitive.load_q3d_capacitance_matrix(
            TEST_DATA / 'q3d_example.txt', user_units='pF', _disp=False)

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
        self.assertEqual(4, test_a_return_size_result)
        self.assertEqual('fF', test_a_user_units_result)
        self.assertEqual(test_a_design_variation_expected,
                         test_a_design_variation_result)

        self.assertEqual(4, test_b_return_size_result)
        self.assertEqual('pF', test_b_user_units_result)
        self.assertEqual(test_b_design_variation_expected,
                         test_b_design_variation_result)

        data_points = test_a_df_cmat_expected['ground_plane'].size
        for i in range(data_points):
            for j in [
                    'ground_plane', 'Q1_bus_Q0_connector_pad',
                    'Q1_bus_Q2_connector_pad', 'Q1_pad_bot', 'Q1_pad_top1',
                    'Q1_readout_connector_pad'
            ]:
                self.assertAlmostEqual(test_a_df_cmat_expected[j][i],
                                       test_a_df_cmat_result[j][i],
                                       places=3)

        data_points = test_a_df_cond_expected['ground_plane'].size
        for i in range(data_points):
            for j in [
                    'ground_plane', 'Q1_bus_Q0_connector_pad',
                    'Q1_bus_Q2_connector_pad', 'Q1_pad_bot', 'Q1_pad_top1',
                    'Q1_readout_connector_pad'
            ]:
                self.assertAlmostEqual(test_a_df_cond_expected[j][i],
                                       test_a_df_cond_result[j][i],
                                       places=3)

        data_points = test_b_df_cmat_expected['ground_plane'].size
        for i in range(data_points):
            for j in [
                    'ground_plane', 'Q1_bus_Q0_connector_pad',
                    'Q1_bus_Q2_connector_pad', 'Q1_pad_bot', 'Q1_pad_top1',
                    'Q1_readout_connector_pad'
            ]:
                self.assertAlmostEqual(test_b_df_cmat_expected[j][i],
                                       test_b_df_cmat_result[j][i],
                                       places=3)

        data_points = test_b_df_cond_expected['ground_plane'].size
        for i in range(data_points):
            for j in [
                    'ground_plane', 'Q1_bus_Q0_connector_pad',
                    'Q1_bus_Q2_connector_pad', 'Q1_pad_bot', 'Q1_pad_top1',
                    'Q1_readout_connector_pad'
            ]:
                self.assertAlmostEqual(test_b_df_cond_expected[j][i],
                                       test_b_df_cond_result[j][i],
                                       places=3)

    def test_analyses_lumped_move_index_to(self):
        """
        Test the functionality of move_index_to in lumped_capacitives.py
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
        """
        # Setup expected test results
        data = {
            'ground_plane': [
                2.8829E-13, -3.1978E-14, -4.0063E-14, -3.254E-14, -4.3842E-14,
                -3.0053E-14
            ],
            'Q1_bus_Q2_connector_pad': [
                -3.1978E-14, 4.5327E-14, -1.218E-15, -2.2765E-16, -1.1552E-14,
                -5.0414E-17
            ],
            'Q1_pad_bot': [
                -4.0063E-14, -1.218E-15, 9.5831E-14, -1.269E-14, -3.2415E-14,
                -8.3665E-15
            ],
            'Q1_bus_Q0_connector_pad': [
                -3.254E-14, -2.2765E-16, -1.269E-14, 4.7257E-14, -1.3351E-15,
                -1.451E-16
            ],
            'Q1_pad_top1': [
                -4.3842E-14, -1.1552E-14, -3.2415E-14, -1.3351E-15, 9.132E-14,
                -1.0199E-15
            ],
            'Q1_readout_connector_pad': [
                -3.0053E-14, -5.0414E-17, -8.3665E-15, -1.451E-16, -1.0199E-15,
                3.9884E-14
            ]
        }

        test_a_expected = pd.DataFrame(
            data,
            index=[
                'ground_plane', 'Q1_bus_Q2_connector_pad', 'Q1_pad_bot',
                'Q1_bus_Q0_connector_pad', 'Q1_pad_top1',
                'Q1_readout_connector_pad'
            ])

        data = {
            'Q1_pad_top1': [
                9.132E-14, -4.3842E-14, -1.3351E-15, -1.1552E-14, -3.2415E-14,
                -1.0199E-15
            ],
            'ground_plane': [
                -4.3842E-14, 2.8829E-13, -3.254E-14, -3.1978E-14, -4.0063E-14,
                -3.0053E-14
            ],
            'Q1_bus_Q0_connector_pad': [
                -1.3351E-15, -3.254E-14, 4.7257E-14, -2.2765E-16, -1.269E-14,
                -1.451E-16
            ],
            'Q1_bus_Q2_connector_pad': [
                -1.1552E-14, -3.1978E-14, -2.2765E-16, 4.5327E-14, -1.218E-15,
                -5.0414E-17
            ],
            'Q1_pad_bot': [
                -3.2415E-14, -4.0063E-14, -1.269E-14, -1.218E-15, 9.5831E-14,
                -8.3665E-15
            ],
            'Q1_readout_connector_pad': [
                -1.0199E-15, -3.0053E-14, -1.451E-16, -5.0414E-17, -8.3665E-15,
                3.9884E-14
            ]
        }

        test_b_expected = pd.DataFrame(data,
                                       index=[
                                           'Q1_pad_top1', 'ground_plane',
                                           'Q1_bus_Q0_connector_pad',
                                           'Q1_bus_Q2_connector_pad',
                                           'Q1_pad_bot',
                                           'Q1_readout_connector_pad'
                                       ])

        # Generate actual result data
        df_a = lumped_capacitive.readin_q3d_matrix(TEST_DATA /
                                                   'q3d_example.txt')[0]
        df_b = lumped_capacitive.readin_q3d_matrix(TEST_DATA /
                                                   'q3d_example.txt')[0]

        test_a_result = lumped_capacitive.df_reorder_matrix_basis(df_a, 1, 3)
        test_b_result = lumped_capacitive.df_reorder_matrix_basis(df_b, 4, 0)

        # Test all elements of the result data against expected data
        for j in [
                'ground_plane', 'Q1_bus_Q2_connector_pad', 'Q1_pad_bot',
                'Q1_bus_Q0_connector_pad', 'Q1_pad_top1',
                'Q1_readout_connector_pad'
        ]:
            self.assertIterableAlmostEqual(test_a_expected[j],
                                           test_a_result[j],
                                           abs_tol=1e-20)

        for j in [
                'ground_plane', 'Q1_bus_Q0_connector_pad',
                'Q1_bus_Q2_connector_pad', 'Q1_pad_bot', 'Q1_pad_top1',
                'Q1_readout_connector_pad'
        ]:
            self.assertIterableAlmostEqual(test_b_expected[j],
                                           test_b_result[j],
                                           abs_tol=1e-20)

        with self.assertRaises(IndexError):
            test_a_result = lumped_capacitive.df_reorder_matrix_basis(
                df_a, 1, 35)


if __name__ == '__main__':
    unittest.main(verbosity=2)
