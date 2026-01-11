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
# pylint: disable=too-many-lines

from typing import List, Tuple, Union

import re
import os
from pathlib import Path
import math
import geopandas
import numpy as np
import pandas as pd
from numpy.linalg import norm
from collections import defaultdict
from platform import system
from scipy.spatial import distance

import shapely
import pyEPR as epr
from pyEPR.ansys import parse_units, HfssApp, release

from qiskit_metal.draw.utility import to_vec3D
from qiskit_metal.draw.basic import is_rectangle
from qiskit_metal.renderers.renderer_base import QRendererAnalysis
from qiskit_metal.toolbox_metal.parsing import is_true
from qiskit_metal.designs.design_base import QDesign

from qiskit_metal import Dict

from qiskit_metal import config

if not config.is_building_docs():
    from qiskit_metal.toolbox_python.utility_functions import (
        toggle_numbers,
        bad_fillet_idxs,
    )


def good_fillet_idxs(coords: list,
                     fradius: float,
                     precision: int = 9,
                     isclosed: bool = False):
    """
    Get list of vertex indices in a linestring (isclosed = False) or polygon (isclosed = True)
    that can be filleted based on proximity to neighbors.

    Args:
        coords (list): Ordered list of tuples of vertex coordinates.
        fradius (float): User-specified fillet radius from QGeometry table.
        precision (int, optional): Digits of precision used for round(). Defaults to 9.
        isclosed (bool, optional): Boolean denoting whether the shape is a linestring or
            polygon. Defaults to False.

    Returns:
        list: List of indices of vertices that can be filleted.
    """
    if isclosed:
        return toggle_numbers(
            bad_fillet_idxs(coords, fradius, precision, isclosed=True),
            len(coords))
    return toggle_numbers(
        bad_fillet_idxs(coords, fradius, precision, isclosed=False),
        len(coords))[1:-1]


def get_clean_name(name: str) -> str:
    """Create a valid variable name from the given one by removing having it
    begin with a letter or underscore followed by an unlimited string of
    letters, numbers, and underscores.

    Args:
        name (str): Initial, possibly unusable, string to be modified.

    Returns:
        str: Variable name consistent with Python naming conventions.
    """
    # Remove invalid characters
    name = re.sub("[^0-9a-zA-Z_]", "", name)
    # Remove leading characters until we find a letter or underscore
    name = re.sub("^[^a-zA-Z_]+", "", name)
    return name


