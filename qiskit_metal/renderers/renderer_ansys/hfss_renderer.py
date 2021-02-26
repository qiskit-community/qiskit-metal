# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
'''
@date: 2020
@author: Dennis Wang
'''

from collections import defaultdict
from pathlib import Path
from typing import Union, Tuple

import logging
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyEPR as epr
from pyEPR.ansys import set_property, parse_units
from pyEPR.reports import (plot_convergence_f_vspass, plot_convergence_max_df,
                           plot_convergence_maxdf_vs_sol,
                           plot_convergence_solved_elem)
from qiskit_metal import Dict
from qiskit_metal.draw.utility import to_vec3D
from qiskit_metal.renderers.renderer_ansys.ansys_renderer import (
    QAnsysRenderer, get_clean_name)


class QHFSSRenderer(QAnsysRenderer):
    """
    Subclass of QAnsysRenderer for running HFSS simulations.
    """

    name = 'hfss'
    """name"""

    hfss_options = Dict()  # For potential future use

    def __init__(self,
                 design: 'QDesign',
                 initiate=True,
                 render_template: Dict = None,
                 render_options: Dict = None):
        """
        Create a QRenderer for HFSS simulations, subclassed from QAnsysRenderer.

        Args:
            design (QDesign): Use QGeometry within QDesign to obtain elements for Ansys.
            initiate (bool, optional): True to initiate the renderer. Defaults to True.
            render_template (Dict, optional): Typically used by GUI for template options for GDS. Defaults to None.
            render_options (Dict, optional):  Used to override all options. Defaults to None.
        """
        super().__init__(design=design,
                         initiate=initiate,
                         render_template=render_template,
                         render_options=render_options)

        self.chip_subtract_dict = defaultdict(set)
        self.assign_perfE = []
        self.assign_mesh = []
        self.jj_lumped_ports = {}
        self.jj_to_ignore = set()

        self.current_sweep = None

        QHFSSRenderer.load()

    def render_design(self,
                      selection: Union[list, None] = None,
                      open_pins: Union[list, None] = None,
                      port_list: Union[list, None] = None,
                      jj_to_port: Union[list, None] = None,
                      ignored_jjs: Union[list, None] = None,
                      box_plus_buffer: bool = True):
        """
        Initiate rendering of components in design contained in selection, assuming they're valid.
        Components are rendered before the chips they reside on, and subtraction of negative shapes
        is performed at the very end. Add the metallize() method here to turn objects in self.assign_perfE
        (see init in QAnsysRenderer class) into perfect electrical conductors. Create lumped ports as needed.

        Among the components selected for export, there may or may not be unused (unconnected) pins.
        The second parameter, open_pins, contains tuples of the form (component_name, pin_name) that
        specify exactly which pins should be open rather than shorted during the simulation. Both the
        component and pin name must be specified because the latter could be shared by multiple
        components. All pins in this list are rendered with an additional endcap in the form of a
        rectangular cutout, to be subtracted from its respective plane.

        In driven modal solutions, the Ansys design must include one or more ports. This is done by adding
        all port designations and their respective impedances in Ohms as (qcomp, pin, impedance) to
        port_list. Note that an open endcap must separate the two sides of each pin before inserting a lumped
        port in between, so behind the scenes all pins in port_list are also added to open_pins. Practically,
        however, port_list and open_pins are inputted as mutually exclusive lists.

        Also in driven modal solutions, one may want to render junctions as lumped ports rather than RLC sheets.
        To do so, tuples of the form (component_name, element_name, impedance) are added to the list jj_to_port.
        For example, ('Q1', 'rect_jj', 70) indicates that rect_jj of component Q1 is to be rendered as a lumped
        port with an impedance of 70 Ohms. Finally, and again for driven modal solutions, one may want to
        disregard select junctions in the Metal design altogether to simulate the capacitive effect while keeping
        the qubit in an "off" state. Such junctions are listed in the form (component_name, element_name) in the
        list ignored_jjs.

        Args:
            selection (Union[list, None], optional): List of components to render. Defaults to None.
            open_pins (Union[list, None], optional): List of tuples of pins that are open. Defaults to None.
            port_list (Union[list, None], optional): List of tuples of pins to be rendered as ports. Defaults to None.
            jj_to_port (Union[list, None], optional): List of tuples of jj's to be rendered as ports. Defaults to None.
            ignored_jjs (Union[list, None], optional): List of tuples of jj's that shouldn't be rendered. Defaults to None.
            box_plus_buffer (bool): Either calculate a bounding box based on the location of rendered geometries
                                     or use chip size from design class.
        """
        self.chip_subtract_dict = defaultdict(set)
        self.assign_perfE = []
        self.assign_mesh = []
        self.jj_lumped_ports = {}
        self.jj_to_ignore = set()

        if jj_to_port:
            self.jj_lumped_ports = {
                (qcomp, elt): impedance for qcomp, elt, impedance in jj_to_port
            }

        if ignored_jjs:
            self.jj_to_ignore = {(qcomp, qelt) for qcomp, qelt in ignored_jjs}

        self.render_tables(selection)
        if port_list:
            self.add_endcaps(open_pins +
                             [(qcomp, pin) for qcomp, pin, _ in port_list])
        else:
            self.add_endcaps(open_pins)

        self.render_chips(box_plus_buffer=box_plus_buffer)
        self.subtract_from_ground()
        self.add_mesh()
        self.metallize()
        if port_list:
            self.create_ports(port_list)

    def create_ports(self, port_list: list):
        """
        Add ports and their respective impedances in Ohms to designated pins in port_list.
        Port_list is formatted as [(qcomp_0, pin_0, impedance_0), (qcomp_1, pin_1, impedance_1), ...].

        Args:
            port_list (list): List of tuples of pins to be rendered as ports.
        """
        for qcomp, pin, impedance in port_list:
            port_name = f'Port_{qcomp}_{pin}'
            pdict = self.design.components[qcomp].pins[pin]
            midpt, gap_size, norm_vec, width = pdict['middle'], pdict['gap'], \
                                               pdict['normal'], pdict['width']
            width = parse_units(width)
            endpoints = parse_units([midpt, midpt + gap_size * norm_vec])
            endpoints_3d = to_vec3D(endpoints, 0)  # Set z height to 0
            x0, y0 = endpoints_3d[0][:2]
            x1, y1 = endpoints_3d[1][:2]
            if abs(y1 - y0) > abs(x1 - x0):
                # Junction runs vertically up/down
                x_min, x_max = x0 - width / 2, x0 + width / 2
                y_min, y_max = min(y0, y1), max(y0, y1)
            else:
                # Junction runs horizontally left/right
                x_min, x_max = min(x0, x1), max(x0, x1)
                y_min, y_max = y0 - width / 2, y0 + width / 2

            # Draw rectangle
            self.logger.debug(f'Drawing a rectangle: {port_name}')
            poly_ansys = self.modeler.draw_rect_corner([x_min, y_min, 0],
                                                       x_max - x_min,
                                                       y_max - y_min, 0,
                                                       **dict(transparency=0.0))
            axis = 'x' if abs(x1 - x0) > abs(y1 - y0) else 'y'
            poly_ansys.make_lumped_port(axis,
                                        z0=str(impedance) + 'ohm',
                                        name=f'LumpPort_{qcomp}_{pin}')
            self.modeler.rename_obj(poly_ansys, port_name)

            # Draw line
            lump_line = self.modeler.draw_polyline(
                [endpoints_3d[0], endpoints_3d[1]],
                closed=False,
                **dict(color=(128, 0, 128)))
            lump_line = lump_line.rename(f'voltage_line_{port_name}')
            lump_line.show_direction = True

    def render_element_junction(self, qgeom: pd.Series):
        """
        Render a Josephson junction depending on the solution type.
        If in HFSS eigenmode, junctions are rendered as inductors consisting of
        1. A rectangle of length pad_gap and width inductor_width. Defines lumped element
           RLC boundary condition.
        2. A line that is later used to calculate the voltage in post-processing analysis.
        If in HFSS driven modal, junctions can either be inductors or lumped ports. The
        latter are characterized by an impedance value given in the list jj_to_port when
        render_design() is called.

        Args:
            qgeom (pd.Series): GeoSeries of element properties.
        """
        ansys_options = dict(transparency=0.0)

        qcomp = self.design._components[qgeom['component']].name
        qc_elt = get_clean_name(qgeom['name'])

        if (qcomp, qc_elt) not in self.jj_to_ignore:

            if (qcomp, qc_elt) in self.jj_lumped_ports:
                # Treat the junction as a lumped port.
                qc_name = qcomp
                port_name = f'Port_{qcomp}_{qc_elt}'
                impedance = self.jj_lumped_ports[(qcomp, qc_elt)]
            else:
                # Treat the junction as an inductor.
                qc_name = 'Lj_' + qcomp
                inductor_name = f'{qc_name}{QAnsysRenderer.NAME_DELIM}{qc_elt}'

            qc_shapely = qgeom.geometry
            qc_chip_z = parse_units(self.design.get_chip_z(qgeom.chip))
            qc_width = parse_units(qgeom.width)

            endpoints = parse_units(list(qc_shapely.coords))
            endpoints_3d = to_vec3D(endpoints, qc_chip_z)
            x0, y0, z0 = endpoints_3d[0]
            x1, y1, z0 = endpoints_3d[1]
            if abs(y1 - y0) > abs(x1 - x0):
                # Junction runs vertically up/down
                x_min, x_max = x0 - qc_width / 2, x0 + qc_width / 2
                y_min, y_max = min(y0, y1), max(y0, y1)
            else:
                # Junction runs horizontally left/right
                x_min, x_max = min(x0, x1), max(x0, x1)
                y_min, y_max = y0 - qc_width / 2, y0 + qc_width / 2

            if (qcomp, qc_elt) in self.jj_lumped_ports:
                # Draw rectangle for lumped port.
                self.logger.debug(f'Drawing a rectangle: {port_name}')
                poly_ansys = self.modeler.draw_rect_corner(
                    [x_min, y_min, qc_chip_z], x_max - x_min, y_max - y_min,
                    qc_chip_z, **ansys_options)
                axis = 'x' if abs(x1 - x0) > abs(y1 - y0) else 'y'
                poly_ansys.make_lumped_port(axis,
                                            z0=str(impedance) + 'ohm',
                                            name=f'LumpPort_{qcomp}_{qc_elt}')
                self.modeler.rename_obj(poly_ansys, port_name)
                # Draw line for lumped port.
                lump_line = self.modeler.draw_polyline(
                    [endpoints_3d[0], endpoints_3d[1]],
                    closed=False,
                    **dict(color=(128, 0, 128)))
                lump_line = lump_line.rename(f'voltage_line_{port_name}')
                lump_line.show_direction = True
            else:
                # Draw rectangle for inductor.
                self.logger.debug(f'Drawing a rectangle: {inductor_name}')
                poly_ansys = self.modeler.draw_rect_corner(
                    [x_min, y_min, qc_chip_z], x_max - x_min, y_max - y_min,
                    qc_chip_z, **ansys_options)
                axis = 'x' if abs(x1 - x0) > abs(y1 - y0) else 'y'
                poly_ansys.make_rlc_boundary(axis,
                                             l=qgeom['hfss_inductance'],
                                             c=qgeom['hfss_capacitance'],
                                             r=qgeom['hfss_resistance'],
                                             name='Lj_' + inductor_name)
                self.modeler.rename_obj(poly_ansys, 'JJ_rect_' + inductor_name)
                self.assign_mesh.append('JJ_rect_' + inductor_name)
                # Draw line for inductor.
                poly_jj = self.modeler.draw_polyline(
                    [endpoints_3d[0], endpoints_3d[1]],
                    closed=False,
                    **dict(color=(128, 0, 128)))
                poly_jj = poly_jj.rename('JJ_' + inductor_name + '_')
                poly_jj.show_direction = True

    def metallize(self):
        """
        Assign metallic property to all shapes in self.assign_perfE list.
        """
        self.modeler.assign_perfect_E(self.assign_perfE)

    def add_drivenmodal_design(self, name: str, connect: bool = True):
        """
        Add a driven modal design with the given name to the project.

        Args:
            name (str): Name of the new driven modal design
            connect (bool, optional): Should we connect this session to this design? Defaults to True
        """
        if self.pinfo:
            adesign = self.pinfo.project.new_dm_design(name)
            if connect:
                self.connect_ansys_design(adesign.name)
            return adesign
        else:
            self.logger.info("Are you mad?? You have to connect to ansys and a project " \
                            "first before creating a new design . Use self.connect_ansys()")

    def activate_drivenmodal_design(self, name: str = "MetalHFSSDrivenModal"):
        """Add a hfss drivenmodal design with the given name to the project.  If the design exists, that will be added WITHOUT
        altering the suffix of the design name.

        Args:
            name (str): Name of the new q3d design
        """
        if self.pinfo:
            if self.pinfo.project:
                try:
                    names_in_design = self.pinfo.project.get_design_names()
                except AttributeError:
                    self.logger.error(
                        'Please install a more recent version of pyEPR (>=0.8.4.5)'
                    )

                if name in names_in_design:
                    self.pinfo.connect_design(name)
                    oDesktop = self.pinfo.design.parent.parent._desktop  # self.pinfo.design does not work
                    oProject = oDesktop.SetActiveProject(
                        self.pinfo.project_name)
                    oDesign = oProject.SetActiveDesign(name)
                else:
                    self.logger.warning(
                        f'The name={name} was not in active project.  '
                        'A new design will be inserted to the project.  '
                        f'Names in active project are: \n{names_in_design}.  ')
                    adesign = self.add_drivenmodal_design(name=name,
                                                          connect=True)

            else:
                self.logger.warning(
                    "Project not available, have you opened a project?")
        else:
            self.logger.warning(
                "Have you run connect_ansys()?  Cannot find a reference to Ansys in QRenderer."
            )

    def activate_drivenmodal_setup(self, setup_name_activate: str = None):
        """For active design, either get existing setup, make new setup with name, 
        or make new setup with default name.

        Args:
            setup_name_activate (str, optional): If name exists for setup, then have pinfo reference it. 
            If name for setup does not exist, create a new setup with the name.  If name is None, 
            create a new setup with default name.
        """
        if self.pinfo:
            if self.pinfo.project:
                if self.pinfo.design:
                    # look for setup name, if not there, then add a new one
                    if setup_name_activate:
                        all_setup_names = self.pinfo.design.get_setup_names()
                        self.pinfo.setup_name = setup_name_activate
                        if setup_name_activate in all_setup_names:
                            # When name is given and in design. So have pinfo reference existing setup.
                            self.pinfo.setup = self.pinfo.get_setup(
                                self.pinfo.setup_name)
                        else:
                            # When name is given, but not in design. So make a new setup with given name.
                            self.pinfo.setup = self.add_drivenmodal_setup(
                                name=self.pinfo.setup_name)
                    else:
                        # When name is not given, so use default name for setup.
                        # default name is "Setup"
                        self.pinfo.setup = self.add_drivenmodal_setup()
                        self.pinfo.setup_name = self.pinfo.setup.name

                else:
                    self.logger.warning(
                        " The design within a project is not available, have you opened a design?"
                    )
            else:
                self.logger.warning(
                    "Project not available, have you opened a project?")
        else:
            self.logger.warning(
                "Have you run connect_ansys()?  Cannot find a reference to Ansys in QRenderer."
            )

    def add_drivenmodal_setup(self,
                              freq_ghz=5,
                              name="Setup",
                              max_delta_s=0.1,
                              max_passes=10,
                              min_passes=1,
                              min_converged=1,
                              pct_refinement=30,
                              basis_order=1):
        # TODO: Move arguments to default options.
        """
        Create a solution setup in Ansys HFSS Driven Modal.

        Args:
            freq_ghz (int, optional): Frequency in GHz. Defaults to 5.
            name (str, optional): Name of driven modal setup. Defaults to "Setup".
            max_delta_s (float, optional): Absolute value of maximum difference in scattering parameter S. Defaults to 0.1.
            max_passes (int, optional): Maximum number of passes. Defaults to 10.
            min_passes (int, optional): Minimum number of passes. Defaults to 1.
            min_converged (int, optional): Minimum number of converged passes. Defaults to 1.
            pct_refinement (int, optional): Percent refinement. Defaults to 30.
            basis_order (int, optional): Basis order. Defaults to -1.
        """
        if self.pinfo:
            if self.pinfo.design:
                return self.pinfo.design.create_dm_setup(
                    freq_ghz=freq_ghz,
                    name=name,
                    max_delta_s=max_delta_s,
                    max_passes=max_passes,
                    min_passes=min_passes,
                    min_converged=min_converged,
                    pct_refinement=pct_refinement,
                    basis_order=basis_order)

    def add_eigenmode_design(self, name: str, connect: bool = True):
        """
        Add an eigenmode design with the given name to the project.

        Args:
            name (str): Name of the new eigenmode design
            connect (bool, optional): Should we connect this session to this design? Defaults to True

        Returns(pyEPR.ansys.HfssDesign): A eigenmode  within Ansys.

        """
        if self.pinfo:
            adesign = self.pinfo.project.new_em_design(name)
            if connect:
                self.connect_ansys_design(adesign.name)
            return adesign
        else:
            self.logger.info("Are you mad?? You have to connect to ansys and a project " \
                            "first before creating a new design . Use self.connect_ansys()")

    def activate_eigenmode_design(self, name: str = "MetalHFSSEigenmode"):
        """Add a hfss eigenmode design with the given name to the project.  If the design exists, that will be added WITHOUT
        altering the suffix of the design name.

        Args:
            name (str): Name of the new q3d design
        """
        if self.pinfo:
            if self.pinfo.project:
                try:
                    names_in_design = self.pinfo.project.get_design_names()
                except AttributeError:
                    self.logger.error(
                        'Please install a more recent version of pyEPR (>=0.8.4.5)'
                    )

                if name in names_in_design:
                    self.pinfo.connect_design(name)
                    oDesktop = self.pinfo.design.parent.parent._desktop  # self.pinfo.design does not work
                    oProject = oDesktop.SetActiveProject(
                        self.pinfo.project_name)
                    oDesign = oProject.SetActiveDesign(name)
                else:
                    self.logger.warning(
                        f'The name={name} was not in active project.  '
                        'A new design will be inserted to the project.  '
                        f'Names in active project are: \n{names_in_design}.  ')
                    adesign = self.add_eigenmode_design(name=name, connect=True)

            else:
                self.logger.warning(
                    "Project not available, have you opened a project?")
        else:
            self.logger.warning(
                "Have you run connect_ansys()?  Cannot find a reference to Ansys in QRenderer."
            )

    def activate_eigenmode_setup(self, setup_name_activate: str = None):
        """For active design, either get existing setup, make new setup with name, 
        or make new setup with default name.

        Args:
            setup_name_activate (str, optional): If name exists for setup, then have pinfo reference it. 
            If name for setup does not exist, create a new setup with the name.  If name is None, 
            create a new setup with default name.
        """
        if self.pinfo:
            if self.pinfo.project:
                if self.pinfo.design:
                    # look for setup name, if not there, then add a new one
                    if setup_name_activate:
                        all_setup_names = self.pinfo.design.get_setup_names()
                        self.pinfo.setup_name = setup_name_activate
                        if setup_name_activate in all_setup_names:
                            # When name is given and in design. So have pinfo reference existing setup.
                            self.pinfo.setup = self.pinfo.get_setup(
                                self.pinfo.setup_name)
                        else:
                            # When name is given, but not in design. So make a new setup with given name.
                            self.pinfo.setup = self.add_eigenmode_setup(
                                name=self.pinfo.setup_name)
                    else:
                        # When name is not given, so use default name for setup.
                        # default name is "Setup"
                        self.pinfo.setup = self.add_eigenmode_setup()
                        self.pinfo.setup_name = self.pinfo.setup.name

                else:
                    self.logger.warning(
                        " The design within a project is not available, have you opened a design?"
                    )
            else:
                self.logger.warning(
                    "Project not available, have you opened a project?")
        else:
            self.logger.warning(
                "Have you run connect_ansys()?  Cannot find a reference to Ansys in QRenderer."
            )

    def add_eigenmode_setup(self,
                            name="Setup",
                            min_freq_ghz=1,
                            n_modes=1,
                            max_delta_f=0.5,
                            max_passes=10,
                            min_passes=1,
                            min_converged=1,
                            pct_refinement=30,
                            basis_order=-1):
        # TODO: Move arguments to default options.
        """
        Create a solution setup in Ansys HFSS Eigenmode.

        Args:
            name (str, optional): Name of eigenmode setup. Defaults to "Setup".
            min_freq_ghz (int, optional): Minimum frequency in GHz. Defaults to 1.
            n_modes (int, optional): Number of modes. Defaults to 1.
            max_delta_f (float, optional): Maximum difference in freq between consecutive passes. Defaults to 0.1.
            max_passes (int, optional): Maximum number of passes. Defaults to 10.
            min_passes (int, optional): Minimum number of passes. Defaults to 1.
            min_converged (int, optional): Minimum number of converged passes. Defaults to 1.
            pct_refinement (int, optional): Percent refinement. Defaults to 30.
            basis_order (int, optional): Basis order. Defaults to -1.
        """
        if self.pinfo:
            if self.pinfo.design:
                return self.pinfo.design.create_em_setup(
                    name=name,
                    min_freq_ghz=min_freq_ghz,
                    n_modes=n_modes,
                    max_delta_f=max_delta_f,
                    max_passes=max_passes,
                    min_passes=min_passes,
                    min_converged=min_converged,
                    pct_refinement=pct_refinement,
                    basis_order=basis_order)

    def set_mode(self, mode: int, setup_name: str):
        """Set the eigenmode in pyEPR for a design with solution_type set to Eigenmode.

        Args:
            mode (int): Identify a mode from 1 to n_modes.
            setup_name (str): Select a setup from the active design. 
        """
        if self.pinfo:
            if self.pinfo.project:
                if self.pinfo.design:
                    oDesktop = self.pinfo.design.parent.parent._desktop  # self.pinfo.design does not work
                    oProject = oDesktop.SetActiveProject(
                        self.pinfo.project_name)
                    oDesign = oProject.GetActiveDesign()
                    if oDesign.GetSolutionType() == 'Eigenmode':
                        # The set_mode() method is in HfssEMDesignSolutions class in pyEPR.
                        # The class HfssEMDesignSolutions is instantiated by get_setup() and create_em_setup().
                        setup = self.pinfo.get_setup(setup_name)
                        if 0 < int(mode) <= int(setup.n_modes):
                            setup_solutions = setup.get_solutions()
                            if setup_solutions:
                                setup_solutions.set_mode(mode)
                            else:
                                self.logger.warning(
                                    'Not able to get setup_solutions, the mode was not set.'
                                )
                        else:
                            self.logger.warning(
                                f'The requested mode={mode} is not a valid (1 to {setup.n_modes}) selection. '
                                'The mode was not set.')
                    else:
                        self.logger.warning(
                            'The design does not have solution type as "Eigenmode". The mode was not set.'
                        )
                else:
                    self.logger.warning(
                        'A design is not in active project. The mode was not set.'
                    )
            else:
                self.logger.warning(
                    "Project not available, have you opened a project? The mode was not set."
                )
        else:
            self.logger.warning(
                "Have you run connect_ansys()?  "
                "Cannot find a reference to Ansys in QRenderer.  The mode was not set."
            )

    def analyze_setup(self, setup_name: str):
        """
        Run a specific solution setup in Ansys HFSS.

        Args:
            setup_name (str): Name of setup.
        """
        if self.pinfo:
            setup = self.pinfo.get_setup(setup_name)
            setup.analyze()

    def add_sweep(self,
                  setup_name="Setup",
                  start_ghz=2.0,
                  stop_ghz=8.0,
                  count=101,
                  step_ghz=None,
                  name="Sweep",
                  type="Fast",
                  save_fields=False):
        """
        Add a frequency sweep to a driven modal setup.

        Args:
            setup_name (str, optional): Name of driven modal simulation setup. Defaults to "Setup".
            start_ghz (float, optional): Starting frequency of sweep in GHz. Defaults to 2.0.
            stop_ghz (float, optional): Ending frequency of sweep in GHz. Defaults to 8.0.
            count (int, optional): Total number of frequencies. Defaults to 101.
            step_ghz ([type], optional): Difference between adjacent frequencies. Defaults to None.
            name (str, optional): Name of sweep. Defaults to "Sweep".
            type (str, optional): Type of sweep. Defaults to "Fast".
            save_fields (bool, optional): Whether or not to save fields. Defaults to False.
        """
        if self.pinfo:
            setup = self.pinfo.get_setup(setup_name)
            return setup.insert_sweep(start_ghz=start_ghz,
                                      stop_ghz=stop_ghz,
                                      count=count,
                                      step_ghz=step_ghz,
                                      name=name,
                                      type=type,
                                      save_fields=save_fields)

    def analyze_sweep(self, sweep_name: str, setup_name: str):
        """
        Analyze a single sweep within the setup.

        Args:
            sweep_name (str): Name of sweep to analyze.
            setup_name (str): Name of setup to analyze.
        """
        if self.pinfo:
            setup = self.pinfo.get_setup(setup_name)
            sweep = setup.get_sweep(sweep_name)
            sweep.analyze_sweep()
            self.current_sweep = sweep

    def plot_s_params(self, getS: Union[list, None] = None):
        """
        Plot one or more S parameters as a function of frequency.

        Args:
            getS (Union[list, None], optional): S parameters to plot. Defaults to None.
        """
        if self.current_sweep:
            freqs, Scurves = self.current_sweep.get_network_data(getS)
            Sparams = pd.DataFrame(Scurves, columns=freqs / 1e9,
                                   index=getS).transpose()
            fig = plt.figure(10)
            fig.clf()
            ax = plt.gca()
            Sparams.apply(lambda x: 20 * np.log10(np.abs(x))).plot(ax=ax)
            ax.autoscale()
            display(fig)

    def distributed_analysis(self):
        """Returns class containing info on Hamiltonian parameters from HFSS simulation.

        Returns:
            DistributedAnalysis: A  class from pyEPR which does DISTRIBUTED ANALYSIS of layout 
            and microwave results.  It is the main computation class & interface with HFSS.  
            This class defines a DistributedAnalysis object which calculates
            and saves Hamiltonian parameters from an HFSS simulation.  
            It allows one to calculate dissipation.
        """
        if self.pinfo:
            return epr.DistributedAnalysis(self.pinfo)

    def get_convergences(self, variation: str = None):
        """Get convergence for convergence_t and convergence_f. 

        Args:
            variation (str, optional):  Information from pyEPR; variation should be in the form
            variation = "scale_factor='1.2001'". Defaults to None.

        Returns:
            tuple[pandas.core.frame.DataFrame, pandas.core.frame.DataFrame]: 
            1st DataFrame: convergence_t
            2nd DataFrame: convergence_f
        """
        if self.pinfo:
            design = self.pinfo.design
            setup = self.pinfo.setup
            convergence_t, _ = setup.get_convergence(variation)
            convergence_f = hfss_report_f_convergence(
                design, setup, self.logger, [])  # TODO; Fix variation []
            return convergence_t, convergence_f

    def plot_convergences(self,
                          variation: str = None,
                          fig: mpl.figure.Figure = None):
        """Plot the convergences in Ansys window.

        Args:
            variation (str, optional): Information from pyEPR; variation should be in the form
            variation = "scale_factor='1.2001'". Defaults to None.
            fig (matplotlib.figure.Figure, optional): A mpl figure. Defaults to None.
        """
        if self.pinfo:
            convergence_t, convergence_f = self.get_convergences(variation)
            hfss_plot_convergences_report(convergence_t,
                                          convergence_f,
                                          fig=fig,
                                          _display=True)


