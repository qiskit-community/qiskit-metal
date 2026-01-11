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
# pylint: disable-msg=too-many-public-methods
"""Qiskit Metal unit tests components functionality."""

import unittest

from qiskit_metal.qlibrary.core import qubit, qroute
from qiskit_metal.qlibrary.sample_shapes import circle_caterpillar
from qiskit_metal.qlibrary.sample_shapes import circle_raster
from qiskit_metal.qlibrary.sample_shapes import rectangle
from qiskit_metal.qlibrary.sample_shapes import rectangle_hollow
from qiskit_metal.qlibrary.sample_shapes import n_gon
from qiskit_metal.qlibrary.sample_shapes import n_square_spiral
from qiskit_metal.qlibrary.lumped.cap_n_interdigital import CapNInterdigital
from qiskit_metal.qlibrary.couplers.coupled_line_tee import CoupledLineTee
from qiskit_metal.qlibrary.couplers.cap_n_interdigital_tee import CapNInterdigitalTee
from qiskit_metal.qlibrary.couplers.line_tee import LineTee
from qiskit_metal.qlibrary.terminations import open_to_ground
from qiskit_metal.qlibrary.terminations import short_to_ground
from qiskit_metal.qlibrary.tlines.anchored_path import RouteAnchors
from qiskit_metal.qlibrary.tlines import straight_path
from qiskit_metal.qlibrary.tlines import meandered
from qiskit_metal.qlibrary.tlines.mixed_path import RouteMixed
from qiskit_metal.qlibrary.tlines.pathfinder import RoutePathfinder
from qiskit_metal import designs
from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond
from qiskit_metal.qlibrary.terminations.launchpad_wb_coupled import LaunchpadWirebondCoupled
from qiskit_metal.qlibrary.lumped.cap_3_interdigital import Cap3Interdigital
from qiskit_metal.qlibrary.qubits import star_qubit
from qiskit_metal.qlibrary.qubits.JJ_Dolan import jj_dolan
from qiskit_metal.qlibrary.qubits.JJ_Manhattan import jj_manhattan
from qiskit_metal.qlibrary.qubits import transmon_concentric
from qiskit_metal.qlibrary.qubits import transmon_cross
from qiskit_metal.qlibrary.qubits.transmon_cross_fl import TransmonCrossFL
from qiskit_metal.qlibrary.qubits import transmon_pocket
from qiskit_metal.qlibrary.qubits import transmon_pocket_cl
from qiskit_metal.qlibrary.qubits.transmon_pocket_6 import TransmonPocket6
from qiskit_metal.qlibrary.qubits.transmon_pocket_teeth import TransmonPocketTeeth
from qiskit_metal.qlibrary.qubits.SQUID_loop import SQUID_LOOP
from qiskit_metal.qlibrary.couplers.tunable_coupler_01 import TunableCoupler01
from qiskit_metal.qlibrary import _template
from .assertions import AssertionsMixin

#pylint: disable-msg=line-too-long
from qiskit_metal.qlibrary.lumped.resonator_coil_rect import ResonatorCoilRect


