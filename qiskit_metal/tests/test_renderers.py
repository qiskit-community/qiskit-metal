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
# pylint: disable-msg=too-many-public-methods
# pylint: disable-msg=import-error
# pylint: disable-msg=protected-access
"""Qiskit Metal unit tests analyses functionality."""

import unittest
from unittest.mock import MagicMock
import matplotlib.pyplot as _plt
import pandas as pd

from qiskit_metal import designs, Dict, draw
from qiskit_metal.renderers import setup_default
from qiskit_metal.renderers.renderer_ansys.ansys_renderer import QAnsysRenderer
from qiskit_metal.renderers.renderer_ansys.q3d_renderer import QQ3DRenderer
from qiskit_metal.renderers.renderer_ansys.hfss_renderer import QHFSSRenderer
from qiskit_metal.renderers.renderer_base.renderer_base import QRenderer
from qiskit_metal.renderers.renderer_base.renderer_gui_base import QRendererGui
from qiskit_metal.renderers.renderer_gds.gds_renderer import QGDSRenderer
from qiskit_metal.renderers.renderer_mpl.mpl_interaction import MplInteraction
from qiskit_metal.renderers.renderer_gmsh.gmsh_renderer import QGmshRenderer
from qiskit_metal.renderers.renderer_elmer.elmer_renderer import QElmerRenderer
from qiskit_metal.renderers.renderer_ansys_pyaedt.hfss_renderer_eigenmode_aedt import QHFSSEigenmodePyaedt
from qiskit_metal.renderers.renderer_ansys_pyaedt.hfss_renderer_drivenmodal_aedt import QHFSSDrivenmodalPyaedt
from qiskit_metal.renderers.renderer_ansys_pyaedt.q3d_renderer_aedt import QQ3DPyaedt

from qiskit_metal.renderers.renderer_ansys import ansys_renderer

from qiskit_metal.qgeometries.qgeometries_handler import QGeometryTables
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
from qiskit_metal.qlibrary.tlines.mixed_path import RouteMixed
from qiskit_metal.renderers.renderer_gds.airbridge import Airbridge_forGDS

from qiskit_metal.renderers.renderer_gds.make_airbridge import Airbridging