def hfss_plot_convergences_report(convergence_t: pd.core.frame.DataFrame,
                                  convergence_f: pd.core.frame.DataFrame,
                                  fig: mpl.figure.Figure = None,
                                  _display=True):
    """Plot convergence frequency vs. pass number if fig is None.
    Plot delta frequency and solved elements vs. pass number.
    Plot delta frequency vs. solved elements.

    Args:
        convergence_t (pandas.core.frame.DataFrame): convergence vs pass number of the eigenemode freqs.
        convergence_f (pandas.core.frame.DataFrame): convergence vs pass number of the eigenemode freqs.
        fig (matplotlib.figure.Figure, optional): A mpl figure. Defaults to None.
        _display (bool, optional): Display the plot? Defaults to True.
    """

    if fig is None:
        fig = plt.figure(figsize=(11, 3.))

        # Grid spec and axes;    height_ratios=[4, 1], wspace=0.5
        gs = mpl.gridspec.GridSpec(1, 3, width_ratios=[1.2, 1.5, 1])
        axs = [fig.add_subplot(gs[i]) for i in range(3)]

        ax0t = axs[1].twinx()
        plot_convergence_f_vspass(axs[0], convergence_f)
        plot_convergence_max_df(axs[1], convergence_t.iloc[:, 1])
        plot_convergence_solved_elem(ax0t, convergence_t.iloc[:, 0])
        plot_convergence_maxdf_vs_sol(axs[2], convergence_t.iloc[:, 1],
                                      convergence_t.iloc[:, 0])

        fig.tight_layout(w_pad=0.1)  # pad=0.0, w_pad=0.1, h_pad=1.0)

        # if _display:
        #     from IPython.display import display
        #     display(fig)