class TestComponentOptions(unittest.TestCase, AssertionsMixin):
    """Unit test class."""

    def setUp(self):
        """Setup unit test."""
        pass

    def tearDown(self):
        """Tie any loose ends."""
        pass

    def test_qlibrary_circle_caterpiller_options(self):
        """Test that default options of circle_caterpiller in
        circle_caterpillar.py were not accidentally changed."""
        # Setup expected test results
        _design = designs.DesignPlanar()
        _circle_caterpillar = circle_caterpillar.CircleCaterpillar(
            _design, 'my_name')
        _options = _circle_caterpillar.default_options

        # Test all elements of the result data against expected data
        self.assertEqual(len(_options), 7)
        self.assertEqual(_options['segments'], '5')
        self.assertEqual(_options['distance'], '1.2')
        self.assertEqual(_options['radius'], '300um')
        self.assertEqual(_options['resolution'], '16')
        self.assertEqual(_options['cap_style'], 'round')
        self.assertEqual(_options['subtract'], 'False')
        self.assertEqual(_options['helper'], 'False')

    def test_qlibrary_circle_raster_options(self):
        """Test that default options of circle_raster in circle_raster.py were
        not accidentally changed."""
        # Setup expected test results
        _design = designs.DesignPlanar()
        _circle_raster = circle_raster.CircleRaster(_design, 'my_name')
        _options = _circle_raster.default_options

        # Test all elements of the result data against expected data
        self.assertEqual(len(_options), 5)
        self.assertEqual(_options['radius'], '300um')
        self.assertEqual(_options['resolution'], '16')
        self.assertEqual(_options['cap_style'], 'round')
        self.assertEqual(_options['subtract'], 'False')
        self.assertEqual(_options['helper'], 'False')

    def test_qlibrary_rectangle_options(self):
        """Test that default options of rectangle in rectangle.py were not
        accidentally changed."""
        # Setup expected test results
        _design = designs.DesignPlanar()
        _rectangle = rectangle.Rectangle(_design, 'my_name')
        _options = _rectangle.default_options

        # Test all elements of the result data against expected data
        self.assertEqual(len(_options), 4)
        self.assertEqual(_options['width'], '500um')
        self.assertEqual(_options['height'], '300um')
        self.assertEqual(_options['subtract'], 'False')
        self.assertEqual(_options['helper'], 'False')

    def test_qlibrary_rectangle_hollow_options(self):
        """Test that default options of rectangle_hollow in rectangle_hollow.py
        were not accidentally changed."""
        # Setup expected test results
        _design = designs.DesignPlanar()
        _rectangle_hollow = rectangle_hollow.RectangleHollow(_design, 'my_name')
        _options = _rectangle_hollow.default_options

        # Test all elements of the result data against expected data
        self.assertEqual(len(_options), 5)
        self.assertEqual(_options['width'], '500um')
        self.assertEqual(_options['height'], '300um')
        self.assertEqual(_options['subtract'], 'False')
        self.assertEqual(_options['helper'], 'False')

        self.assertEqual(len(_options['inner']), 5)
        self.assertEqual(_options['inner']['width'], '250um')
        self.assertEqual(_options['inner']['height'], '100um')
        self.assertEqual(_options['inner']['offset_x'], '40um')
        self.assertEqual(_options['inner']['offset_y'], '-20um')
        self.assertEqual(_options['inner']['orientation'], '15')

    def test_qlibrary_n_gon_options(self):
        """Test that default options of NGon in n_gon.py were not accidentally
        changed."""
        # Setup expected test results
        design = designs.DesignPlanar()
        my_n_gon = n_gon.NGon(design, 'my_name')
        options = my_n_gon.default_options

        # Test all elements of the result data against expected data
        self.assertEqual(len(options), 4)
        self.assertEqual(options['n'], '3')
        self.assertEqual(options['radius'], '30um')
        self.assertEqual(options['subtract'], 'False')
        self.assertEqual(options['helper'], 'False')

    def test_qlibrary_n_square_spiral_options(self):
        """Test that default options of NSquareSpiral in n_square_spiral.py
        were not accidentally changed."""
        # Setup expected test results
        design = designs.DesignPlanar()
        my_n_square_spiral = n_square_spiral.NSquareSpiral(design, 'my_name')
        options = my_n_square_spiral.default_options

        # Test all elements of the result data against expected data
        self.assertEqual(len(options), 6)
        self.assertEqual(options['n'], '3')
        self.assertEqual(options['width'], '1um')
        self.assertEqual(options['radius'], '40um')
        self.assertEqual(options['gap'], '4um')
        self.assertEqual(options['subtract'], 'False')
        self.assertEqual(options['helper'], 'False')

    def test_qlibrary_basequbit_options(self):
        """Test that default options of BaseQubit in qubit.py were not
        accidentally changed."""
        # Setup expected test results
        design = designs.DesignPlanar()
        my_base_qubit = qubit.BaseQubit(design, 'my_name', make=False)
        options = my_base_qubit.default_options

        # Test all elements of the results data against expected ata
        self.assertEqual(len(options), 2)
        self.assertEqual(options['connection_pads'], {})
        self.assertEqual(options['_default_connection_pads'], {})

    def test_qlibrary_open_to_ground_options(self):
        """Test that default options of OpenToGround in open_to_ground.py were
        not accidentally changed."""
        # Setup expected test results
        design = designs.DesignPlanar()
        my_open_to_ground = open_to_ground.OpenToGround(design, 'my_name')
        options = my_open_to_ground.default_options

        # Test all elements of the results data against expected ata
        self.assertEqual(len(options), 3)
        self.assertEqual(options['width'], '10um')
        self.assertEqual(options['gap'], '6um')
        self.assertEqual(options['termination_gap'], '6um')

    def test_qlibrary_short_to_ground_options(self):
        """Test that default options of ShortToGround in short_to_ground.py
        where not accidentally changed."""
        # Setup expected test results
        design = designs.DesignPlanar()
        my_short_to_ground = short_to_ground.ShortToGround(design, 'my_name')
        options = my_short_to_ground.default_options

        # Test all elements of the results data against expected ata
        self.assertEqual(len(options), 1)
        self.assertEqual(options['width'], '10um')

    def test_qlibrary_straight_path_options(self):
        """Test that default options of RouteStraight in straight_path.py were
        not accidentally changed."""
        # Setup expected test results
        my_straight_path = straight_path.RouteStraight
        options = my_straight_path.default_options

        # Test all elements of the results data against expected ata
        self.assertEqual(len(options), 5)
        self.assertEqual(options['fillet'], '0')
        self.assertEqual(options['total_length'], '7mm')
        self.assertEqual(options['trace_width'], 'cpw_width')

        self.assertEqual(len(options['pin_inputs']), 2)
        self.assertEqual(len(options['pin_inputs']['start_pin']), 2)
        self.assertEqual(len(options['pin_inputs']['end_pin']), 2)
        self.assertEqual(options['pin_inputs']['start_pin']['component'], '')
        self.assertEqual(options['pin_inputs']['start_pin']['pin'], '')
        self.assertEqual(options['pin_inputs']['end_pin']['component'], '')
        self.assertEqual(options['pin_inputs']['end_pin']['pin'], '')

        self.assertEqual(len(options['lead']), 4)
        self.assertEqual(options['lead']['start_straight'], '0mm')
        self.assertEqual(options['lead']['end_straight'], '0mm')
        self.assertEqual(options['lead']['start_jogged_extension'], '')
        self.assertEqual(options['lead']['end_jogged_extension'], '')

    def test_qlibrary_route_meander_options(self):
        """Test that default options of RouteMeander in meandered.py were not
        accidentally changed."""
        # Setup expected test results
        my_route_meander = meandered.RouteMeander
        options = my_route_meander.default_options

        # Test all elements of the results data against expected ata
        self.assertEqual(len(options), 3)
        self.assertEqual(options['snap'], 'true')
        self.assertEqual(options['prevent_short_edges'], 'true')

        self.assertEqual(len(options['meander']), 2)
        self.assertEqual(options['meander']['spacing'], '200um')
        self.assertEqual(options['meander']['asymmetry'], '0um')

    def test_qlibrary_route_mixed_options(self):
        """Test that default options of RouteMixed in mixed_path.py were not
        accidentally changed."""
        # Setup expected test results
        my_route_mixed = RouteMixed
        options = my_route_mixed.default_options

        # Test all elements of the results data against expected ata
        self.assertEqual(len(options), 1)
        self.assertEqual(options['between_anchors'], {})

    def test_qlibrary_my_qcomponent_options(self):
        """Test that default options in MyQComponent in _template.py were not
        accidentally changed."""
        # Setup expected test results
        my_qcomponent_local = _template.MyQComponent
        options = my_qcomponent_local.default_options

        # Test all elements of the results data against expected ata
        self.assertEqual(len(options), 2)
        self.assertEqual(options['width'], '500um')
        self.assertEqual(options['height'], '300um')

    def test_qlibrary_transmon_concentric_options(self):
        """Test that default options of transmon_concentric in
        transmon_concentric.py were not accidentally changed."""
        # Setup expected test results
        design = designs.DesignPlanar()
        my_transmon_concentric = transmon_concentric.TransmonConcentric(
            design, 'my_name')
        options = my_transmon_concentric.default_options

        self.assertEqual(len(options), 17)
        self.assertEqual(options['width'], '1000um')
        self.assertEqual(options['height'], '1000um')
        self.assertEqual(options['rad_o'], '170um')
        self.assertEqual(options['rad_i'], '115um')
        self.assertEqual(options['gap'], '35um')
        self.assertEqual(options['jj_w'], '10um')
        self.assertEqual(options['res_s'], '100um')
        self.assertEqual(options['res_ext'], '100um')
        self.assertEqual(options['fbl_rad'], '100um')
        self.assertEqual(options['fbl_sp'], '100um')
        self.assertEqual(options['fbl_gap'], '80um')
        self.assertEqual(options['fbl_ext'], '300um')
        self.assertEqual(options['pocket_w'], '1500um')
        self.assertEqual(options['pocket_h'], '1000um')
        self.assertEqual(options['cpw_width'], '10.0um')
        self.assertEqual(options['inductor_width'], '5.0um')

    def test_qlibrary_star_qubit_options(self):
        """Test that default options of transmon_concentric in
        star_qubit.py were not accidentally changed."""
        # Setup expected test results
        design = designs.DesignPlanar()
        my_star_qubit = star_qubit.StarQubit(design, 'my_name')
        options = my_star_qubit.default_options

        self.assertEqual(len(options), 18)
        self.assertEqual(options['radius'], '300um')
        self.assertEqual(options['center_radius'], '100um')
        self.assertEqual(options['gap_couplers'], '25um')
        self.assertEqual(options['gap_readout'], '10um')
        self.assertEqual(options['connector_length'], '75um')
        self.assertEqual(options['trap_offset'], '20um')
        self.assertEqual(options['junc_h'], '100um')
        self.assertEqual(options['cpw_width'], '0.01')
        self.assertEqual(options['rotation_cpl1'], '0.0')
        self.assertEqual(options['rotation_cpl2'], '72.0')
        self.assertEqual(options['rotation_rdout'], '144.0')
        self.assertEqual(options['rotation_cpl3'], '216.0')
        self.assertEqual(options['rotation_cpl4'], '288.0')
        self.assertEqual(options['number_of_connectors'], '4')
        self.assertEqual(options['resolution'], '16')
        self.assertEqual(options['cap_style'], 'round')
        self.assertEqual(options['subtract'], 'False')
        self.assertEqual(options['helper'], 'False')

    def test_qlibrary_transmon_cross_fl_options(self):
        """Test that default_options of transmon_cross_fl were not accidentally changed."""
        # Setup expected test results
        design = designs.DesignPlanar()
        transmon_cross_fl = TransmonCrossFL(design, 'my_name')
        options = transmon_cross_fl.default_options

        self.assertEqual(len(options), 2)
        self.assertEqual(len(options['fl_options']), 5)
        self.assertEqual(options['make_fl'], True)
        self.assertEqual(options['fl_options']['t_top'], '15um')
        self.assertEqual(options['fl_options']['t_offset'], '0um')
        self.assertEqual(options['fl_options']['t_inductive_gap'], '3um')
        self.assertEqual(options['fl_options']['t_width'], '5um')
        self.assertEqual(options['fl_options']['t_gap'], '3um')

    def test_qlibrary_transmon_pocket_6_options(self):
        """Test that default_options of transmon_pocket_6 were not accidentally changed."""
        # Setup expected test results
        design = designs.DesignPlanar()
        transmon_pocket_6 = TransmonPocket6(design, 'my_name')
        options = transmon_pocket_6.default_options

        self.assertEqual(len(options), 7)
        self.assertEqual(options['pad_gap'], '30um')
        self.assertEqual(options['inductor_width'], '20um')
        self.assertEqual(options['pad_width'], '455um')
        self.assertEqual(options['pad_height'], '90um')
        self.assertEqual(options['pocket_width'], '650um')
        self.assertEqual(options['pocket_height'], '650um')

        self.assertEqual(len(options['_default_connection_pads']), 12)
        self.assertEqual(options['_default_connection_pads']['pad_gap'], '15um')
        self.assertEqual(options['_default_connection_pads']['pad_width'],
                         '125um')
        self.assertEqual(options['_default_connection_pads']['pad_height'],
                         '30um')
        self.assertEqual(options['_default_connection_pads']['pad_cpw_shift'],
                         '0um')
        self.assertEqual(options['_default_connection_pads']['pad_cpw_extent'],
                         '25um')
        self.assertEqual(options['_default_connection_pads']['cpw_width'],
                         '10um')
        self.assertEqual(options['_default_connection_pads']['cpw_gap'], '6um')
        self.assertEqual(options['_default_connection_pads']['cpw_extend'],
                         '100um')
        self.assertEqual(options['_default_connection_pads']['pocket_extent'],
                         '5um')
        self.assertEqual(options['_default_connection_pads']['pocket_rise'],
                         '0um')
        self.assertEqual(options['_default_connection_pads']['loc_W'], '+1')
        self.assertEqual(options['_default_connection_pads']['loc_H'], '+1')

    def test_qlibrary_transmon_pocket_teeth_options(self):
        """Test that default_options of transmon_pocket_teeth were not accidentally changed."""
        # Setup expected test results
        design = designs.DesignPlanar()
        transmon_pocket_teeth = TransmonPocketTeeth(design, 'my_name')
        options = transmon_pocket_teeth.default_options

        self.assertEqual(len(options), 10)
        self.assertEqual(options['pad_gap'], '30um')
        self.assertEqual(options['inductor_width'], '20um')
        self.assertEqual(options['pad_width'], '400um')
        self.assertEqual(options['pad_height'], '90um')
        self.assertEqual(options['pocket_width'], '650um')
        self.assertEqual(options['pocket_height'], '650um')
        self.assertEqual(options['coupled_pad_height'], '150um')
        self.assertEqual(options['coupled_pad_width'], '20um')
        self.assertEqual(options['coupled_pad_gap'], '50um')

        self.assertEqual(len(options['_default_connection_pads']), 12)
        self.assertEqual(options['_default_connection_pads']['pad_gap'], '15um')
        self.assertEqual(options['_default_connection_pads']['pad_width'],
                         '20um')
        self.assertEqual(options['_default_connection_pads']['pad_height'],
                         '150um')
        self.assertEqual(options['_default_connection_pads']['pad_cpw_shift'],
                         '0um')
        self.assertEqual(options['_default_connection_pads']['pad_cpw_extent'],
                         '25um')
        self.assertEqual(options['_default_connection_pads']['cpw_width'],
                         '10um')
        self.assertEqual(options['_default_connection_pads']['cpw_gap'], '6um')
        self.assertEqual(options['_default_connection_pads']['cpw_extend'],
                         '100um')
        self.assertEqual(options['_default_connection_pads']['pocket_extent'],
                         '5um')
        self.assertEqual(options['_default_connection_pads']['pocket_rise'],
                         '0um')
        self.assertEqual(options['_default_connection_pads']['loc_W'], '+1')
        self.assertEqual(options['_default_connection_pads']['loc_H'], '+1')

    def test_qlibrary_squid_loop_options(self):
        """Test that default_options of squid loop were not accidentally changed."""
        # Setup expected test results
        design = designs.DesignPlanar()
        squid_loop = SQUID_LOOP(design, 'my_name')
        options = squid_loop.default_options

        self.assertEqual(len(options), 15)
        self.assertEqual(options['plate1_width'], '5.5um')
        self.assertEqual(options['plate1_height'], '40um')
        self.assertEqual(options['plate1_pos_x'], '0')
        self.assertEqual(options['plate1_pos_y'], '0')
        self.assertEqual(options['squid_gap'], '10um')
        self.assertEqual(options['segment_a_length'], '10um')
        self.assertEqual(options['segment_a_width'], '1um')
        self.assertEqual(options['JJ_gap'], '0.5um')
        self.assertEqual(options['segment_b_length'], '5um')
        self.assertEqual(options['segment_b_width'], '1um')
        self.assertEqual(options['segment_c_width'], '1um')
        self.assertEqual(options['segment_d_length'], '10um')
        self.assertEqual(options['segment_d_width'], '2um')
        self.assertEqual(options['plate2_width'], '6um')
        self.assertEqual(options['plate2_height'], '30um')

    def test_qlibrary_tunable_coupler_01_options(self):
        """Test that default_options of tunable_coupler_01 were not accidentally changed."""
        # Setup expected test results
        design = designs.DesignPlanar()
        tunable_coupler = TunableCoupler01(design, 'my_name')
        options = tunable_coupler.default_options

        self.assertEqual(len(options), 13)
        self.assertEqual(options['c_width'], '400um')
        self.assertEqual(options['l_width'], '20um')
        self.assertEqual(options['l_gap'], '10um')
        self.assertEqual(options['a_height'], '60um')
        self.assertEqual(options['cp_height'], '15um')
        self.assertEqual(options['cp_arm_length'], '30um')
        self.assertEqual(options['cp_arm_width'], '6um')
        self.assertEqual(options['cp_gap'], '6um')
        self.assertEqual(options['cp_gspace'], '3um')
        self.assertEqual(options['fl_width'], '5um')
        self.assertEqual(options['fl_gap'], '3um')
        self.assertEqual(options['fl_length'], '10um')
        self.assertEqual(options['fl_ground'], '2um')

    def test_qlibrary_transmon_cross_options(self):
        """Test that default options of transmon_cross in transmon_cross.py
        were not accidentally changed."""
        # Setup expected test results
        _design = designs.DesignPlanar()
        _transmon_cross = transmon_cross.TransmonCross(_design, 'my_name')
        _options = _transmon_cross.default_options

        # Test all elements of the result data against expected data
        self.assertEqual(len(_options), 5)
        self.assertEqual(_options['cross_width'], '20um')
        self.assertEqual(_options['cross_length'], '200um')
        self.assertEqual(_options['cross_gap'], '20um')

        self.assertEqual(len(_options['_default_connection_pads']), 8)
        self.assertEqual(_options['_default_connection_pads']['connector_type'],
                         '0')
        self.assertEqual(_options['_default_connection_pads']['claw_length'],
                         '30um')
        self.assertEqual(_options['_default_connection_pads']['ground_spacing'],
                         '5um')
        self.assertEqual(_options['_default_connection_pads']['claw_width'],
                         '10um')
        self.assertEqual(
            _options['_default_connection_pads']['claw_cpw_length'], '40um')
        self.assertEqual(_options['_default_connection_pads']['claw_cpw_width'],
                         '10um')
        self.assertEqual(_options['_default_connection_pads']['claw_gap'],
                         '6um')
        self.assertEqual(
            _options['_default_connection_pads']['connector_location'], '0')

    def test_qlibrary_transmon_pocket_options(self):
        """Test that default options of transmon_pocket in transmon_pocket.py
        were not accidentally changed."""
        # Setup expected test results
        _design = designs.DesignPlanar()
        _transmon_pocket = transmon_pocket.TransmonPocket(_design, 'my_name')
        _options = _transmon_pocket.default_options

        # Test all elements of the result data against expected data
        self.assertEqual(len(_options), 7)
        self.assertEqual(_options['pad_gap'], '30um')
        self.assertEqual(_options['inductor_width'], '20um')
        self.assertEqual(_options['pad_width'], '455um')
        self.assertEqual(_options['pad_height'], '90um')
        self.assertEqual(_options['pocket_width'], '650um')
        self.assertEqual(_options['pocket_height'], '650um')

        self.assertEqual(len(_options['_default_connection_pads']), 12)
        self.assertEqual(_options['_default_connection_pads']['pad_gap'],
                         '15um')
        self.assertEqual(_options['_default_connection_pads']['pad_width'],
                         '125um')
        self.assertEqual(_options['_default_connection_pads']['pad_height'],
                         '30um')
        self.assertEqual(_options['_default_connection_pads']['pad_cpw_shift'],
                         '5um')
        self.assertEqual(_options['_default_connection_pads']['pad_cpw_extent'],
                         '25um')
        self.assertEqual(_options['_default_connection_pads']['cpw_width'],
                         'cpw_width')
        self.assertEqual(_options['_default_connection_pads']['cpw_gap'],
                         'cpw_gap')
        self.assertEqual(_options['_default_connection_pads']['cpw_extend'],
                         '100um')
        self.assertEqual(_options['_default_connection_pads']['pocket_extent'],
                         '5um')
        self.assertEqual(_options['_default_connection_pads']['pocket_rise'],
                         '65um')
        self.assertEqual(_options['_default_connection_pads']['loc_W'], '+1')
        self.assertEqual(_options['_default_connection_pads']['loc_H'], '+1')

    def test_qlibrary_transmon_pocket_cl_options(self):
        """Test that default options of transmon_pocket_cl in
        transmon_pocket_cl.py were not accidentally changed."""
        # Setup expected test results
        _design = designs.DesignPlanar()
        _transmon_pocket_cl = transmon_pocket_cl.TransmonPocketCL(
            _design, 'my_name')
        _options = _transmon_pocket_cl.default_options

        # Test all elements of the result data against expected data
        self.assertEqual(len(_options), 7)
        self.assertEqual(_options['make_CL'], True)
        self.assertEqual(_options['cl_gap'], '6um')
        self.assertEqual(_options['cl_width'], '10um')
        self.assertEqual(_options['cl_length'], '20um')
        self.assertEqual(_options['cl_ground_gap'], '6um')
        self.assertEqual(_options['cl_pocket_edge'], '0')
        self.assertEqual(_options['cl_off_center'], '50um')

    def test_qlibrary_cpw_finger_cap_options(self):
        """Test that default options of CapNInterdigital in cap_n_interdigital.py were not
        accidentally changed."""
        # Setup expected test results
        design = designs.DesignPlanar()
        finger_cap = CapNInterdigital(design, 'my_name')
        options = finger_cap.default_options

        # Test all elements of the result data against expected data
        self.assertEqual(len(options), 10)
        self.assertEqual(options['north_width'], '10um')
        self.assertEqual(options['north_gap'], '6um')
        self.assertEqual(options['south_width'], '10um')
        self.assertEqual(options['south_gap'], '6um')
        self.assertEqual(options['cap_width'], '10um')
        self.assertEqual(options['cap_gap'], '6um')
        self.assertEqual(options['cap_gap_ground'], '6um')
        self.assertEqual(options['finger_length'], '20um')
        self.assertEqual(options['finger_count'], '5')
        self.assertEqual(options['cap_distance'], '50um')

    def test_qlibrary_cpw_t_finger_cap_options(self):
        """Test that default options of CapNInterdigitalTee in cap_n_interdigital_tee.py were not
        accidentally changed."""
        # Setup expected test results
        design = designs.DesignPlanar()
        t_finger_cap = CapNInterdigitalTee(design, 'my_name')
        options = t_finger_cap.default_options

        # Test all elements of the result data against expected data
        self.assertEqual(len(options), 9)
        self.assertEqual(options['prime_width'], '10um')
        self.assertEqual(options['prime_gap'], '6um')
        self.assertEqual(options['second_width'], '10um')
        self.assertEqual(options['second_gap'], '6um')
        self.assertEqual(options['cap_gap'], '6um')
        self.assertEqual(options['cap_width'], '10um')
        self.assertEqual(options['finger_length'], '20um')
        self.assertEqual(options['finger_count'], '5')
        self.assertEqual(options['cap_distance'], '50um')

    def test_qlibrary_cpw_t_options(self):
        """Test that default options of LineTee in line_tee.py were not accidentally changed."""
        # Setup expected test results
        design = designs.DesignPlanar()
        cpw_t = LineTee(design, 'my_name')
        options = cpw_t.default_options

        # Test all elements of the result data against expected data
        self.assertEqual(len(options), 5)
        self.assertEqual(options['prime_width'], '10um')
        self.assertEqual(options['prime_gap'], '6um')
        self.assertEqual(options['second_width'], '10um')
        self.assertEqual(options['second_gap'], '6um')
        self.assertEqual(options['t_length'], '50um')

    def test_qlibrary_cpw_hanger_t_options(self):
        """Test that default options of CoupledLineTee in coupled_line_tee.py were not
        accidentally changed."""
        # Setup expected test results
        design = designs.DesignPlanar()
        hanger_t = CoupledLineTee(design, 'my_name')
        options = hanger_t.default_options

        # Test all elements of the result data against expected data
        self.assertEqual(len(options), 10)
        self.assertEqual(options['prime_width'], '10um')
        self.assertEqual(options['prime_gap'], '6um')
        self.assertEqual(options['second_width'], '10um')
        self.assertEqual(options['second_gap'], '6um')
        self.assertEqual(options['coupling_space'], '3um')
        self.assertEqual(options['coupling_length'], '100um')
        self.assertEqual(options['down_length'], '100um')
        self.assertEqual(options['fillet'], '25um')
        self.assertEqual(options['mirror'], False)
        self.assertEqual(options['open_termination'], True)

    def test_qlibrary_resonator_rectangle_spiral_options(self):
        """Test that default options of ResonatorCoilRect in
        resonator_coil_rect.py were not accidentally changed."""
        # Setup expected test results
        design = designs.DesignPlanar()
        resonator_rectangle_spiral = ResonatorCoilRect(design, 'my_name')
        options = resonator_rectangle_spiral.default_options

        # Test all elements of the result data against expected data
        self.assertEqual(len(options), 6)
        self.assertEqual(options['n'], '3')
        self.assertEqual(options['length'], '2000um')
        self.assertEqual(options['line_width'], '1um')
        self.assertEqual(options['height'], '40um')
        self.assertEqual(options['gap'], '4um')
        self.assertEqual(options['coupler_distance'], '10um')

    def test_qlibrary_route_anchors_options(self):
        """Test that default options of RouteAnchors in anchored_path.py were
        not accientally changed."""
        # Setup expected test results
        route_anchors = RouteAnchors
        options = route_anchors.default_options

        # Test all elements of the result data against expected data
        self.assertEqual(len(options), 2)
        self.assertEqual(options['anchors'], {})
        self.assertEqual(len(options['advanced']), 1)
        self.assertEqual(options['advanced']['avoid_collision'], 'false')

    def test_qlibrary_route_pathfinder_options(self):
        """Test that default options of RoutePathfinder in pathfinder.py were
        not accidentally changed."""
        # Setup expected test results
        route_pathfinder = RoutePathfinder
        options = route_pathfinder.default_options

        # Test all elements of the result data against expected data
        self.assertEqual(len(options), 2)
        self.assertEqual(options['step_size'], '0.25mm')
        self.assertEqual(len(options['advanced']), 1)
        self.assertEqual(options['advanced']['avoid_collision'], 'true')

    def test_qlibrary_launch_v1_options(self):
        """Test that default options of LaunchpadWirebond in launchpad_wb.py
        were not accidentally changed."""
        design = designs.DesignPlanar()
        launch_v1 = LaunchpadWirebond(design, 'my_name')
        options = launch_v1.default_options

        self.assertEqual(len(options), 7)
        self.assertEqual(options['trace_width'], 'cpw_width')
        self.assertEqual(options['trace_gap'], 'cpw_gap')
        self.assertEqual(options['lead_length'], '25um')
        self.assertEqual(options['pad_width'], '80um')
        self.assertEqual(options['pad_height'], '80um')
        self.assertEqual(options['pad_gap'], '58um')
        self.assertEqual(options['taper_height'], '122um')

    def test_qlibrary_launch_v2_options(self):
        """Test that default options of LaunchpadWirebondCoupled in
        launchpad_wb_coupled.py were not accidentally changed."""
        design = designs.DesignPlanar()
        launch_v2 = LaunchpadWirebondCoupled(design, 'my_name')
        options = launch_v2.default_options

        self.assertEqual(len(options), 4)
        self.assertEqual(options['trace_width'], 'cpw_width')
        self.assertEqual(options['trace_gap'], 'cpw_gap')
        self.assertEqual(options['coupler_length'], '62.5um')
        self.assertEqual(options['lead_length'], '25um')

    def test_qlibrary_cap_three_fingers(self):
        """Test that default options of Cap3Interdigital were not accidentally
        changed."""
        design = designs.DesignPlanar()
        cap_three_fingers = Cap3Interdigital(design, 'my_name')
        options = cap_three_fingers.default_options

        self.assertEqual(len(options), 4)
        self.assertEqual(options['trace_width'], '10um')
        self.assertEqual(options['finger_length'], '65um')
        self.assertEqual(options['pocket_buffer_width_x'], '10um')
        self.assertEqual(options['pocket_buffer_width_y'], '30um')

    def test_qlibrary_qroute_options(self):
        """Test that default options of QRoute were not accidentally changed."""
        design = designs.DesignPlanar()
        my_qroute = qroute.QRoute(design, name='test_qroute', options={})
        options = my_qroute.default_options

        self.assertEqual(len(options), 5)
        self.assertEqual(options['fillet'], '0')
        self.assertEqual(options['total_length'], '7mm')
        self.assertEqual(options['trace_width'], 'cpw_width')

        self.assertEqual(len(options['pin_inputs']), 2)
        self.assertEqual(len(options['pin_inputs']['start_pin']), 2)
        self.assertEqual(len(options['pin_inputs']['end_pin']), 2)
        self.assertEqual(options['pin_inputs']['start_pin']['component'], '')
        self.assertEqual(options['pin_inputs']['start_pin']['pin'], '')
        self.assertEqual(options['pin_inputs']['end_pin']['component'], '')
        self.assertEqual(options['pin_inputs']['end_pin']['pin'], '')

        self.assertEqual(len(options['lead']), 4)
        self.assertEqual(options['lead']['start_straight'], '0mm')
        self.assertEqual(options['lead']['end_straight'], '0mm')
        self.assertEqual(options['lead']['start_jogged_extension'], '')
        self.assertEqual(options['lead']['end_jogged_extension'], '')

    def test_qlibrary_jj_dolan_options(self):
        """Test the default options of JJ_Dolan were not accidentially changed."""
        design = designs.DesignPlanar()
        my_jj_dolan = jj_dolan(design, name='test_jj_dolan', options={})
        options = my_jj_dolan.default_options

        self.assertEqual(len(options), 10)
        self.assertEqual(options['JJ_pad_lower_width'], '25um')
        self.assertEqual(options['JJ_pad_lower_height'], '10um')
        self.assertEqual(options['JJ_pad_lower_pos_x'], '0')
        self.assertEqual(options['JJ_pad_lower_pos_y'], '0')
        self.assertEqual(options['finger_lower_width'], '1um')
        self.assertEqual(options['finger_lower_height'], '20um')
        self.assertEqual(options['extension'], '1um')
        self.assertEqual(options['offset'], '2um')
        self.assertEqual(options['second_metal_length'], '5um')
        self.assertEqual(options['second_metal_width'], '1um')

    def test_qlibrary_jj_manhattan_options(self):
        """Test the default options of JJ_Manhattan were not accidentially changed."""
        design = designs.DesignPlanar()
        my_jj_manhattan = jj_manhattan(design,
                                       name='test_jj_manhattan',
                                       options={})
        options = my_jj_manhattan.default_options

        self.assertEqual(len(options), 7)
        self.assertEqual(options['JJ_pad_lower_width'], '25um')
        self.assertEqual(options['JJ_pad_lower_height'], '10um')
        self.assertEqual(options['JJ_pad_lower_pos_x'], '0')
        self.assertEqual(options['JJ_pad_lower_pos_y'], '0')
        self.assertEqual(options['finger_lower_width'], '1um')
        self.assertEqual(options['finger_lower_height'], '20um')
        self.assertEqual(options['extension'], '1um')

        def test_qlibrary_BridgeFreeJunction_options(self):
            """Test the default options of JJ_Manhattan were not accidentially changed."""
            design = designs.DesignPlanar()
            my_jj_BridgeFree = BridgeFreeJunction(
                design, name='test_BridgeFreeJunction', options={})
            options = my_jj_BridgeFree.default_options

            self.assertEqual(len(options), 7)
            self.assertEqual(options['The width of lower JJ metal region'],
                             '4um')
            self.assertEqual(options['The height of lower JJ metal region'],
                             '4um')
            self.assertEqual(
                options['Evaporation angle of the first evaporation (˚)'], '30')
            self.assertEqual(
                options['Evaporation angle of the second evaporation (˚)'],
                '30')
            self.assertEqual(options['The length of the connecting wires'],
                             '30um')
            self.assertEqual(options['The width of the connecting wires.'],
                             '0.5um')
            self.assertEqual(
                options['Thickness of the first (bottom) resist layer.'],
                '0.3um')
            self.assertEqual(
                options['Thickness of the second (top) resist layer.'], '0.2um')


if __name__ == '__main__':
    unittest.main(verbosity=2)