class TestRenderers(unittest.TestCase):
    """Unit test class."""

    def setUp(self):
        """Setup unit test."""
        pass

    def tearDown(self):
        """Tie any loose ends."""
        pass

    def test_renderer_instanitate_qansys_renderer(self):
        """Test instantiation of QAnsysRenderer in ansys_renderer.py"""
        design = designs.DesignPlanar()
        try:
            QAnsysRenderer(design, initiate=False)
        except Exception:
            self.fail("QAnsysRenderer() failed")

    def test_renderer_instantiate_gdsrender(self):
        """Test instantiation of QGDSRenderer in gds_renderer.py."""
        design = designs.DesignPlanar()
        try:
            QGDSRenderer(design)
        except Exception:
            self.fail("QGDSRenderer(design) failed")

        try:
            QGDSRenderer(design, initiate=False)
        except Exception:
            self.fail("QGDSRenderer(design, initiate=False) failed")

        try:
            QGDSRenderer(design, initiate=False, render_template={})
        except Exception:
            self.fail(
                "QGDSRenderer(design, initiate=False, render_template={}) failed"
            )

        try:
            QGDSRenderer(design, initiate=False, render_options={})
        except Exception:
            self.fail(
                "QGDSRenderer(design, initiate=False, render_options={}) failed"
            )

    def test_renderer_instantiate_mplinteraction(self):
        """Test instantiation of MplInteraction in mpl_interaction.py."""
        try:
            MplInteraction(_plt)
        except Exception:
            self.fail("MplInteraction(None) failed")

    def test_renderer_instantiate_qq3d_renderer(self):
        """Test instantiation of QQ3DRenderer in q3d_renderer.py."""
        design = designs.DesignPlanar()
        try:
            QQ3DRenderer(design, initiate=False)
        except Exception:
            self.fail("QQ3DRenderer failed")

    def test_renderer_instantiate_qhfss_renderer(self):
        """Test instantiation of QHFSSRenderer in hfss_renderer.py."""
        design = designs.DesignPlanar()
        try:
            QHFSSRenderer(design, initiate=False)
        except Exception:
            self.fail("QHFSSRenderer failed")

    def test_renderer_instantiate_qgmsh_renderer(self):
        """Test instantiation of QGmshRenderer in gmsh_renderer.py."""
        design = designs.DesignPlanar()
        try:
            QGmshRenderer(design)
        except Exception:
            self.fail("QGmshRenderer(design) failed")

        try:
            QGmshRenderer(design, initiate=False)
        except Exception:
            self.fail(
                "QGmshRenderer(design, initiate=False) failed in DesignPLanar")

        try:
            QGmshRenderer(design, initiate=False, options={})
        except Exception:
            self.fail(
                "QGmshRenderer(design, initiate=False, options={}) failed in DesignPLanar"
            )

    def test_renderer_instantiate_qelmer_renderer(self):
        """Test instantiation of QElmerRenderer in elmer_renderer.py."""
        design = designs.MultiPlanar()
        try:
            QElmerRenderer(design)
        except Exception:
            self.fail("QElmerRenderer(design) failed")

        try:
            QElmerRenderer(design, initiate=False)
        except Exception:
            self.fail(
                "QElmerRenderer(design, initiate=False) failed in MultiPlanar")

        try:
            QElmerRenderer(design, initiate=False, options={})
        except Exception:
            self.fail(
                "QElmerRenderer(design, initiate=False, options={}) failed in MultiPlanar"
            )

    def test_renderer_qansys_renderer_options(self):
        """Test that defaults in QAnsysRenderer were not accidentally changed."""
        design = designs.DesignPlanar()
        renderer = QAnsysRenderer(design, initiate=False)
        options = renderer.default_options

        self.assertEqual(len(options), 14)
        self.assertEqual(options['Lj'], '10nH')
        self.assertEqual(options['Cj'], 0)
        self.assertEqual(options['_Rj'], 0)
        self.assertEqual(options['max_mesh_length_jj'], '7um')
        self.assertEqual(options['max_mesh_length_port'], '7um')
        self.assertEqual(options['project_path'], None)
        self.assertEqual(options['project_name'], None)
        self.assertEqual(options['design_name'], None)
        self.assertEqual(options['x_buffer_width_mm'], 0.2)
        self.assertEqual(options['y_buffer_width_mm'], 0.2)
        self.assertEqual(options['wb_threshold'], '400um')
        self.assertEqual(options['wb_offset'], '0um')
        self.assertEqual(options['wb_size'], 5)

        self.assertEqual(len(options['plot_ansys_fields_options']), 13)
        self.assertEqual(options['plot_ansys_fields_options']['name'],
                         "NAME:Mag_E1")
        self.assertEqual(
            options['plot_ansys_fields_options']['UserSpecifyName'], '0')
        self.assertEqual(
            options['plot_ansys_fields_options']['UserSpecifyFolder'], '0')
        self.assertEqual(options['plot_ansys_fields_options']['QuantityName'],
                         "Mag_E")
        self.assertEqual(options['plot_ansys_fields_options']['PlotFolder'],
                         "E Field")
        self.assertEqual(options['plot_ansys_fields_options']['StreamlinePlot'],
                         "False")
        self.assertEqual(
            options['plot_ansys_fields_options']['AdjacentSidePlot'], "False")
        self.assertEqual(options['plot_ansys_fields_options']['FullModelPlot'],
                         "False")
        self.assertEqual(options['plot_ansys_fields_options']['IntrinsicVar'],
                         "Phase=\'0deg\'")
        self.assertEqual(options['plot_ansys_fields_options']['PlotGeomInfo_0'],
                         "1")
        self.assertEqual(options['plot_ansys_fields_options']['PlotGeomInfo_1'],
                         "Surface")
        self.assertEqual(options['plot_ansys_fields_options']['PlotGeomInfo_2'],
                         "FacesList")
        self.assertEqual(options['plot_ansys_fields_options']['PlotGeomInfo_3'],
                         "1")

    def test_renderer_qansysrenderer_default_setup(self):
        """Test that default_setup in QAnsysRenderer have not been accidentally changed."""
        default_setup = QAnsysRenderer.default_setup

        self.assertEqual(len(default_setup), 4)
        self.assertEqual(len(default_setup['drivenmodal']), 8)
        self.assertEqual(len(default_setup['eigenmode']), 9)
        self.assertEqual(len(default_setup['q3d']), 12)
        self.assertEqual(default_setup['port_inductor_gap'], '10um')

        self.assertEqual(default_setup['drivenmodal']['name'], "Setup")
        self.assertEqual(default_setup['drivenmodal']['freq_ghz'], '5.0')
        self.assertEqual(default_setup['drivenmodal']['max_delta_s'], '0.1')
        self.assertEqual(default_setup['drivenmodal']['max_passes'], '10')
        self.assertEqual(default_setup['drivenmodal']['min_passes'], '1')
        self.assertEqual(default_setup['drivenmodal']['min_converged'], '1')
        self.assertEqual(default_setup['drivenmodal']['pct_refinement'], '30')
        self.assertEqual(default_setup['drivenmodal']['basis_order'], '1')

        self.assertEqual(default_setup['eigenmode']['name'], "Setup")
        self.assertEqual(default_setup['eigenmode']['min_freq_ghz'], '1')
        self.assertEqual(default_setup['eigenmode']['n_modes'], '1')
        self.assertEqual(default_setup['eigenmode']['max_delta_f'], '0.5')
        self.assertEqual(default_setup['eigenmode']['max_passes'], '10')
        self.assertEqual(default_setup['eigenmode']['min_passes'], '1')
        self.assertEqual(default_setup['eigenmode']['min_converged'], '1')
        self.assertEqual(default_setup['eigenmode']['pct_refinement'], '30')
        self.assertEqual(default_setup['eigenmode']['basis_order'], '-1')

        self.assertEqual(default_setup['q3d']['name'], 'Setup')
        self.assertEqual(default_setup['q3d']['freq_ghz'], '5.0')
        self.assertEqual(default_setup['q3d']['save_fields'], 'False')
        self.assertEqual(default_setup['q3d']['enabled'], 'True')
        self.assertEqual(default_setup['q3d']['max_passes'], '15')
        self.assertEqual(default_setup['q3d']['min_passes'], '2')
        self.assertEqual(default_setup['q3d']['min_converged_passes'], '2')
        self.assertEqual(default_setup['q3d']['percent_error'], '0.5')
        self.assertEqual(default_setup['q3d']['percent_refinement'], '30')
        self.assertEqual(default_setup['q3d']['auto_increase_solution_order'],
                         'True')
        self.assertEqual(default_setup['q3d']['solution_order'], 'High')
        self.assertEqual(default_setup['q3d']['solver_type'], 'Iterative')

    def test_renderer_qelmer_renderer_default_setup(self):
        """Test that default_setup in QElmerRenderer have not been accidentally changed."""
        default_setup = QElmerRenderer.default_setup

        self.assertEqual(len(default_setup), 4)
        self.assertEqual(len(default_setup['capacitance']), 12)
        self.assertEqual(len(default_setup['eigenmode']), 0)
        self.assertEqual(len(default_setup['materials']), 2)
        self.assertEqual(len(default_setup['constants']), 2)

        self.assertEqual(
            default_setup['capacitance']['Calculate_Electric_Field'], True)
        self.assertEqual(
            default_setup['capacitance']['Calculate_Electric_Energy'], True)
        self.assertEqual(
            default_setup['capacitance']['Calculate_Capacitance_Matrix'], True)
        self.assertEqual(
            default_setup['capacitance']['Capacitance_Matrix_Filename'],
            'cap_matrix.txt')
        self.assertEqual(default_setup['capacitance']['Linear_System_Solver'],
                         'Iterative')
        self.assertEqual(
            default_setup['capacitance']['Steady_State_Convergence_Tolerance'],
            1e-05)
        self.assertEqual(
            default_setup['capacitance']
            ['Nonlinear_System_Convergence_Tolerance'], 1e-07)
        self.assertEqual(
            default_setup['capacitance']['Nonlinear_System_Max_Iterations'], 20)
        self.assertEqual(
            default_setup['capacitance']['Linear_System_Convergence_Tolerance'],
            1e-10)
        self.assertEqual(
            default_setup['capacitance']['Linear_System_Max_Iterations'], 500)
        self.assertEqual(
            default_setup['capacitance']['Linear_System_Iterative_Method'],
            'BiCGStab')
        self.assertEqual(
            default_setup['capacitance']['BiCGstabl_polynomial_degree'], 2)

        self.assertEqual(default_setup['materials'], ['vacuum', 'silicon'])

        self.assertEqual(default_setup['constants']['Permittivity_of_Vacuum'],
                         8.8542e-12)
        self.assertEqual(default_setup['constants']['Unit_Charge'], 1.602e-19)

    def test_renderer_qq3d_render_options(self):
        """Test that defaults in QQ3DRenderer were not accidentally changed."""
        design = designs.DesignPlanar()
        renderer = QQ3DRenderer(design, initiate=False)
        options = renderer.q3d_options

        self.assertEqual(renderer.name, 'q3d')

        self.assertEqual(len(options), 2)
        self.assertEqual(options['material_type'], 'pec')
        self.assertEqual(options['material_thickness'], '200nm')

    def test_renderer_hfss_render_options(self):
        """Test that defaults in QHFSSRender were not accidentally changed."""
        design = designs.DesignPlanar()
        renderer = QHFSSRenderer(design, initiate=False)
        options = renderer.hfss_options

        self.assertEqual(renderer.name, 'hfss')
        self.assertEqual(len(options), 1)
        self.assertEqual(options['port_inductor_gap'], '10um')

    def test_renderer_gdsrenderer_options(self):
        """Test that default_options in QGDSRenderer were not accidentally
        changed."""
        design = designs.DesignPlanar()
        renderer = QGDSRenderer(design)
        options = renderer.default_options

        self.assertEqual(len(options), 18)
        self.assertEqual(options['short_segments_to_not_fillet'], 'True')
        self.assertEqual(options['check_short_segments_by_scaling_fillet'],
                         '2.0')
        self.assertEqual(options['gds_unit'], '1')
        self.assertEqual(options['ground_plane'], 'True')
        self.assertEqual(options['negative_mask']['main'], [])
        self.assertEqual(options['corners'], 'circular bend')
        self.assertEqual(options['tolerance'], '0.00001')
        self.assertEqual(options['precision'], '0.000000001')
        self.assertEqual(options['width_LineString'], '10um')
        self.assertEqual(options['path_filename'],
                         '../resources/Fake_Junctions.GDS')
        self.assertEqual(options['junction_pad_overlap'], '5um')
        self.assertEqual(options['max_points'], '199')
        self.assertEqual(options['bounding_box_scale_x'], '1.2')
        self.assertEqual(options['bounding_box_scale_y'], '1.2')

        self.assertEqual(options['fabricate'], 'False')

        self.assertEqual(len(options['airbridge']), 4)
        self.assertEqual(len(options['airbridge']['geometry']), 2)

        self.assertEqual(options['airbridge']['geometry']['qcomponent_base'],
                         Airbridge_forGDS)
        self.assertEqual(
            options['airbridge']['geometry']['options']['crossover_length'],
            '22um')
        self.assertEqual(options['airbridge']['bridge_pitch'], '100um')
        self.assertEqual(options['airbridge']['bridge_minimum_spacing'], '5um')
        self.assertEqual(options['airbridge']['datatype'], '0')

        self.assertEqual(len(options['cheese']), 9)
        self.assertEqual(len(options['no_cheese']), 5)

        self.assertEqual(options['cheese']['datatype'], '100')
        self.assertEqual(options['cheese']['shape'], '0')
        self.assertEqual(options['cheese']['cheese_0_x'], '25um')
        self.assertEqual(options['cheese']['cheese_0_y'], '25um')
        self.assertEqual(options['cheese']['cheese_1_radius'], '100um')
        self.assertEqual(options['cheese']['delta_x'], '100um')
        self.assertEqual(options['cheese']['delta_y'], '100um')
        self.assertEqual(options['cheese']['edge_nocheese'], '200um')

        self.assertEqual(options['no_cheese']['datatype'], '99')
        self.assertEqual(options['no_cheese']['buffer'], '25um')
        self.assertEqual(options['no_cheese']['cap_style'], '2')
        self.assertEqual(options['no_cheese']['join_style'], '2')

        self.assertEqual(len(options['cheese']['view_in_file']), 1)
        self.assertEqual(len(options['cheese']['view_in_file']['main']), 1)
        self.assertEqual(options['cheese']['view_in_file']['main'][1], True)

        self.assertEqual(len(options['no_cheese']['view_in_file']), 1)
        self.assertEqual(len(options['no_cheese']['view_in_file']['main']), 1)
        self.assertEqual(options['no_cheese']['view_in_file']['main'][1], True)

    def test_renderer_qgmsh_renderer_options(self):
        """Test that default_options in QGmshRenderer were not accidentally
        changed."""
        design = designs.DesignPlanar()
        renderer = QGmshRenderer(design)
        options = renderer.default_options

        self.assertEqual(len(options), 4)
        self.assertEqual(len(options["mesh"]), 8)
        self.assertEqual(len(options["mesh"]["mesh_size_fields"]), 4)
        self.assertEqual(len(options["colors"]), 3)
        self.assertEqual(options["x_buffer_width_mm"], 0.2)
        self.assertEqual(options["y_buffer_width_mm"], 0.2)
        self.assertEqual(options["mesh"]["max_size"], "70um")
        self.assertEqual(options["mesh"]["min_size"], "5um")
        self.assertEqual(options["mesh"]["max_size_jj"], "5um")
        self.assertEqual(options["mesh"]["smoothing"], 10)
        self.assertEqual(options["mesh"]["nodes_per_2pi_curve"], 90)
        self.assertEqual(options["mesh"]["algorithm_3d"], 10)
        self.assertEqual(options["mesh"]["num_threads"], 8)
        self.assertEqual(
            options["mesh"]["mesh_size_fields"]["min_distance_from_edges"],
            "10um")
        self.assertEqual(
            options["mesh"]["mesh_size_fields"]["max_distance_from_edges"],
            "130um")
        self.assertEqual(options["mesh"]["mesh_size_fields"]["distance_delta"],
                         "30um")
        self.assertEqual(options["mesh"]["mesh_size_fields"]["gradient_delta"],
                         "3um")
        self.assertEqual(options["colors"]["metal"], (84, 140, 168, 255))
        self.assertEqual(options["colors"]["jj"], (84, 140, 168, 150))
        self.assertEqual(options["colors"]["dielectric"], (180, 180, 180, 255))

    def test_renderer_qelmer_renderer_options(self):
        """Test that default_options in QElmerRenderer were not accidentally
        changed."""
        design = designs.MultiPlanar()
        renderer = QElmerRenderer(design)
        options = renderer.default_options

        self.assertEqual(len(options), 6)
        self.assertEqual(options["simulation_type"], "steady_3D")
        self.assertEqual(options["simulation_dir"], "./simdata")
        self.assertEqual(options["mesh_file"], "out.msh")
        self.assertEqual(options["simulation_input_file"], "case.sif")
        self.assertEqual(options["postprocessing_file"], "case.msh")
        self.assertEqual(options["output_file"], "case.result")

    def test_renderer_ansys_renderer_get_clean_name(self):
        """Test get_clean_name in ansys_renderer.py"""
        self.assertEqual(ansys_renderer.get_clean_name('name12'), 'name12')
        self.assertEqual(ansys_renderer.get_clean_name('12name12'), 'name12')
        self.assertEqual(ansys_renderer.get_clean_name('name!'), 'name')

    def test_renderer_ansys_renderer_name_delim(self):
        """Test NAME_DELIM in QAnsysRenderer."""
        design = designs.DesignPlanar()
        renderer = QAnsysRenderer(design, initiate=False)
        self.assertEqual(renderer.NAME_DELIM, '_')

    def test_renderer_ansys_renderer_name(self):
        """Test name in QAnsysRenderer."""
        design = designs.DesignPlanar()
        renderer = QAnsysRenderer(design, initiate=False)
        self.assertEqual(renderer.name, 'ansys')

    def test_renderer_renderer_base_name(self):
        """Test name in QRenderer."""
        renderer = QRenderer
        self.assertEqual(renderer.name, 'base')

    def test_renderer_renderer_gui_base_name(self):
        """Test name in QRenderer."""
        renderer = QRendererGui
        self.assertEqual(renderer.name, 'guibase')

    def test_renderer_qgmsh_renderer_name(self):
        """Test name in QGmshRenderer."""
        design = designs.DesignPlanar()
        renderer = QGmshRenderer(design, initiate=False)
        self.assertEqual(renderer.name, 'gmsh')

    def test_renderer_qelmer_renderer_name(self):
        """Test name in QElmerRenderer."""
        design = designs.MultiPlanar()
        renderer = QElmerRenderer(design, initiate=False)
        self.assertEqual(renderer.name, 'elmer')

    def test_renderer_gdsrenderer_inclusive_bound(self):
        """Test functionality of inclusive_bound in gds_renderer.py."""
        design = designs.DesignPlanar()
        renderer = QGDSRenderer(design)

        my_list = []
        my_list.append([1, 1, 2, 2])
        my_list.append([3, 3, 5, 5])
        my_list.append([2.2, 2.3, 4.4, 4.9])
        self.assertEqual(renderer._inclusive_bound(my_list), (1, 1, 5, 5))

    def test_renderer_scale_max_bounds(self):
        """Test functionality of scale_max_bounds in gds_renderer.py."""
        design = designs.DesignPlanar()
        renderer = QGDSRenderer(design)

        actual = renderer._scale_max_bounds('main', [(1, 1, 3, 3)])
        self.assertEqual(len(actual), 2)
        self.assertEqual(actual[0], (0.8, 0.8, 3.2, 3.2))
        self.assertEqual(actual[1], (1, 1, 3, 3))

    def test_renderer_get_chip_names(self):
        """Test functionality of get_chip_names in gds_renderer.py."""
        design = designs.DesignPlanar()
        renderer = QGDSRenderer(design)

        qgt = QGeometryTables(design)
        qgt.clear_all_tables()

        transmon_pocket_1 = TransmonPocket(design, 'my_id')
        transmon_pocket_1.make()
        transmon_pocket_1.get_template_options(design)

        a_linestring = draw.LineString([[0, 0], [0, 1]])
        a_poly = draw.rectangle(2, 2, 0, 0)
        qgt.add_qgeometry('path',
                          'my_id', {'n_sprial': a_linestring},
                          width=4000)
        qgt.add_qgeometry('poly',
                          'my_id', {'n_spira_etch': a_poly},
                          subtract=True)

        result = renderer._get_chip_names()
        self.assertEqual(result, {'main': {}})

    def test_renderer_setup_renderers(self):
        """Test setup_renderers in setup_defauts.py."""
        actual = setup_default.setup_renderers()
        self.assertEqual(actual, {})

    def test_renderer_renderer_base_element_table_data(self):
        """Test element_table_data in QRenderer."""
        renderer = QRenderer
        etd = renderer.element_table_data

        self.assertEqual(len(etd), 0)

    def test_renderer_ansys_renderer_element_table_data(self):
        """Test element_table_data in QAnsysRenderer."""
        design = designs.DesignPlanar()
        renderer = QAnsysRenderer(design, initiate=False)
        etd = renderer.element_table_data

        self.assertEqual(len(etd), 2)
        self.assertEqual(len(etd['path']), 1)
        self.assertEqual(len(etd['junction']), 4)

        self.assertEqual(etd['path']['wire_bonds'], False)
        self.assertEqual(etd['junction']['inductance'], '10nH')
        self.assertEqual(etd['junction']['capacitance'], 0)
        self.assertEqual(etd['junction']['resistance'], 0)
        self.assertEqual(etd['junction']['mesh_kw_jj'], 7e-06)

    def test_renderer_gdsrenderer_high_level(self):
        """Test that high level defaults were not accidentally changed in
        gds_renderer.py."""
        design = designs.DesignPlanar()
        renderer = QGDSRenderer(design)

        self.assertEqual(renderer.name, 'gds')
        element_table_data = renderer.element_table_data
        self.assertEqual(len(element_table_data), 2)

        self.assertEqual(len(element_table_data['junction']), 1)
        self.assertEqual(element_table_data['junction']['cell_name'],
                         'my_other_junction')

        self.assertEqual(len(element_table_data['path']), 1)
        self.assertEqual(element_table_data['path']['make_airbridge'], False)

    def test_renderer_gdsrenderer_update_units(self):
        """Test update_units in gds_renderer.py."""
        design = designs.DesignPlanar()
        renderer = QGDSRenderer(design)

        renderer.options['gds_unit'] = 12345
        self.assertEqual(renderer.options['gds_unit'], 12345)

        renderer._update_units()
        self.assertEqual(renderer.options['gds_unit'], 0.001)

    def test_renderer_gdsrenderer_midpoint_xy(self):
        """Test midpoint_xy in gds_renderer.py."""
        actual = QGDSRenderer._midpoint_xy(10, 15, 20, 30)
        self.assertEqual(len(actual), 2)
        self.assertEqual(actual[0], 15.0)
        self.assertEqual(actual[1], 22.5)

    # pylint: disable-msg=unused-variable
    def test_renderer_gdsrenderer_check_qcomps(self):
        """Test check_qcomps in gds_renderer.py."""
        design = designs.DesignPlanar()
        renderer = QGDSRenderer(design)

        actual = []
        actual.append(renderer._check_qcomps([]))
        actual.append(renderer._check_qcomps(['Q1', 'Q2', 'Q3']))
        actual.append(renderer._check_qcomps(['Q1', 'Q2', 'Q3', 'Q1']))

        expected = []
        expected.append(([], 0))
        expected.append((['Q2', 'Q3', 'Q1'], 1))
        expected.append((['Q2', 'Q3', 'Q1'], 1))

        for x in range(3):
            my_length = len(actual[x][0])
            self.assertEqual(my_length, len(expected[x][0]))
            self.assertEqual(actual[x][1], expected[x][1])

            for y, _ in enumerate(expected[x][0]):
                self.assertTrue(_ in actual[x][0])

    def test_renderer_mpl_interaction_disconnect(self):
        """Test disconnect in MplInteraction in mpl_interaction.py."""
        mpl = MplInteraction(_plt)
        mpl.disconnect()
        self.assertEqual(mpl.figure, None)

    def test_renderer_gds_check_uniform_airbridge(self):
        """Tests uniform airbridge placement via Airbridging"""
        design = designs.DesignPlanar()
        open_start_options = Dict(pos_x='1000um',
                                  pos_y='0um',
                                  orientation='-90')
        open_start_meander = OpenToGround(design,
                                          'Open_meander_start',
                                          options=open_start_options)
        open_end_options = Dict(pos_x='1200um',
                                pos_y='500um',
                                orientation='0',
                                termination_gap='10um')
        open_end_meander = OpenToGround(design,
                                        'Open_meander_end',
                                        options=open_end_options)
        meander_options = Dict(pin_inputs=Dict(
            start_pin=Dict(component='Open_meander_start', pin='open'),
            end_pin=Dict(component='Open_meander_end', pin='open')),
                               fillet='49.99um',
                               gds_make_airbridge=True)
        testMeander = RouteMixed(design, 'meanderTest', options=meander_options)

        airbridging = Airbridging(design=design,
                                  lib=None,
                                  minx=None,
                                  miny=None,
                                  maxx=None,
                                  maxy=None,
                                  chip_name=None,
                                  precision=0.000001)
        ab_placement_result = airbridging.find_uniform_ab_placement(
            cpw_name='meanderTest',
            bridge_pitch=0.3,  # in mm
            bridge_minimum_spacing=0.005)  # in mm
        ab_placement_check = [(1.0, 0.4, 90.0), (1.1, 0.5, 0.0),
                              (1.0146417320084844, 0.4853582679915155, 45.0)]
        self.assertEqual(ab_placement_result, ab_placement_check)

        test_ab_qgeom = pd.DataFrame({
            'geometry': [draw.Polygon([(0, 0), (1, 0), (0, 1)])],
            'layer': [1]
        })
        df_result = airbridging.ab_placement_to_df(
            ab_placement=ab_placement_result, ab_qgeom=test_ab_qgeom)

        self.assertIn('MultiPoly', df_result)
        self.assertIn('layer', df_result)

    def test_renderer_gds_check_cheese(self):
        """Test check_cheese in gds_renderer.py."""
        design = designs.DesignPlanar()
        renderer = QGDSRenderer(design)

        self.assertEqual(renderer._check_cheese('main', 0), 4)
        self.assertEqual(renderer._check_cheese('main', 1), 1)
        self.assertEqual(renderer._check_cheese('fake', 0), 3)

    def test_renderer_gds_check_no_cheese(self):
        """Test check_no_cheese in gds_renderer.py."""
        design = designs.DesignPlanar()
        renderer = QGDSRenderer(design)

        self.assertEqual(renderer._check_no_cheese('main', 0), 4)
        self.assertEqual(renderer._check_no_cheese('main', 1), 1)
        self.assertEqual(renderer._check_no_cheese('fake', 0), 3)

    def test_renderer_gds_check_either_cheese(self):
        """Test check_either_cheese in gds_renderer.py."""
        design = designs.DesignPlanar()
        renderer = QGDSRenderer(design)

        self.assertEqual(renderer._check_either_cheese('main', 0), 6)
        self.assertEqual(renderer._check_either_cheese('main', 1), 1)
        self.assertEqual(renderer._check_either_cheese('fake', 0), 5)

    def test_successful_get_convergence(self):
        """Test get_convergence returns the correct Boolean when converged"""

        convergence_txt = '''Setup : Setup
        \nProblem Type : CG\n
        \n==================\n
        Number of Passes\n
        Completed : 15\n
        Maximum   : 20\n
        Minimum   : 2\n
        ==================\n
        Criterion : Delta %\n
        Target    : 0.1\n
        Current   : 0.042998\n
        ==================\n
        Pass|# Triangle| Delta %|\n
        1|       108|     N/A|\n
        2|       326|   1.739|\n
        3|       966|  1.3044|\n
        4|      2358|  1.2871|\n
        5|      3040|  1.0324|\n
        6|      4038| 0.53456|\n
        7|      5470| 0.50188|\n
        8|      7440| 0.28342|\n
        9|     10122| 0.33775|\n
        10|     13768| 0.10967|\n
        11|     18498| 0.11437|\n
        12|     25044| 0.13151|\n
        13|     33562| 0.13472|\n
        14|     44028| 0.07696|\n
        15|     57390|0.042998|\n\n'''
        design = designs.DesignPlanar()
        renderer = QQ3DRenderer(design, initiate=False)
        renderer._pinfo = MagicMock()
        renderer._pinfo.setup = MagicMock()
        renderer._pinfo.setup.get_convergence = MagicMock()
        renderer._pinfo.setup.get_convergence.return_value = (None,
                                                              convergence_txt)
        self.assertTrue(renderer.get_convergence())

    def test_unsuccessful_get_convergence(self):
        """Test get_convergence returns the correct Boolean when not converged"""

        convergence_txt = ''''Setup : Setup\n
            Problem Type : CG\n\n
            ==================\n
            Number of Passes\n
            Completed : 2\n
            Maximum   : 2\n
            Minimum   : 2\n
            ==================\n
            Criterion : Delta %\n
            Target    : 0.1\n
            Current   : 1.739\n
            ==================\n
            Pass|# Triangle|Delta %|\n
            1|       108|    N/A|\n
            2|       326|  1.739|\n\n'''
        design = designs.DesignPlanar()
        renderer = QQ3DRenderer(design, initiate=False)
        renderer._pinfo = MagicMock()
        renderer._pinfo.setup = MagicMock()
        renderer._pinfo.setup.get_convergence = MagicMock()
        renderer._pinfo.setup.get_convergence.return_value = (None,
                                                              convergence_txt)
        self.assertFalse(renderer.get_convergence())


if __name__ == '__main__':
    unittest.main(verbosity=2)