class QAnsysRenderer(QRendererAnalysis):
    """Extends QRenderer to export designs to Ansys using pyEPR. The methods
        which a user will need for Ansys export should be found within this class.

    Default Options:
        * Lj: '10nH' -- Lj has units of nanoHenries (nH)
        * Cj: 0 -- Cj *must* be 0 for pyEPR analysis! Cj has units of femtofarads (fF)
        * _Rj: 0 -- _Rj *must* be 0 for pyEPR analysis! _Rj has units of Ohms
        * max_mesh_length_jj: '7um' -- Maximum mesh length for Josephson junction elements
        * project_path: None -- Default project path; if None --> get active
        * max_mesh_length_port: '7um' -- Maximum mesh length for Ports in Eigenmode Simulations
        * project_name: None -- Default project name
        * design_name: None -- Default design name
        * ansys_file_extension: '.aedt' -- Ansys file extension for 2016 version and newer
        * x_buffer_width_mm: 0.2 -- Buffer between max/min x and edge of ground plane, in mm
        * y_buffer_width_mm: 0.2 -- Buffer between max/min y and edge of ground plane, in mm
        * wb_threshold:'400um' -- the minimum distance between two vertices of a path for a
          wirebond to be added.
        * wb_offset:'0um' -- offset distance for wirebond placement (along the direction
          of the cpw)
        * wb_size: 3 -- scalar which controls the width of the wirebond (wb_size * path['width'])
    """

    #: Default options, over-written by passing ``options` dict to render_options.
    #: Type: Dict[str, str]
    # yapf: disable
    default_options = Dict(
        Lj='10nH',  # Lj has units of nanoHenries (nH)
        Cj=0,  # Cj *must* be 0 for pyEPR analysis! Cj has units of femtofarads (fF)
        _Rj=0,  # _Rj *must* be 0 for pyEPR analysis! _Rj has units of Ohms
        max_mesh_length_jj='7um',  # maximum mesh length for Josephson junction elements
        max_mesh_length_port='7um', # maximum mesh length for Ports in Eigenmode Simulations
        project_path=None,  # default project path; if None --> get active
        project_name=None,  # default project name
        design_name=None,  # default design name
        # bounding_box_scale_x = 1.2, # Ratio of 'main' chip width to bounding box width
        # bounding_box_scale_y = 1.2, # Ratio of 'main' chip length to bounding box length
        x_buffer_width_mm=0.2,  # Buffer between max/min x and edge of ground plane, in mm
        y_buffer_width_mm=0.2,  # Buffer between max/min y and edge of ground plane, in mm
        wb_threshold = '400um',
        wb_offset = '0um',
        wb_size = 5,
        plot_ansys_fields_options = Dict(
            name="NAME:Mag_E1",
            UserSpecifyName='0',
            UserSpecifyFolder='0',
            QuantityName= "Mag_E",
            PlotFolder= "E Field",
            StreamlinePlot= "False",
            AdjacentSidePlot= "False",
            FullModelPlot= "False",
            IntrinsicVar= "Phase=\'0deg\'",
            PlotGeomInfo_0= "1",
            PlotGeomInfo_1= "Surface",
            PlotGeomInfo_2= "FacesList",
            PlotGeomInfo_3= "1",
        ),
    )
    """Default options"""
    # yapf: enable

    NAME_DELIM = r"_"
    """Name delimiter"""

    name = "ansys"
    """Name"""

    default_setup = Dict(
        drivenmodal=Dict(
            name="Setup",
            freq_ghz="5.0",
            max_delta_s="0.1",
            max_passes="10",
            min_passes="1",
            min_converged="1",
            pct_refinement="30",
            basis_order="1",
        ),
        eigenmode=Dict(
            name="Setup",
            min_freq_ghz="1",
            n_modes="1",
            max_delta_f="0.5",
            max_passes="10",
            min_passes="1",
            min_converged="1",
            pct_refinement="30",
            basis_order="-1",
        ),
        q3d=Dict(
            name="Setup",
            freq_ghz="5.0",
            save_fields="False",
            enabled="True",
            max_passes="15",
            min_passes="2",
            min_converged_passes="2",
            percent_error="0.5",
            percent_refinement="30",
            auto_increase_solution_order="True",
            solution_order="High",
            solver_type="Iterative",
        ),
        port_inductor_gap=
        "10um",  # spacing between port and inductor if junction is drawn both ways
    )
    """Default setup."""

    # When additional columns are added to QGeometry, this is the example to populate it.
    # e.g. element_extensions = dict(
    #         base=dict(color=str, klayer=int),
    #         path=dict(thickness=float, material=str, perfectE=bool),
    #         poly=dict(thickness=float, material=str), )
    """Element extensions dictionary   element_extensions = dict() from base class"""

    # Add columns to junction table during QAnsysRenderer.load()
    # element_extensions  is now being populated as part of load().
    # Determined from element_table_data.

    # Dict structure MUST be same as  element_extensions!!!!!!
    # This dict will be used to update QDesign during init of renderer.
    # Keeping this as a cls dict so could be edited before renderer is instantiated.
    # To update component.options junction table.

    element_table_data = dict(
        path=dict(wire_bonds=False),
        junction=dict(
            inductance=default_options["Lj"],
            capacitance=default_options["Cj"],
            resistance=default_options["_Rj"],
            mesh_kw_jj=parse_units(default_options["max_mesh_length_jj"]),
        ),
    )
    """Element table data."""

    def __init__(self, design: "QDesign", initiate=True, options: Dict = None):
        """Create a QRenderer for Ansys.

        Args:
            design (QDesign): Use QGeometry within QDesign to obtain elements for Ansys.
            initiate (bool, optional): True to initiate the renderer. Defaults to True.
            options (Dict, optional):  Used to override all options. Defaults to None.
        """
        # Variables to connect to Ansys
        self._rapp = None
        self._rdesktop = None

        # Initialize renderer
        super().__init__(design=design, initiate=initiate, options=options)

        # Default behavior is to render all components unless a strict subset was chosen
        self.render_everything = True

        self._pinfo = None

    @property
    def initialized(self):
        """Returns True if initialized, False otherwise."""
        if self._pinfo:
            if self._pinfo.project:
                try:
                    # this is because after previous pyEPR close(),
                    # the pinfo.project becomes None, but the type is not None (method)
                    # TODO: fix where appropriate, then remove this patch.
                    self._pinfo.project.name
                except AttributeError:
                    return False
                return True
        return False

    @property
    def rapp(self):
        return self._rapp

    @rapp.setter
    def rapp(self, app_com):
        if self._rapp:
            self._rapp.release()
        self._rapp = app_com

    @property
    def rdesktop(self):
        return self._rdesktop

    @rdesktop.setter
    def rdesktop(self, desktop_com):
        if self._rdesktop:
            self._rdesktop.release()
        self._rdesktop = desktop_com

    def _initiate_renderer(self):
        """
        Open a session of the default Ansys EDT.
        Establishes the connection to the App and Desktop only.
        """
        # test if ansys is open
        # import psutil
        # booted = False
        # for proc in psutil.process_iter():
        #     if 'ansysedt' in proc.name():
        #         booted = True

        # if not booted:
        #    self._open_ansys(*args, **kwargs)
        # need to make it so that it waits for the Ansys boot to end
        # after opening, should establish a connection (able to create a new project)

        self.rapp = HfssApp()
        self.rdesktop = self.rapp.get_app_desktop()
        if self.rdesktop.project_count() == 0:
            self.rdesktop.new_project()
        self.connect_ansys()  # TODO: can this be done differently?

        # return True to indicate successful completion
        return True

    def _close_renderer(self):
        """Not used by the gds renderer at this time. only returns True.

        Returns:
            bool: True
        """
        # wipe local variables
        self.epr_distributed_analysis = None
        self.epr_quantum_analysis = None

        # close COM connections to ansys
        if self.rdesktop is not None:
            self.rdesktop.release()
        if self.rapp is not None:
            self.rapp.release()
        if self.pinfo:
            self.disconnect_ansys()

        return True

    def close(self):
        """Alias of _close_renderer()

        Returns:
            bool: True
        """
        return self._close_renderer()

    def open_ansys(
        self,
        path: str = None,
        executable: str = "reg_ansysedt.exe",
        path_var: str = "ANSYSEM_ROOT202",
    ):
        """Alternative method to open an Ansys session that allows to specify
                which version to use. Default is version 2020 R2, but can be overridden.

        Args:
            path (str): Path to the Ansys executable. Defaults to None
            executable (str): Name of the ansys executable. Defaults to 'reg_ansysedt.exe'
            path_var (str): Name of the OS environment variable that contains the path to the
                            Ansys executable. Only used when path=None.
                            Defaults to 'ANSYSEM_ROOT202' (Ansys ver. 2020 R2)
        """
        if not system() == "Windows":
            self.logger.warning(
                "You are using %s, but this is a renderer to Ansys, which only runs on Windows. "
                "Expect any sort of Errors if you try to work with this renderer beyond this point."
                % system())

        import subprocess

        if path is None:
            try:
                path = os.environ[path_var]
            except KeyError:
                self.logger.error(
                    "environment variable %s not found. Is Ansys 2020 R2 installed on this "
                    "machine? If yes, then create said environment variable. If you have a "
                    "different version of Ansys, then pass to open_ansys() the path to its "
                    "binary, or the env var that stores it." % path_var)
                raise
        else:
            path = os.path.abspath(path)
        cmdlist = [os.path.sep.join([path, executable]), "-shortcut"]
        subprocess.call(cmdlist, cwd=path)

    def connect_ansys(
        self,
        project_path: str = None,
        project_name: str = None,
        design_name: str = None,
    ):
        """If none of the optional parameters are provided: connects to the
        Ansys COM, then checks for, and grab if present, an active project,
        design, and design setup.

        If the optional parameters are provided: if present, opens the project file and design in
        Ansys.

        Args:
            project_path (str, optional): Path without file name
            project_name (str, optional): File name (with or without extension)
            design_name (str, optional): Name of the default design to open from the project file
        """
        if not system() == "Windows":
            self.logger.warning(
                "You are using %s, but this is a renderer to Ansys, which only runs on Windows. "
                "Expect any sort of Errors if you try to work with this renderer beyond this point."
                % system())

        # pyEPR does not like extensions
        if project_name:
            project_name = project_name.replace(".aedt", "")
        # open connection through pyEPR
        import pythoncom

        try:
            self._pinfo = epr.ProjectInfo(
                do_connect=True,
                project_path=self._options["project_path"]
                if not project_path else project_path,
                project_name=self._options["project_name"]
                if not project_name else project_name,
                design_name=self._options['design_name']
                if not design_name else design_name)
        except pythoncom.com_error as error:  # pylint: disable=no-member
            print("com_error: ", error)
            hr, msg, exc, arg = error.args
            if (msg == "Invalid class string"
               ):  # and hr == -2147221005 and exc is None and arg is None
                self.logger.error(
                    "pyEPR cannot find the Ansys COM. Ansys installation might not have registered it. "
                    "To verify if this is the problem, execute the following: "
                    "`print(win32com.client.Dispatch('AnsoftHfss.HfssScriptInterface'))` "
                    "If the print-out is not `<COMObject ...>` then Ansys COM is not registered, "
                    "and you will need to look into correcting your Ansys installation."
                )
            raise error

    def disconnect_ansys(self):
        """Disconnect Ansys."""
        if self.pinfo:
            self.pinfo.disconnect()
        else:
            self.logger.warning(
                "This renderer appears to be already disconnected from Ansys")

    def new_ansys_project(self):
        """Creates a new empty project in Ansys."""
        here = HfssApp()
        here.get_app_desktop().new_project()

    def connect_ansys_design(self, design_name: str = None):
        """Used to switch between existing designs.

        Args:
            design_name (str, optional): Name within the active project. Defaults to None.
        """

        if self.pinfo:
            if self.pinfo.project:
                all_designs_names = self.pinfo.project.get_design_names()
                if design_name not in all_designs_names:
                    self.logger.warning(
                        f"The design_name={design_name} is not in project.  Connection did not happen."
                    )
                    return

                try:
                    self.pinfo.connect_design(design_name)
                    self.pinfo.connect_setup()
                except AttributeError:
                    self.logger.error(
                        "Please install a more recent version of pyEPR (>=0.8.4.3)"
                    )
            else:
                self.logger.warning(
                    "Either you do not have a project loaded in Ansys, or you are not connected "
                    "to it. Try executing hfss.connect_ansys(), or creating a new Ansys project. "
                    "Also check the help file and other guide notebooks")
        else:
            self.logger.warning(
                "It does not look like you are connected to Ansys. Please use connect_ansys() "
                "and make sure self.pinfo is set. There must be a project open in Ansys first."
            )

    def get_active_design_name(self):
        """Returns the name of the Ansys Design Object

        Returns:
            (str): Name of the active Ansys Design
        """
        if self.pinfo:
            if self.pinfo.project:
                return self.pinfo.project.get_active_design().name

    @property
    def pinfo(self) -> epr.ProjectInfo:
        """Project info for Ansys renderer (class: pyEPR.ProjectInfo)."""
        return self._pinfo

    @property
    def modeler(self):
        """The modeler from pyEPR HfssModeler.

        Returns:
            pyEPR.ansys.HfssModeler: Reference to  design.HfssModeler in Ansys.
        """
        if self.pinfo:
            if self.pinfo.design:
                return self.pinfo.design.modeler

    def plot_ansys_fields(self, *args, **kwargs):
        """
        (deprecated) use plot_fields()
        """
        self.logger.warning(
            "This method is deprecated. Change your scripts to use plot_fields()"
        )
        return self.plot_fields(*args, **kwargs)

    def plot_fields(
        self,
        object_name: str,
        name: str = None,
        UserSpecifyName: int = None,
        UserSpecifyFolder: int = None,
        QuantityName: str = None,
        PlotFolder: str = None,
        StreamlinePlot: bool = None,
        AdjacentSidePlot: bool = None,
        FullModelPlot: bool = None,
        IntrinsicVar: str = None,
        PlotGeomInfo_0: int = None,
        PlotGeomInfo_1: str = None,
        PlotGeomInfo_2: str = None,
        PlotGeomInfo_3: int = None,
    ):
        """Plot fields in Ansys. The options are populated by the component's
        options.

        Args:
            object_name (str): Used to plot on faces of.
            name (str, optional): "NAME:<PlotName>" Defaults to None.
            UserSpecifyName (int, optional): 0 if default name for plot is used, 1 otherwise.
                Defaults to None.
            UserSpecifyFolder (int, optional): 0 if default folder for plot is used, 1 otherwise.
                Defaults to None.
            QuantityName (str, optional): Type of plot to create. Possible values are
                Mesh plots - "Mesh";
                Field plots - "Mag_E", "Mag_H", "Mag_Jvol", "Mag_Jsurf","ComplexMag_E",
                "ComplexMag_H", "ComplexMag_Jvol", "ComplexMag_Jsurf", "Vector_E", "Vector_H",
                "Vector_Jvol", "Vector_Jsurf", "Vector_RealPoynting","Local_SAR", "Average_SAR".
                Defaults to None.
            PlotFolder (str, optional): Name of the folder to which the plot should be added.
                Possible values are: "E Field",  "H Field", "Jvol", "Jsurf", "SARField", and
                "MeshPlots". Defaults to None.
            StreamlinePlot (bool, optional): Passed to CreateFieldPlot. Defaults to None.
            AdjacentSidePlot (bool, optional): Passed to CreateFieldPlot. Defaults to None.
            FullModelPlot (bool, optional): Passed to CreateFieldPlot. Defaults to None.
            IntrinsicVar (str, optional): Formatted string that specifies the frequency and phase
                at which to make the plot.  For example: "Freq='1GHz' Phase='30deg'".
                Defaults to None.
            PlotGeomInfo_0 (int, optional): 0th entry in list for "PlotGeomInfo:=",
                <PlotGeomArray>. Defaults to None.
            PlotGeomInfo_1 (str, optional): 1st entry in list for "PlotGeomInfo:=",
                <PlotGeomArray>. Defaults to None.
            PlotGeomInfo_2 (str, optional): 2nd entry in list for "PlotGeomInfo:=",
                <PlotGeomArray>. Defaults to None.
            PlotGeomInfo_3 (int, optional): 3rd entry in list for "PlotGeomInfo:=",
                <PlotGeomArray>. Defaults to None.

        Returns:
            NoneType: Return information from oFieldsReport.CreateFieldPlot().
            The method CreateFieldPlot() always returns None.
        """
        self.modeler._modeler.ShowWindow()
        if not self.pinfo:
            self.logger.warning("pinfo is None.")
            return

        if self.pinfo.design:
            if not self.pinfo.design._fields_calc:
                self.logger.warning("The _fields_calc in design is None.")
                return
            if not self.pinfo.design._modeler:
                self.logger.warning("The _modeler in design is None.")
                return
        else:
            self.logger.warning("The design in pinfo is None.")
            return

        if not self.pinfo.setup:
            self.logger.warning("The setup in pinfo is None.")
            return

        # TODO: This is just a prototype - should add features and flexibility.
        oFieldsReport = (self.pinfo.design._fields_calc
                        )  # design.GetModule("FieldsReporter")
        oModeler = self.pinfo.design._modeler  # design.SetActiveEditor("3D Modeler")
        setup = self.pinfo.setup

        # Object ID - use to plot on faces of
        object_id = oModeler.GetObjectIDByName(object_name)
        # Can also use hfss.pinfo.design._modeler.GetFaceIDs("main")

        paf = self.options["plot_ansys_fields_options"]

        if not name:
            name = self.parse_value(paf["name"])

        # Name of the solution setup and solution formatted as:"<SolveSetupName> : <WhichSolution>",
        # where <WhichSolution> can be "Adaptive_<n>", "LastAdaptive", or "PortOnly".
        # HFSS requires a space on either side of the ‘:’ character.
        # If it is missing, the plot will not be created.
        SolutionName = f"{setup.name} : LastAdaptive"
        if not UserSpecifyName:
            UserSpecifyName = int(self.parse_value(paf["UserSpecifyName"]))
        if not UserSpecifyFolder:
            UserSpecifyFolder = int(self.parse_value(paf["UserSpecifyFolder"]))
        if not QuantityName:
            QuantityName = self.parse_value(paf["QuantityName"])
        if not PlotFolder:
            PlotFolder = self.parse_value(paf["PlotFolder"])
        if not StreamlinePlot:
            StreamlinePlot = is_true(self.parse_value(paf["StreamlinePlot"]))
        if not AdjacentSidePlot:
            AdjacentSidePlot = is_true(self.parse_value(
                paf["AdjacentSidePlot"]))
        if not FullModelPlot:
            FullModelPlot = is_true(self.parse_value(paf["FullModelPlot"]))
        if not IntrinsicVar:
            IntrinsicVar = self.parse_value(paf["IntrinsicVar"])
        if not PlotGeomInfo_0:
            PlotGeomInfo_0 = int(self.parse_value(paf["PlotGeomInfo_0"]))
        if not PlotGeomInfo_1:
            PlotGeomInfo_1 = self.parse_value(paf["PlotGeomInfo_1"])
        if not PlotGeomInfo_2:
            PlotGeomInfo_2 = self.parse_value(paf["PlotGeomInfo_2"])
        if not PlotGeomInfo_3:
            PlotGeomInfo_3 = int(self.parse_value(paf["PlotGeomInfo_3"]))

        # used to pass to CreateFieldPlot
        # Copied from  pdf at http://www.ece.uprm.edu/~rafaelr/inel6068/HFSS/scripting.pdf
        # <PlotGeomArray>Array(<NumGeomTypes>, <GeomTypeData>,<GeomTypeData>, ...)
        # For example:
        # Array(4, "Volume", "ObjList", 1, "Box1","Surface", "FacesList", 1, "12", "Line", 1,"Polyline1",
        #       "Point", 2, "Point1", "Point2"
        PlotGeomInfo = [
            PlotGeomInfo_0,
            PlotGeomInfo_1,
            PlotGeomInfo_2,
            PlotGeomInfo_3,
            str(object_id),
        ]

        # yapf: disable
        args_list = [
                name                 ,
                "SolutionName:="     , SolutionName,  # name of the setup
                "UserSpecifyName:="  , UserSpecifyName ,
                "UserSpecifyFolder:=", UserSpecifyFolder,
                "QuantityName:="     , QuantityName,
                "PlotFolder:="       , PlotFolder,
                "StreamlinePlot:="   , StreamlinePlot,
                "AdjacentSidePlot:=" , AdjacentSidePlot,
                "FullModelPlot:="    , FullModelPlot,
                "IntrinsicVar:="     , IntrinsicVar,
                "PlotGeomInfo:="     , PlotGeomInfo,
            ]
        # yapf: enable
        return oFieldsReport.CreateFieldPlot(args_list, "Field")

    def plot_ansys_delete(self, names: list):
        """
        (deprecated) Use clear_fields()
        """
        self.logger.warning(
            "This method is deprecated. Change your scripts to use clear_fields()"
        )
        self.clear_fields(names)

    def clear_fields(self, names: list):
        """
        Delete field plots from modeler window in Ansys.
        Does not throw an error if names are missing.

        Can give multiple names, for example:
        hfss.plot_ansys_delete(['Mag_E1', 'Mag_E1_2'])

        Args:
            names (list): Names of plots to delete from modeler window.
        """
        if not names:
            names = list(self.pinfo.design._fields_calc.GetFieldPlotNames())
        return self.pinfo.design._fields_calc.DeleteFieldPlot(names)

    def add_message(self, msg: str, severity: int = 0):
        """Add message to Message Manager box in Ansys.

        Args:
            msg (str): Message to add.
            severity (int): 0 = Informational, 1 = Warning, 2 = Error, 3 = Fatal.
        """
        self.pinfo.design.add_message(msg, severity)

    def save_screenshot(self, path: str = None, show: bool = True):
        """Save the screenshot.

        Args:
            path (str, optional): Path to save location.  Defaults to None.
            show (bool, optional): Whether or not to display the screenshot.  Defaults to True.

        Returns:
            pathlib.WindowsPath: path to png formatted screenshot.
        """
        self.modeler._modeler.ShowWindow()
        try:
            return self.pinfo.design.save_screenshot(path, show)
        except AttributeError:
            self.logger.error(
                "Please install a more recent version of pyEPR (>=0.8.4.3)")

    def execute_design(
        self,
        design_name: str,
        solution_type: str,
        vars_to_initialize: Dict,
        force_redraw: bool = False,
        **design_selection,
    ) -> str:
        """It wraps the render_design() method to
        1. skip rendering if the "selection" of components is left empty (re-uses selected design)
        2. force design clearing and redraw if force_Redraw is set

        Args:
            design_name (str): Name to assign to the renderer design
            solution_type (str): eigenmode, capacitive or drivenmodal
            vars_to_initialize (Dict): Variables to initialize, i.e. Ljx, Cjx
            force_redraw (bool, optional): Force re-render the design. Defaults to False.

        Returns:
            str: final design name (a suffix might have been added to the provided name,
                in case of conflicts)
        """
        # If a selection of components is not specified, use the active renderer-design
        if "selection" in design_selection:
            if design_selection["selection"] is None:
                try:
                    return self.pinfo.design.name
                except AttributeError:
                    # if no design exists, then we will proceed and render the full design instead
                    pass

        # either create a new one, or clear the active one, depending on force_redraw.
        if force_redraw and (design_name
                             in self.pinfo.project.get_design_names()):
            self.activate_ansys_design(design_name, solution_type)
            self.clean_active_design()
        else:
            self.new_ansys_design(design_name, solution_type)

        self.set_variables(vars_to_initialize)
        self.render_design(**design_selection)
        return self.pinfo.design.name

    def new_ansys_design(self,
                         design_name: str,
                         solution_type: str,
                         connect: bool = True):
        """Add an Ansys design with the given name to the Ansys project.
        Valid solutions_type values are: 'capacitive' (q3d), 'eignemode' and 'drivenmodal' (hfss)

        Args:
            design_name (str): name of the Design to be created in Ansys
            solution_type (str): defines type of Design and solution to be created in Ansys
            connect (bool, optional): Should we connect qiskit-metal to this Ansy design? Defaults to True.

        Returns(pyEPR.ansys.HfssDesign): The pointer to the design within Ansys.

        """
        if self.pinfo:
            try:
                if solution_type == "capacitive":
                    adesign = self.pinfo.project.new_q3d_design(design_name)
                elif solution_type == "eigenmode":
                    adesign = self.pinfo.project.new_em_design(design_name)
                elif solution_type == "drivenmodal":
                    adesign = self.pinfo.project.new_dm_design(design_name)
                else:
                    self.logger.error(
                        f"The solution_type = {solution_type} is not supported by this renderer"
                    )
            except AttributeError:
                if self.pinfo.project is None:
                    self.logger.error("Project not found")
                else:
                    self.logger.error(
                        "Please install a more recent version of pyEPR (>=0.8.4.4)"
                    )
                raise
            if connect:
                self.connect_ansys_design(adesign.name)
            return adesign
        else:
            self.logger.info(
                "You have to first connect to Ansys and to a project "
                "before creating a new design. You can use renderer.connect_ansys()"
            )

    def activate_ansys_design(self,
                              design_name: str,
                              solution_type: str = None):
        """Select a design with the given name from the open project.
        If the design exists, that will be added WITHOUT altering the suffix of the design name.

        Args:
            name (str): Name of the new Ansys design
        """

        if self.pinfo:
            if self.pinfo.project:
                try:
                    names_in_design = self.pinfo.project.get_design_names()
                except AttributeError:
                    self.logger.error(
                        "Please install a more recent version of pyEPR (>=0.8.4.5)"
                    )

                if design_name in names_in_design:
                    self.pinfo.connect_design(design_name)
                    oDesktop = (self.pinfo.design.parent.parent._desktop
                               )  # self.pinfo.design does not work
                    oProject = oDesktop.SetActiveProject(
                        self.pinfo.project_name)
                    oDesign = oProject.SetActiveDesign(design_name)
                    current_solution_type = self.pinfo.design.solution_type.lower(
                    )
                    if current_solution_type == "q3d":
                        current_solution_type = "capacitive"
                    if (current_solution_type != solution_type and
                            solution_type is not None):
                        self.logger.warning(
                            f"The design_name={design_name} already exists, but it has solution_type=="
                            f"{current_solution_type}, which is different from the requested=={solution_type}. "
                            f"If you want a design with solution type=={solution_type}, please change the name "
                            "requested for your design to one that does not exist. Alternatively, manually modify "
                            f"the solution_type for design {design_name} from the Ansys GUI."
                        )
                else:
                    self.logger.warning(
                        f"The design_name={design_name} was not in active project.  "
                        f"Designs in active project are: \n{names_in_design}.  "
                        "A new design will be added to the project.  ")
                    if solution_type is not None:
                        adesign = self.new_ansys_design(
                            design_name=design_name,
                            solution_type=solution_type,
                            connect=True,
                        )
                    else:
                        self.logger.error(
                            "Please specify the solution_type, to determine what design to create"
                        )
            else:
                self.logger.warning(
                    "Project not found, have you opened a project?")
        else:
            self.logger.warning(
                "Have you run start()?  Cannot find a reference to Ansys in QRenderer."
            )

    def new_ansys_setup(self, name: str, **other_setup):
        """Determines the appropriate setup to be created based on the pinfo.design.solution_type.
        make sure to set this variable before executing this method

        Args:
            name (str): name to give to the new setup

        Returns:
            pyEPR.ansys.HfssEMSetup: Pointer to the ansys setup object
        """
        # TODO: only use activate_ansys_setup?
        if self.pinfo:
            if self.pinfo.design:
                if "reuse_setup" in other_setup:
                    if other_setup["reuse_setup"]:
                        # delete_setup will check if setup exists, before deleting.
                        self.pinfo.design.delete_setup(name)

                if self.pinfo.design.solution_type == "Eigenmode":
                    setup = self.add_eigenmode_setup(name, **other_setup)
                elif self.pinfo.design.solution_type == "DrivenModal":
                    setup = self.add_drivenmodal_setup(name, **other_setup)
                elif self.pinfo.design.solution_type == "Q3D":
                    setup = self.add_q3d_setup(name, **other_setup)
        return setup

    def initialize_cap_extract(self, **kwargs):
        """Any task that needs to occur before running a simulation, such as creating a setup

        Returns:
            str: Name of the setup that has been updated
        """

        setup = self.new_ansys_setup(**kwargs)  # TODO: activate_ansys_setup?
        return setup.name

    def initialize_eigenmode(self, vars: Dict = {}, **kwargs):
        """Any task that needs to occur before running a simulation, such as creating a setup

        Args:
            vars (Dict, optional): list of parametric variables to set in the renderer.
                Defaults to {}.

        Returns:
            str: Name of the setup that has been updated
        """
        self.set_variables(vars)
        setup = self.new_ansys_setup(**kwargs)  # TODO: activate_ansys_setup?
        return setup.name

    def initialize_drivenmodal(self,
                               sweep_setup: Dict,
                               vars: Dict = {},
                               **kwargs):
        """Any task that needs to occur before running a simulation, such as creating a setup

        Args:
            sweep_setup (Dict): list of parametric variables to set the frequency sweep.
            vars (Dict, optional): list of parametric variables to set in the renderer.
                Defaults to {}.

        Returns:
            str: Name of the setup that has been updated
        """
        self.set_variables(vars)
        setup = self.new_ansys_setup(**kwargs)  # TODO: activate_ansys_setup?
        sweep = self.add_sweep(setup.name, **sweep_setup)
        return setup.name, sweep.name

    def activate_ansys_setup(self, setup_name: str):
        """For active design, either get existing setup, make new setup with name,
        or make new setup with default name.

        Args:
            setup_name (str, optional): If name exists for setup, then have pinfo reference it.
              If name for setup does not exist, create a new setup with the name.
              If name is None, create a new setup with default name.
        """
        if self.pinfo:
            if self.pinfo.project:
                if self.pinfo.design:
                    # look for setup name, if not there, then add a new one
                    if setup_name:
                        all_setup_names = self.pinfo.design.get_setup_names()
                        self.pinfo.setup_name = setup_name
                        if setup_name in all_setup_names:
                            # When name is given and in design. So have pinfo reference existing setup.
                            self.pinfo.setup = self.pinfo.get_setup(setup_name)
                        else:
                            # When name is given, but not in design. So make a new setup with given name.
                            self.logger.warning(
                                f"The setup_name={setup_name} was not in active design.  "
                                f"Setups in active design are: \n{all_setup_names}.  "
                                "A new setup will default values will be added to the design.  "
                            )
                            self.pinfo.setup = self.new_ansys_setup(
                                name=setup_name)
                    else:
                        self.logger.warning(f"Please specify a setup_name.")
                else:
                    self.logger.warning(
                        "Design not found in selected project, have you opened a design?"
                    )
            else:
                self.logger.warning(
                    "Project not found, have you opened a project?")
        else:
            self.logger.warning(
                "Have you run connect_ansys()?  Cannot find a reference to Ansys in QRenderer."
            )

    def render_design(
        self,
        selection: Union[list, None] = None,
        open_pins: Union[list, None] = None,
        box_plus_buffer: bool = True,
    ):
        """Initiate rendering of components in design contained in selection,
        assuming they're valid. Components are rendered before the chips they
        reside on, and subtraction of negative shapes is performed at the very
        end.

        First obtain a list of IDs of components to render and a corresponding case, denoted by self.qcomp_ids
        and self.case, respectively. If self.case == 1, all components in QDesign are to be rendered.
        If self.case == 0, a strict subset of components in QDesign are to be rendered. Otherwise, if
        self.case == 2, one or more component names in selection cannot be found in QDesign.

        Chip_subtract_dict consists of component names (keys) and a set of all elements within each component that
        will eventually be subtracted from the ground plane. Add objects that are perfect conductors and/or have
        meshing to self.assign_perfE and self.assign_mesh, respectively; both are initialized as empty lists. Similarly,
        if the object is a port in an eigenmode simulation, add it to self.assign_port_mesh, which is initialized
        as an empty list. Note that these objects are "refreshed" each time render_design is called (as opposed to
        in the init function) to clear QAnsysRenderer of any leftover items from the last call to render_design.

        Among the components selected for export, there may or may not be unused (unconnected) pins.
        The second parameter, open_pins, contains tuples of the form (component_name, pin_name) that
        specify exactly which pins should be open rather than shorted during the simulation. Both the
        component and pin name must be specified because the latter could be shared by multiple
        components. All pins in this list are rendered with an additional endcap in the form of a
        rectangular cutout, to be subtracted from its respective plane.

        The final parameter, box_plus_buffer, determines how the chip is drawn. When set to True, it takes the
        minimum rectangular bounding box of all rendered components and adds a buffer of x_buffer_width_mm and
        y_buffer_width_mm horizontally and vertically, respectively, to the chip size. The center of the chip
        lies at the midpoint x/y coordinates of the minimum rectangular bounding box and may change depending
        on which components are rendered and how they're positioned. If box_plus_buffer is False, however, the
        chip position and dimensions are taken from the chip info dictionary found in QDesign, irrespective
        of what's being rendered. While this latter option is faster because it doesn't require calculating a
        bounding box, it runs the risk of rendered components being too close to the edge of the chip or even
        falling outside its boundaries.

        Args:
            selection (Union[list, None], optional): List of components to render. Defaults to None.
            open_pins (Union[list, None], optional): List of tuples of pins that are open. Defaults to None.
            box_plus_buffer (bool): Either calculate a bounding box based on the location of rendered geometries
                                     or use chip size from design class.
        """
        self.qcomp_ids, self.case = self.get_unique_component_ids(selection)

        if self.case == 2:
            self.logger.warning(
                "Unable to proceed with rendering. Please check selection.")
            return

        self.chip_subtract_dict = defaultdict(set)
        self.assign_perfE = []
        self.assign_mesh = []

        self.render_tables()
        self.add_endcaps(open_pins)

        self.render_chips(box_plus_buffer=box_plus_buffer)
        self.subtract_from_ground()
        self.add_mesh()

    def render_chip(self):
        pass

    def render_component(self):
        pass

    def render_tables(self, skip_junction: bool = False):
        """
        Render components in design grouped by table type (path, poly, or junction).
        """
        for table_type in self.design.qgeometry.get_element_types():
            if table_type != "junction" or not skip_junction:
                self.render_components(table_type)

    def render_components(self, table_type: str):
        """
        Render components by breaking them down into individual elements.

        Args:
            table_type (str): Table type (poly, path, or junction).
        """
        table = self.design.qgeometry.tables[table_type]

        if self.case == 0:  # Render a subset of components using mask
            mask = table["component"].isin(self.qcomp_ids)
            table = table[mask]

        for _, qgeom in table.iterrows():
            self.render_element(qgeom, bool(table_type == "junction"))

        if table_type == "path":
            self.auto_wirebonds(table)

    def render_element(self, qgeom: pd.Series, is_junction: bool):
        """Render an individual shape whose properties are listed in a row of
        QGeometry table. Junction elements are handled separately from non-
        junction elements, as the former consist of two rendered shapes, not
        just one.

        Args:
            qgeom (pd.Series): GeoSeries of element properties.
            is_junction (bool): Whether or not qgeom belongs to junction table.
        """
        qc_shapely = qgeom.geometry
        if is_junction:
            self.render_element_junction(qgeom)
        else:
            if isinstance(qc_shapely, shapely.geometry.Polygon):
                self.render_element_poly(qgeom)
            elif isinstance(qc_shapely, shapely.geometry.LineString):
                self.render_element_path(qgeom)

    def render_element_junction(self, qgeom: pd.Series):
        """
        Render a Josephson junction consisting of
            1. A rectangle of length pad_gap and width inductor_width. Defines lumped element
               RLC boundary condition.
            2. A line that is later used to calculate the voltage in post-processing analysis.

        Args:
            qgeom (pd.Series): GeoSeries of element properties.
        """
        ansys_options = dict(transparency=0.0)

        qc_name = "Lj_" + str(qgeom["component"])
        qc_elt = get_clean_name(qgeom["name"])
        qc_shapely = qgeom.geometry
        qc_chip_z = parse_units(self.design.get_chip_z(qgeom.chip))
        qc_width = parse_units(qgeom.width)

        name = f"{qc_name}{QAnsysRenderer.NAME_DELIM}{qc_elt}"

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

        # Draw rectangle
        self.logger.debug(f"Drawing a rectangle: {name}")
        poly_ansys = self.modeler.draw_rect_corner(
            [x_min, y_min, qc_chip_z],
            x_max - x_min,
            y_max - y_min,
            qc_chip_z,
            **ansys_options,
        )
        axis = "x" if abs(x1 - x0) > abs(y1 - y0) else "y"
        self.modeler.rename_obj(poly_ansys, "JJ_rect_" + name)
        self.assign_mesh.append("JJ_rect_" + name)

        # Draw line
        poly_jj = self.modeler.draw_polyline(
            [endpoints_3d[0], endpoints_3d[1]],
            closed=False,
            **dict(color=(128, 0, 128)),
        )
        poly_jj = poly_jj.rename("JJ_" + name + "_")
        poly_jj.show_direction = True

    def render_element_poly(self, qgeom: pd.Series):
        """Render a closed polygon.

        Args:
            qgeom (pd.Series): GeoSeries of element properties.
        """
        ansys_options = dict(transparency=0.0)

        qc_name = self.design._components[qgeom["component"]].name
        qc_elt = get_clean_name(qgeom["name"])

        qc_shapely = qgeom.geometry  # shapely geom
        qc_chip_z = parse_units(self.design.get_chip_z(qgeom.chip))
        qc_fillet = round(qgeom.fillet, 7)

        name = f"{qc_elt}{QAnsysRenderer.NAME_DELIM}{qc_name}"

        points = parse_units(list(
            qc_shapely.exterior.coords))  # list of 2d point tuples
        points_3d = to_vec3D(points, qc_chip_z)

        if is_rectangle(qc_shapely):  # Draw as rectangle
            self.logger.debug(f"Drawing a rectangle: {name}")
            x_min, y_min, x_max, y_max = qc_shapely.bounds
            poly_ansys = self.modeler.draw_rect_corner(
                *parse_units([
                    [x_min, y_min,
                     self.design.get_chip_z(qgeom.chip)],
                    x_max - x_min,
                    y_max - y_min,
                    0,
                ]),
                **ansys_options,
            )
            self.modeler.rename_obj(poly_ansys, name)

        else:
            # Draw general closed poly
            poly_ansys = self.modeler.draw_polyline(points_3d[:-1],
                                                    closed=True,
                                                    **ansys_options)
            # rename: handle bug if the name of the cut already exits and is used to make a cut
            poly_ansys = poly_ansys.rename(name)

        qc_fillet = round(qgeom.fillet, 7)
        if qc_fillet > 0:
            qc_fillet = parse_units(qc_fillet)
            idxs_to_fillet = good_fillet_idxs(
                points,
                qc_fillet,
                precision=self.design._template_options.PRECISION,
                isclosed=True,
            )
            if idxs_to_fillet:
                self.modeler._fillet(qc_fillet, idxs_to_fillet, poly_ansys)

        # Subtract interior shapes, if any
        if len(qc_shapely.interiors) > 0:
            for i, x in enumerate(qc_shapely.interiors):
                interior_points_3d = to_vec3D(parse_units(list(x.coords)),
                                              qc_chip_z)
                inner_shape = self.modeler.draw_polyline(
                    interior_points_3d[:-1], closed=True)
                self.modeler.subtract(name, [inner_shape])

        # Input chip info into self.chip_subtract_dict
        if qgeom.chip not in self.chip_subtract_dict:
            self.chip_subtract_dict[qgeom.chip] = set()

        if qgeom["subtract"]:
            self.chip_subtract_dict[qgeom.chip].add(name)

        # Potentially add to list of elements to metallize
        elif not qgeom["helper"]:
            self.assign_perfE.append(name)

    def render_element_path(self, qgeom: pd.Series):
        """Render a path-type element.

        Args:
            qgeom (pd.Series): GeoSeries of element properties.
        """
        ansys_options = dict(transparency=0.0)

        qc_name = self.design._components[qgeom["component"]].name
        qc_elt = get_clean_name(qgeom["name"])

        qc_shapely = qgeom.geometry  # shapely geom
        qc_chip_z = parse_units(self.design.get_chip_z(qgeom.chip))

        name = f"{qc_elt}{QAnsysRenderer.NAME_DELIM}{qc_name}"

        qc_width = parse_units(qgeom.width)

        points = parse_units(list(qc_shapely.coords))
        points_3d = to_vec3D(points, qc_chip_z)

        try:
            poly_ansys = self.modeler.draw_polyline(points_3d,
                                                    closed=False,
                                                    **ansys_options)
        except AttributeError:
            if self.modeler is None:
                self.logger.error(
                    "No modeler was found. Are you connected to an active Ansys Design?"
                )
            raise

        poly_ansys = poly_ansys.rename(name)

        qc_fillet = round(qgeom.fillet, 7)
        if qc_fillet > 0:
            qc_fillet = parse_units(qc_fillet)
            idxs_to_fillet = good_fillet_idxs(
                points,
                qc_fillet,
                precision=self.design._template_options.PRECISION,
                isclosed=False,
            )
            if idxs_to_fillet:
                self.modeler._fillet(qc_fillet, idxs_to_fillet, poly_ansys)

        if qc_width:
            x0, y0 = points[0]
            x1, y1 = points[1]
            vlen = math.sqrt((x1 - x0)**2 + (y1 - y0)**2)
            p0 = np.array([
                x0, y0, qc_chip_z
            ]) + qc_width / (2 * vlen) * np.array([y0 - y1, x1 - x0, 0])
            p1 = np.array([
                x0, y0, qc_chip_z
            ]) + qc_width / (2 * vlen) * np.array([y1 - y0, x0 - x1, 0])
            shortline = self.modeler.draw_polyline([p0, p1],
                                                   closed=False)  # sweepline
            import pythoncom

            try:
                self.modeler._sweep_along_path(shortline, poly_ansys)
            except pythoncom.com_error as error:
                print("com_error: ", error)
                hr, msg, exc, arg = error.args
                if msg == "Exception occurred." and hr == -2147352567:
                    self.logger.error(
                        "We cannot find a writable design. \n  Either you are trying to use a Ansys "
                        "design that is not empty, in which case please clear it manually or with the "
                        "renderer method clean_active_design(). \n  Or you accidentally deleted "
                        "the design in Ansys, in which case please create a new one."
                    )
                raise error

        if qgeom.chip not in self.chip_subtract_dict:
            self.chip_subtract_dict[qgeom.chip] = set()

        if qgeom["subtract"]:
            self.chip_subtract_dict[qgeom.chip].add(name)

        elif qgeom["width"] and (not qgeom["helper"]):
            self.assign_perfE.append(name)

    def add_endcaps(self, open_pins: Union[list, None] = None):
        """Create endcaps (rectangular cutouts) for all pins in the list
        open_pins and add them to chip_subtract_dict. Each element in open_pins
        takes on the form (component_name, pin_name) and corresponds to a
        single pin.

        Args:
            open_pins (Union[list, None], optional): List of tuples of pins that are open. Defaults to None.
        """
        open_pins = open_pins if open_pins else []

        for comp, pin in open_pins:
            pin_dict = self.design.components[comp].pins[pin]
            width, gap = parse_units([pin_dict["width"], pin_dict["gap"]])
            mid, normal = parse_units(pin_dict["middle"]), pin_dict["normal"]
            chip_name = self.design.components[comp].options.chip
            qc_chip_z = parse_units(self.design.get_chip_z(chip_name))
            rect_mid = np.append(mid + normal * gap / 2, [qc_chip_z])
            # Assumption: pins only point in x or y directions
            # If this assumption is not satisfied, draw_rect_center no longer works -> must use draw_polyline
            endcap_name = f"endcap_{comp}_{pin}"
            if abs(normal[0]) > abs(normal[1]):
                self.modeler.draw_rect_center(rect_mid,
                                              x_size=gap,
                                              y_size=width + 2 * gap,
                                              name=endcap_name)
            else:
                self.modeler.draw_rect_center(rect_mid,
                                              x_size=width + 2 * gap,
                                              y_size=gap,
                                              name=endcap_name)
            self.chip_subtract_dict[pin_dict["chip"]].add(endcap_name)

    def get_chip_names(self) -> List[str]:
        """
        Obtain a list of chips on which the selection of components, if valid, resides.

        Returns:
            List[str]: Chips to render.
        """
        if self.case == 2:  # One or more components not in QDesign.
            self.logger.warning("One or more components not found.")
            return []
        chip_names = set()
        if self.case == 1:  # All components rendered.
            comps = self.design.components
            for qcomp in comps:
                if "chip" not in comps[qcomp].options:
                    self.chip_designation_error()
                    return []
                # elif comps[qcomp].options.chip != 'main':
                #    self.chip_not_main()
                #    return []
                chip_names.add(comps[qcomp].options.chip)
        else:  # Strict subset rendered.
            icomps = self.design._components
            for qcomp_id in self.qcomp_ids:
                if "chip" not in icomps[qcomp_id].options:
                    self.chip_designation_error()
                    return []
                # elif icomps[qcomp_id].options.chip != 'main':
                #    self.chip_not_main()
                #    return []
                chip_names.add(icomps[qcomp_id].options.chip)

        for unique_name in chip_names:
            if unique_name not in self.design.chips:
                self.chip_not_in_design_error(unique_name)

        return list(chip_names)

    def chip_designation_error(self):
        """
        Warning message that appears when the Ansys renderer fails to locate a component's chip designation.
        Provides instructions for a temporary workaround until the layer stack is finalized.
        """
        self.logger.warning(
            "This component currently lacks a chip designation. Please add chip='main' to the component's default_options dictionary, restart the kernel, and try again."
        )

    def chip_not_in_design_error(self, missing_chip: str):
        """
        Warning message that appears when the Ansys renderer fails to locate a component's chip designation in DesignPlanar (or any child of QDesign).
        Provides instructions for a temporary workaround until the layer stack is finalized.
        """
        self.logger.warning(
            f'This component currently lacks a chip designation in DesignPlanar, or any child of QDesign. '
            f'Please add dict for chip=\'{missing_chip}\' in DesignPlanar, or child of QDesign. Then restart the kernel, and try again.'
        )

    def chip_not_main(self):
        """
        Warning message that appears when a component's chip designation is not 'main'.
        As of 05/10/21, all chip designations should be 'main' until the layer stack is finalized.
        Provides instructions for a temporary workaround until the layer stack is finalized.
        """
        self.logger.warning(
            "The chip designation for this component is not 'main'. Please set chip='main' in its default_options dictionary, restart the kernel, and try again."
        )

    def get_min_bounding_box(self) -> Tuple[float]:
        """
        Determine the max/min x/y coordinates of the smallest rectangular, axis-aligned
        bounding box that will enclose a selection of components to render, given by
        self.qcomp_ids. This method is only used when box_plus_buffer is True.

        Returns:
            Tuple[float]: min x, min y, max x, and max y coordinates of bounding box.
        """
        min_x_main = min_y_main = float("inf")
        max_x_main = max_y_main = float("-inf")
        if self.case == 2:  # One or more components not in QDesign.
            self.logger.warning("One or more components not found.")
        elif self.case == 1:  # All components rendered.
            for qcomp in self.design.components:
                min_x, min_y, max_x, max_y = self.design.components[
                    qcomp].qgeometry_bounds()
                min_x_main = min(min_x, min_x_main)
                min_y_main = min(min_y, min_y_main)
                max_x_main = max(max_x, max_x_main)
                max_y_main = max(max_y, max_y_main)
        else:  # Strict subset rendered.
            for qcomp_id in self.qcomp_ids:
                min_x, min_y, max_x, max_y = self.design._components[
                    qcomp_id].qgeometry_bounds()
                min_x_main = min(min_x, min_x_main)
                min_y_main = min(min_y, min_y_main)
                max_x_main = max(max_x, max_x_main)
                max_y_main = max(max_y, max_y_main)
        return min_x_main, min_y_main, max_x_main, max_y_main

    def render_chips(self,
                     draw_sample_holder: bool = True,
                     box_plus_buffer: bool = True):
        """
        Render all chips containing components in self.qcomp_ids.

        Args:
            draw_sample_holder (bool, optional): Option to draw vacuum box around chip. Defaults to True.
            box_plus_buffer (bool, optional): Whether or not to use a box plus buffer. Defaults to True.
        """
        chip_list = self.get_chip_names()
        # added this quick hack for the case of flipchip device.
        # current self.get_chip_names only renders chips whose components are to be rendered.
        # so if you happen to only draw a qubit only, then the other chip (C_chip) does not get rendered because get_chip_names only returns Q_chip
        # I hope this gets a prettier fix in the future
        if self.design._metadata.design_name == 'FlipChip_Device':
            chip_list = self.design.chips.keys()
        self.cw_x, self.cw_y = Dict(), Dict()
        self.cc_x, self.cc_y = Dict(), Dict()

        for chip_name in chip_list:
            if box_plus_buffer:  # Get bounding box of components first
                min_x_main, min_y_main, max_x_main, max_y_main = parse_units(
                    self.get_min_bounding_box())
                self.cw_x.update({chip_name: max_x_main - min_x_main
                                 })  # chip width along x
                self.cw_y.update({chip_name: max_y_main - min_y_main
                                 })  # chip width along y
                self.cw_x[chip_name] += 2 * parse_units(
                    self._options["x_buffer_width_mm"])
                self.cw_y[chip_name] += 2 * parse_units(
                    self._options["y_buffer_width_mm"])
                self.cc_x.update({chip_name:
                    (max_x_main + min_x_main) / 2})  # x coord of chip center
                self.cc_y.update({chip_name:
                    (max_y_main + min_y_main) / 2})  # y coord of chip center
            else:  # Adhere to chip placement and dimensions in QDesign
                p = self.design.get_chip_size(
                    chip_name)  # x/y center/width same for all chips
                self.cw_x.update({chip_name: parse_units(p["size_x"])})
                self.cw_y.update({chip_name: parse_units(p["size_y"])})
                self.cc_x.update({chip_name: parse_units(p["center_x"])})
                self.cc_y.update({chip_name: parse_units(p["center_y"])})
                # self.cw_x, self.cw_y, _ = parse_units(
                #    [p['size_x'], p['size_y'], p['size_z']])
                # self.cc_x, self.cc_y, _ = parse_units(
                #    [p['center_x'], p['center_y'], p['center_z']])
            self.render_chip(chip_name, draw_sample_holder)

        if draw_sample_holder:  # HFSS
            if "sample_holder_top" in self.design.variables.keys():
                p = self.design.variables
            else:
                p = self.design.get_chip_size(chip_list[0])
            vac_height = parse_units(
                [p["sample_holder_top"], p["sample_holder_bottom"]])
            # very simple algorithm to build the vacuum box. It could be made better in the future
            # assuming that both
            cc_x = np.array([item for item in self.cc_x.values()])
            cc_y = np.array([item for item in self.cc_y.values()])
            cw_x = np.array([item for item in self.cw_x.values()])
            cw_y = np.array([item for item in self.cw_y.values()])

            cc_x_left, cc_x_right = np.min(cc_x - cw_x / 2), np.max(cc_x +
                                                                    cw_x / 2)
            cc_y_left, cc_y_right = np.min(cc_y - cw_y / 2), np.max(cc_y +
                                                                    cw_y / 2)

            cc_x = (cc_x_left + cc_x_right) / 2
            cc_y = (cc_y_left + cc_y_right) / 2
            cw_x = cc_x_right - cc_x_left
            cw_y = cc_y_right - cc_y_left

            vacuum_box = self.modeler.draw_box_center(
                [cc_x, cc_y, (vac_height[0] - vac_height[1]) / 2],
                [cw_x, cw_y, sum(vac_height)],
                name="sample_holder",
            )

    def render_chip(self, chip_name: str, draw_sample_holder: bool):
        """
        Render individual chips.

        Args:
            chip_name (str): Name of chip.
            draw_sample_holder (bool): Option to draw vacuum box around chip.
        """
        ansys_options = dict(transparency=0.0)
        ops = self.design._chips[chip_name]
        p = self.design.get_chip_size(chip_name)
        z_coord, height = parse_units([p["center_z"], p["size_z"]])
        plane = self.modeler.draw_rect_center(
            [self.cc_x[chip_name], self.cc_y[chip_name], z_coord],
            x_size=self.cw_x[chip_name],
            y_size=self.cw_y[chip_name],
            z_size=0,
            name=f"ground_{chip_name}_plane",
            **ansys_options,
        )
        whole_chip = self.modeler.draw_box_center(
            [self.cc_x[chip_name], self.cc_y[chip_name], z_coord + height / 2],
            [self.cw_x[chip_name], self.cw_y[chip_name], -height],
            name=chip_name,
            material=ops["material"],
            color=(186, 186, 205),
            transparency=0.2,
            wireframe=False,
        )
        if self.chip_subtract_dict[chip_name]:
            # Any layer which has subtract=True qgeometries will have a ground plane
            # TODO: Material property assignment may become layer-dependent.
            self.assign_perfE.append(f"ground_{chip_name}_plane")

    def subtract_from_ground(self):
        """For each chip, subtract all "negative" shapes residing on its
        surface if any such shapes exist."""
        for chip, shapes in self.chip_subtract_dict.items():
            if shapes:
                import pythoncom

                try:
                    self.modeler.subtract(f"ground_{chip}_plane", list(shapes))
                except pythoncom.com_error as error:
                    print("com_error: ", error)
                    hr, msg, exc, arg = error.args
                    if msg == "Exception occurred." and hr == -2147352567:
                        self.logger.error(
                            "This error might indicate that a component was not correctly rendered in Ansys. \n"
                            "This might have been caused by floating point numerical corrections. \n For example "
                            "Ansys will inconsistently render (or not) routing that has 180deg jogs with the two "
                            "adjacent segments spaced 'exactly' twice the fillet radius (U shaped routing). \n"
                            "In this example, changing your fillet radius to a smaller number would solve the issue."
                        )
                    raise error

    def add_mesh(self):
        """Add mesh to all elements in self.assign_mesh."""
        if self.assign_mesh:
            self.modeler.mesh_length(
                "small_mesh",
                self.assign_mesh,
                MaxLength=self._options["max_mesh_length_jj"],
            )

        try:
            exists_port_mesh = (len(self.assign_port_mesh) > 0)
        except:
            exists_port_mesh = False

        if exists_port_mesh:
            self.modeler.mesh_length(
                'port_mesh',
                self.assign_port_mesh,
                MaxLength=self._options['max_mesh_length_port'])

    # Still implementing
    def auto_wirebonds(self, table):
        """
        Adds wirebonds to the Ansys model for path elements where;
        subtract = True and wire_bonds = True.

        Uses render options for determining of the:
        * wb_threshold -- the minimum distance between two vertices of a path for a
        wirebond to be added.
        * wb_offset -- offset distance for wirebond placement (along the direction
        of the cpw)
        * wb_size -- controls the width of the wirebond (wb_size * path['width'])
        """
        norm_z = np.array([0, 0, 1])

        wb_threshold = parse_units(self._options["wb_threshold"])
        wb_offset = parse_units(self._options["wb_offset"])

        # selecting only the qgeometry which meet criteria
        wb_table = table.loc[table["hfss_wire_bonds"] == True]
        wb_table2 = wb_table.loc[wb_table["subtract"] == True]

        # looping through each qgeometry
        for _, row in wb_table2.iterrows():
            geom = row["geometry"]
            width = row["width"]
            # looping through the linestring of the path to determine where WBs should be
            for index, i_p in enumerate(geom.coords[:-1], start=0):
                j_p = np.asarray(geom.coords[:][index + 1])
                vert_distance = parse_units(distance.euclidean(i_p, j_p))
                if vert_distance > wb_threshold:
                    # Gets number of wirebonds to fit in section of path
                    wb_count = int(vert_distance // wb_threshold)
                    # finds the position vector
                    wb_pos = (j_p - i_p) / (wb_count + 1)
                    # gets the norm vector for finding the orthonormal of path
                    wb_vec = wb_pos / np.linalg.norm(wb_pos)
                    # finds the orthonormal (for orientation)
                    wb_perp = np.cross(norm_z, wb_vec)[:2]
                    # finds the first wirebond to place (rest are in the loop)
                    wb_pos_step = parse_units(wb_pos + i_p) + (wb_vec *
                                                               wb_offset)
                    # Other input values could be modified, kept to minimal selection for automation
                    # for the time being. Loops to place N wirebonds based on length of path section.
                    for wb_i in range(wb_count):
                        self.modeler.draw_wirebond(
                            pos=wb_pos_step + parse_units(wb_pos * wb_i),
                            ori=wb_perp,
                            width=parse_units(width * self._options["wb_size"]),
                            height=parse_units(width *
                                               self._options["wb_size"]),
                            z=0,
                            wire_diameter="0.015mm",
                            NumSides=6,
                            name="g_wb",
                            material="pec",
                            solve_inside=False,
                        )

    def clean_active_design(self):
        """Remove all elements from Ansys Modeler."""
        if self.pinfo:
            if self.pinfo.get_all_object_names():
                project_name = self.pinfo.project_name
                design_name = self.pinfo.design_name
                select_all = ",".join(self.pinfo.get_all_object_names())

                # self.pinfo.design does not work, thus the following line
                oDesktop = self.pinfo.design.parent.parent._desktop
                oProject = oDesktop.SetActiveProject(project_name)
                oDesign = oProject.SetActiveDesign(design_name)

                # The available editors: "Layout", "3D Modeler", "SchematicEditor"
                oEditor = oDesign.SetActiveEditor("3D Modeler")

                oEditor.Delete(["NAME:Selections", "Selections:=", select_all])

    def set_variables(self, variables: Dict):
        """Fixes the junction properties before setup. This is necessary becasue the eigenmode
        analysis only considers the junction as a lumped CL element.

        Args:
            variables (Dict): dictionary of variables to set in Ansys. For example it could
                contain 'Lj': '10 nH'
        """
        if self.pinfo:
            if self.pinfo.design:
                for k, v in variables.items():
                    self.pinfo.design.set_variable(k, v)
            else:
                self.logger.warning(
                    "Please create a design before setting variables, otherwise all variables will be set to 0 during rendering by default."
                )

    # TODO: epr methods below should not be in the renderer, but in the analysis files.
    #  Thus needs to remove the dependency from pinfo, which is Ansys-specific.

    def epr_start(self, junctions: dict = None, dissipatives: dict = None):
        """Use to initialize the epr analysis package by first identifying which are the junctions,
        their electrical properties and their reference plane; then initialize the
        DistributedAnalysis package, which can execute microwave analysis on eigenmode results.

        Args:
            junctions (dict, optional): Each element of this dictionary describes one junction.
                Defaults to dict().
            dissipatives (dict, optional): Each element of this dictionary describes one dissipative.
                Defaults to dict().
        """
        if self.pinfo:
            if junctions:
                for k, v in junctions.items():
                    self.pinfo.junctions[k] = v
                # Check that valid names of variables and objects have been supplied
                self.pinfo.validate_junction_info()
            if dissipatives:
                for k, v in dissipatives.items():
                    self.pinfo.dissipative[k] = v

            # Class handling microwave analysis on eigenmode solutions
            self.epr_distributed_analysis = epr.DistributedAnalysis(self.pinfo)

    def epr_get_stored_energy(self,
                              junctions: dict = None,
                              dissipatives: dict = None):
        """Computes the energy stored in the system
        pinfo must have a valid list of junctions and dissipatives to compute the energy stored
        in the system. So please provide them here, or using epr_start()

        Args:
            junctions (dict, optional): Each element of this dictionary describes one junction.
                Defaults to dict().
            dissipatives (dict, optional): Each element of this dictionary describes one dissipative.
                Defaults to dict().

        Returns:
            (float, float, float): energy_elec, energy_elec_substrate, energy_mag
        """
        if junctions is not None or dissipatives is not None:
            self.epr_start(junctions, dissipatives)
        elif self.epr_distributed_analysis is None:
            self.epr_start()

        if self.pinfo.dissipative["dielectrics_bulk"] is not None:
            eprd = self.epr_distributed_analysis
            energy_elec = eprd.calc_energy_electric()
            energy_elec_substrate = eprd.calc_energy_electric(
                None, self.pinfo.dissipative["dielectrics_bulk"][0])
            energy_mag = eprd.calc_energy_magnetic()

            return energy_elec, energy_elec_substrate, energy_mag
        self.logger.error("dielectrics_bulk needs to be defined")

    def epr_run_analysis(self,
                         junctions: dict = None,
                         dissipatives: dict = None):
        """Executes the EPR analysis
        pinfo must have a valid list of junctions and dissipatives to compute the energy stored
        in the system. So please provide them here, or using epr_start()

        Args:
            junctions (dict, optional): Each element of this dictionary describes one junction.
                Defaults to dict().
            dissipatives (dict, optional): Each element of this dictionary describes one dissipative.
                Defaults to dict().
        """
        if junctions is not None or dissipatives is not None:
            self.epr_start(junctions, dissipatives)
        self.epr_distributed_analysis.do_EPR_analysis()

    def epr_spectrum_analysis(self, cos_trunc: int = 8, fock_trunc: int = 7):
        """Core epr analysis method.

        Args:
            cos_trunc (int, optional): truncation of the cosine. Defaults to 8.
            fock_trunc (int, optional): truncation of the fock. Defaults to 7.
        """
        self.epr_quantum_analysis = epr.QuantumAnalysis(
            self.epr_distributed_analysis.data_filename)
        self.epr_quantum_analysis.analyze_all_variations(cos_trunc=cos_trunc,
                                                         fock_trunc=fock_trunc)

    def epr_report_hamiltonian(self,
                               swp_variable: str = "variation",
                               numeric=True):
        """Reports in a markdown friendly table the hamiltonian results.

        Args:
            swp_variable (str, optional): Variable against which we swept. Defaults to 'variation'.
        """
        self.epr_quantum_analysis.plot_hamiltonian_results(
            swp_variable=swp_variable)
        self.epr_quantum_analysis.report_results(swp_variable=swp_variable,
                                                 numeric=numeric)

    def epr_get_frequencies(self,
                            junctions: dict = None,
                            dissipatives: dict = None) -> pd.DataFrame:
        """Returns all frequencies and quality factors vs a variation.
        It also initializes the systems for the epr analysis in terms of junctions and dissipatives

        Args:
            junctions (dict, optional): Each element of this dictionary describes one junction.
                Defaults to dict().
            dissipatives (dict, optional): Each element of this dictionary describes one dissipative.
                Defaults to dict().

        Returns:
            pd.DataFrame: multi-index, frequency and quality factors for each variation point.
        """
        # TODO: do I need to reset self.pinfo.junctions (does it keep the older analysis one)
        self.epr_start(junctions, dissipatives)
        return self.epr_distributed_analysis.get_ansys_frequencies_all()