def hfss_report_f_convergence(oDesign: epr.ansys.HfssDesign,
                              setup: epr.ansys.HfssEMSetup,
                              logger: logging.Logger,
                              variation: str = None,
                              save_csv: bool = True):
    """Create a report inside HFSS to plot the converge of frequency and style it.
    Saves report to csv file.
    .. code-block:: text

            re(Mode(1)) [g]	re(Mode(2)) [g]	re(Mode(3)) [g]
        Pass []
        1	4.643101	4.944204	5.586289
        2	5.114490	5.505828	6.242423
        3	5.278594	5.604426	6.296777

    Args:
        oDesign (pyEPR.ansys.HfssDesign): Active design within Ansys.
        setup (pyEPR.ansys.HfssEMSetup): The setup of active project and design within Ansys.
        logger (logging.Logger): To give feedback to user.
        variation ('str', optional): Information from pyEPR; variation should be in the form
            variation = "scale_factor='1.2001'". Defaults to None.
        save_csv (bool, optional): Save to file? Defaults to True.

    Returns:
        pd.core.frame.DataFrame: Returns a convergence vs pass number of the eigenemode frequencies.
    """

    if not oDesign.solution_type == 'Eigenmode':
        return None

    report = oDesign._reporter  # reporter OModule for Ansys

    # Create report
    n_modes = int(setup.n_modes)
    ycomp = [f"re(Mode({i}))" for i in range(1, 1 + n_modes)]

    params = ["Pass:=", ["All"]] + variation
    report_name = "Freq. vs. pass"
    if report_name in report.GetAllReportNames():
        report.DeleteReports([report_name])

    solutions = setup.get_solutions()
    solutions.create_report(report_name,
                            "Pass",
                            ycomp,
                            params,
                            pass_name='AdaptivePass')

    # Properties of lines
    curves = [
        f"{report_name}:re(Mode({i})):Curve1" for i in range(1, 1 + n_modes)
    ]
    set_property(report, 'Attributes', curves, 'Line Width', 3)
    set_property(report, 'Scaling', f"{report_name}:AxisY1", 'Auto Units',
                 False)
    set_property(report, 'Scaling', f"{report_name}:AxisY1", 'Units', 'g')
    set_property(report, 'Legend', f"{report_name}:Legend",
                 'Show Solution Name', False)

    if save_csv:  # Save
        try:
            path = Path().absolute(
            ) / 'hfss_eig_f_convergence.csv'  # TODO: Determine better path
            report.ExportToFile(report_name, path)
            logger.info(f'Saved convergences to {path}')
            return pd.read_csv(path, index_col=0)
        except Exception as e:
            logger.error(f"Error could not save and export hfss plot to {path}.\
                           Is the plot made in HFSS with the correct name.\
                           Check the HFSS error window. \t Error =  {e}")

    return None
