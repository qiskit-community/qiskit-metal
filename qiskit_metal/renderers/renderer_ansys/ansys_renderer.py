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
from pyEPR.ansys import parse_units, HfssApp

from qiskit_metal.draw.utility import to_vec3D
from qiskit_metal.draw.basic import is_rectangle
from qiskit_metal.renderers.renderer_base import QRenderer
from qiskit_metal.toolbox_python.utility_functions import toggle_numbers, bad_fillet_idxs
from qiskit_metal.toolbox_metal.parsing import is_true

from qiskit_metal import Dict


def good_fillet_idxs(coords: list,
                     fradius: float,
                     precision: int = 9,
                     isclosed: bool = False):
    """
    Get list of vertex indices in a linestring (isclosed = False) or polygon (isclosed = True) that can be filleted based on
    proximity to neighbors.

    Args:
        coords (list): Ordered list of tuples of vertex coordinates.
        fradius (float): User-specified fillet radius from QGeometry table.
        precision (int, optional): Digits of precision used for round(). Defaults to 9.
        isclosed (bool, optional): Boolean denoting whether the shape is a linestring or polygon. Defaults to False.

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
    """
    Create a valid variable name from the given one by removing having it begin with a letter or underscore
    followed by an unlimited string of letters, numbers, and underscores.

    Args:
        name (str): Initial, possibly unusable, string to be modified.

    Returns:
        str: Variable name consistent with Python naming conventions.
    """
    # Remove invalid characters
    name = re.sub('[^0-9a-zA-Z_]', '', name)
    # Remove leading characters until we find a letter or underscore
    name = re.sub('^[^a-zA-Z_]+', '', name)
    return name


class QAnsysRenderer(QRenderer):
    """
    Extends QRenderer to export designs to Ansys using pyEPR.
    The methods which a user will need for Ansys export should be found within this class.

    Default Options:
        * Lj: '10nH' -- Lj has units of nanoHenries (nH)
        * Cj: 0 -- Cj *must* be 0 for pyEPR analysis! Cj has units of femtofarads (fF)
        * _Rj: 0 -- _Rj *must* be 0 for pyEPR analysis! _Rj has units of Ohms
        * max_mesh_length_jj: '7um' -- Maximum mesh length for Josephson junction elements
        * project_path: None -- Default project path; if None --> get active
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
        project_path=None,  # default project path; if None --> get active
        project_name=None,  # default project name
        design_name=None,  # default design name
        # Ansys file extension for 2016 version and newer
        ansys_file_extension='.aedt',
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
    # yapf: enable

    NAME_DELIM = r'_'

    name = 'ansys'
    """Name"""

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

    element_table_data = dict(path=dict(wire_bonds=False),
                              junction=dict(
                                  inductance=default_options['Lj'],
                                  capacitance=default_options['Cj'],
                                  resistance=default_options['_Rj'],
                                  mesh_kw_jj=parse_units(
                                      default_options['max_mesh_length_jj'])))

    def __init__(self,
                 design: 'QDesign',
                 initiate=True,
                 render_template: Dict = None,
                 render_options: Dict = None):
        """
        Create a QRenderer for Ansys.

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

        # Default behavior is to render all components unless a strict subset was chosen
        self.render_everything = True

        self._pinfo = None

    def open_ansys(self,
                   path: str = None,
                   executable: str = 'reg_ansysedt.exe',
                   path_var: str = 'ANSYSEM_ROOT202'):
        """
        Open a session of Ansys. Default is version 2020 R2, but can be overridden.

        Args:
            path (str): Path to the Ansys executable. Defaults to None
            executable (str): Name of the ansys executable. Defaults to 'reg_ansysedt.exe'
            path_var (str): Name of the OS environment variable that contains the path to the Ansys executable.
                            Only used when path=None. Defaults to 'ANSYSEM_ROOT202' (Ansys ver. 2020 R2)
        """
        if not system() == 'Windows':
            self.logger.warning(
                'You are using %s, but this is a renderer to Ansys, which only runs on Windows. '
                'Expect any sort of Errors if you try to work with this renderer beyond this point.'
                % system())

        import subprocess
        if path is None:
            try:
                path = os.environ[path_var]
            except KeyError:
                self.logger.error(
                    'environment variable %s not found. Is Ansys 2020 R2 installed on this machine? '
                    'If yes, then create said environment variable. If you have a different version of Ansys, '
                    'then pass to open_ansys() the path to its binary, or the env var that stores it.'
                    % path_var)
                raise
        else:
            path = os.path.abspath(path)
        cmdlist = [os.path.sep.join([path, executable]), '-shortcut']
        subprocess.call(cmdlist, cwd=path)

    def connect_ansys(self,
                      project_path: str = None,
                      project_name: str = None,
                      design_name: str = None):
        """
        If none of the optional parameters are provided: connects to the Ansys COM, then
        checks for, and grab if present, an active project, design, and design setup.

        If the optional parameters are provided: if present, opens the project file and design in Ansys.

        Args:
            project_path (str, optional): Path without file name
            project_name (str, optional): File name (with or without extension)
            design_name (str, optional): Name of the default design to open from the project file

        """
        if not system() == 'Windows':
            self.logger.warning(
                'You are using %s, but this is a renderer to Ansys, which only runs on Windows. '
                'Expect any sort of Errors if you try to work with this renderer beyond this point.'
                % system())

        # pyEPR does not like extensions
        if project_name:
            project_name = project_name.replace(".aedt", "")
        # open connection through pyEPR
        import pythoncom
        try:
            self._pinfo = epr.ProjectInfo(
                project_path=self._options['project_path']
                if not project_path else project_path,
                project_name=self._options['project_name']
                if not project_name else project_name,
                design_name=self._options['design_name']
                if not design_name else design_name)
        except pythoncom.com_error as error:
            print("com_error: ", error)
            hr, msg, exc, arg = error.args
            if msg == "Invalid class string":  # and hr == -2147221005 and exc is None and arg is None
                self.logger.error(
                    "pyEPR cannot find the Ansys COM. Ansys installation might not have registered it. "
                    "To verify if this is the problem, execute the following: ",
                    "`print(win32com.client.Dispatch('AnsoftHfss.HfssScriptInterface'))` ",
                    "If the print-out is not `<COMObject ...>` then Ansys COM is not registered, ",
                    "and you will need to look into correcting your Ansys installation."
                )
            raise error

    def disconnect_ansys(self):
        """
        Disconnect Ansys.
        """
        if self.pinfo:
            self.pinfo.disconnect()
        else:
            self.logger.warning(
                'This renderer appears to be already disconnected from Ansys')

    def new_ansys_project(self):
        """
        Creates a new empty project in Ansys.
        """
        here = HfssApp()
        here.get_app_desktop().new_project()

    def connect_ansys_design(self, design_name: str = None):
        """ Used to switch between existing designs.

        Args:
            design_name (str, optional): Name within the active project. Defaults to None.
        """

        if self.pinfo:
            if self.pinfo.project:
                all_designs_names = self.pinfo.project.get_design_names()
                if design_name not in all_designs_names:
                    self.logger.warning(
                        f'The design_name={design_name} is not in project.  Connection did not happen.'
                    )
                    return

                try:
                    self.pinfo.connect_design(design_name)
                    self.pinfo.connect_setup()
                except AttributeError:
                    self.logger.error(
                        'Please install a more recent version of pyEPR (>=0.8.4.3)'
                    )
            else:
                self.logger.warning(
                    'Either you do not have a project loaded in Ansys, or you are not connected to it. '
                    'Try executing hfss.connect_ansys(), or creating a new Ansys project. '
                    'Also check the help file and other tutorials notebooks')
        else:
            self.logger.warning(
                'It does not look like you are connected to Ansys. Please use connect_ansys() '
                'and make sure self.pinfo is set. There must be a project open in Ansys first.'
            )

    @property
    def pinfo(self) -> epr.ProjectInfo:
        """Project info for Ansys renderer (class: pyEPR.ProjectInfo)."""
        return self._pinfo

    @property
    def modeler(self):
        """ The modeler from pyEPR HfssModeler. 

        Returns:
            pyEPR.ansys.HfssModeler: Reference to  design.HfssModeler in Ansys.
        """
        if self.pinfo:
            if self.pinfo.design:
                return self.pinfo.design.modeler

    def plot_ansys_fields(
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
        """Plot fields in Ansys. The options are populated by the component's options.

        Args:
            object_name (str): Used to plot on faces of.
            name (str, optional): "NAME:<PlotName>" Defaults to None.
            UserSpecifyName (int, optional): 0 if default name for plot is used, 1 otherwise. Defaults to None.
            UserSpecifyFolder (int, optional): 0 if default folder for plot is used, 1 otherwise. Defaults to None.
            QuantityName (str, optional): Type of plot to create. Possible values are: 
            Mesh plots: "Mesh"
            Field plots: "Mag_E", "Mag_H", "Mag_Jvol", "Mag_Jsurf","ComplexMag_E", "ComplexMag_H", 
            "ComplexMag_Jvol", "ComplexMag_Jsurf", "Vector_E", "Vector_H", "Vector_Jvol", "Vector_Jsurf", 
            "Vector_RealPoynting","Local_SAR", "Average_SAR". Defaults to None.
            PlotFolder (str, optional): Name of the folder to which the plot should be added. Possible values 
            are: "E Field",  "H Field", "Jvol", "Jsurf", "SARField", and "MeshPlots". Defaults to None.
            StreamlinePlot (bool, optional): Passed to CreateFieldPlot. Defaults to None.
            AdjacentSidePlot (bool, optional): Passed to CreateFieldPlot. Defaults to None.
            FullModelPlot (bool, optional): Passed to CreateFieldPlot. Defaults to None.
            IntrinsicVar (str, optional): Formatted string that specifies the frequency and phase 
            at which to make the plot.  For example: "Freq='1GHz' Phase='30deg'" Defaults to None.
            PlotGeomInfo_0 (int, optional): 0th entry in list for "PlotGeomInfo:=", <PlotGeomArray>. Defaults to None.
            PlotGeomInfo_1 (str, optional): 1st entry in list for "PlotGeomInfo:=", <PlotGeomArray>. Defaults to None.
            PlotGeomInfo_2 (str, optional): 2nd entry in list for "PlotGeomInfo:=", <PlotGeomArray>. Defaults to None.
            PlotGeomInfo_3 (int, optional): 3rd entry in list for "PlotGeomInfo:=", <PlotGeomArray>. Defaults to None.

        Returns:
            NoneType: Return information from oFieldsReport.CreateFieldPlot(). 
            The method CreateFieldPlot() always returns None.
        """
        if not self.pinfo:
            self.logger.warning('pinfo is None.')
            return

        if self.pinfo.design:
            if not self.pinfo.design._fields_calc:
                self.logger.warning('The _fields_calc in design is None.')
                return
            if not self.pinfo.design._modeler:
                self.logger.warning('The _modeler in design is None.')
                return
        else:
            self.logger.warning('The design in pinfo is None.')
            return

        if not self.pinfo.setup:
            self.logger.warning('The setup in pinfo is None.')
            return

        #TODO: This is just a prototype - should add features and flexibility.
        oFieldsReport = self.pinfo.design._fields_calc  #design.GetModule("FieldsReporter")
        oModeler = self.pinfo.design._modeler  #design.SetActiveEditor("3D Modeler")
        setup = self.pinfo.setup

        # Object ID - use to plot on faces of
        object_id = oModeler.GetObjectIDByName(object_name)
        # Can also use hfss.pinfo.design._modeler.GetFaceIDs("main")

        paf = self.options['plot_ansys_fields_options']

        if not name:
            name = self.parse_value(paf['name'])

        # Name of the solution setup and solution formatted as:"<SolveSetupName> : <WhichSolution>",
        # where <WhichSolution> can be "Adaptive_<n>", "LastAdaptive", or "PortOnly".
        # HFSS requires a space on either side of the ‘:’ character.
        # If it is missing, the plot will not be created.
        SolutionName = f"{setup.name} : LastAdaptive"
        if not UserSpecifyName:
            UserSpecifyName = int(self.parse_value(paf['UserSpecifyName']))
        if not UserSpecifyFolder:
            UserSpecifyFolder = int(self.parse_value(paf['UserSpecifyFolder']))
        if not QuantityName:
            QuantityName = self.parse_value(paf['QuantityName'])
        if not PlotFolder:
            PlotFolder = self.parse_value(paf['PlotFolder'])
        if not StreamlinePlot:
            StreamlinePlot = is_true(self.parse_value(paf['StreamlinePlot']))
        if not AdjacentSidePlot:
            AdjacentSidePlot = is_true(self.parse_value(
                paf['AdjacentSidePlot']))
        if not FullModelPlot:
            FullModelPlot = is_true(self.parse_value(paf['FullModelPlot']))
        if not IntrinsicVar:
            IntrinsicVar = self.parse_value(paf['IntrinsicVar'])
        if not PlotGeomInfo_0:
            PlotGeomInfo_0 = int(self.parse_value(paf['PlotGeomInfo_0']))
        if not PlotGeomInfo_1:
            PlotGeomInfo_1 = self.parse_value(paf['PlotGeomInfo_1'])
        if not PlotGeomInfo_2:
            PlotGeomInfo_2 = self.parse_value(paf['PlotGeomInfo_2'])
        if not PlotGeomInfo_3:
            PlotGeomInfo_3 = int(self.parse_value(paf['PlotGeomInfo_3']))

        # used to pass to CreateFieldPlot
        # Copied from  pdf at http://www.ece.uprm.edu/~rafaelr/inel6068/HFSS/scripting.pdf
        #<PlotGeomArray>Array(<NumGeomTypes>, <GeomTypeData>,<GeomTypeData>, ...)
        # For example:
        # Array(4, "Volume", "ObjList", 1, "Box1","Surface", "FacesList", 1, "12", "Line", 1,"Polyline1",
        #       "Point", 2, "Point1", "Point2"
        PlotGeomInfo = [
            PlotGeomInfo_0, PlotGeomInfo_1, PlotGeomInfo_2, PlotGeomInfo_3,
            str(object_id)
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
        #yapf: enable
        return oFieldsReport.CreateFieldPlot(args_list, "Field")

    def plot_ansys_delete(self, names: list):
        """
        Delete plots from modeler window in Ansys.
        Does not throw an error if names are missing. 

        Can give multiple names, for example:
        hfss.plot_ansys_delete(['Mag_E1', 'Mag_E1_2'])

        Args:
            names (list): Names of plots to delete from modeler window.
        """
        # (["Mag_E1"]
        oFieldsReport = self.pinfo.design._fields_calc
        return oFieldsReport.DeleteFieldPlot(names)

    def add_message(self, msg: str, severity: int = 0):
        """
        Add message to Message Manager box in Ansys.

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
        try:
            return self.pinfo.design.save_screenshot(path, show)
        except AttributeError:
            self.logger.error(
                'Please install a more recent version of pyEPR (>=0.8.4.3)')

    def render_design(self,
                      selection: Union[list, None] = None,
                      open_pins: Union[list, None] = None,
                      box_plus_buffer: bool = True):
        """
        Initiate rendering of components in design contained in selection, assuming they're valid.
        Components are rendered before the chips they reside on, and subtraction of negative shapes
        is performed at the very end.

        Chip_subtract_dict consists of component names (keys) and a set of all elements within each component that
        will eventually be subtracted from the ground plane. Add objects that are perfect conductors and/or have
        meshing to self.assign_perfE and self.assign_mesh, respectively; both are initialized as empty lists. Note
        that these objects are "refreshed" each time render_design is called (as opposed to in the init function)
        to clear QAnsysRenderer of any leftover items from the last call to render_design.

        Among the components selected for export, there may or may not be unused (unconnected) pins.
        The second parameter, open_pins, contains tuples of the form (component_name, pin_name) that
        specify exactly which pins should be open rather than shorted during the simulation. Both the
        component and pin name must be specified because the latter could be shared by multiple
        components. All pins in this list are rendered with an additional endcap in the form of a
        rectangular cutout, to be subtracted from its respective plane.

        Args:
            selection (Union[list, None], optional): List of components to render. Defaults to None.
            open_pins (Union[list, None], optional): List of tuples of pins that are open. Defaults to None.
            box_plus_buffer (bool): Either calculate a bounding box based on the location of rendered geometries
                                     or use chip size from design class. 
        """
        self.chip_subtract_dict = defaultdict(set)
        self.assign_perfE = []
        self.assign_mesh = []

        self.render_tables(selection)
        self.add_endcaps(open_pins)

        self.render_chips(box_plus_buffer=box_plus_buffer)
        self.subtract_from_ground()
        self.add_mesh()

    def render_tables(self, selection: Union[list, None] = None):
        """
        Render components in design grouped by table type (path, poly, or junction).
        Start by initializing chip boundaries for later use.

        Args:
            selection (Union[list, None], optional): List of components to render. (Default: None)
        """
        self.min_x_main = float('inf')
        self.min_y_main = float('inf')
        self.max_x_main = float('-inf')
        self.max_y_main = float('-inf')

        for table_type in self.design.qgeometry.get_element_types():
            self.render_components(table_type, selection)

    def render_components(self,
                          table_type: str,
                          selection: Union[list, None] = None):
        """
        Render individual components by breaking them down into individual elements.

        Args:
            table_type (str): Table type (poly, path, or junction).
            selection (Union[list, None], optional): List of components to render.  (Default: None)
        """
        # Establish bounds for exported components and update these accordingly

        selection = selection if selection else []
        table = self.design.qgeometry.tables[table_type]

        if selection:
            qcomp_ids, case = self.get_unique_component_ids(selection)

            if qcomp_ids:  # Render strict subset of components
                # Update bounding box (and hence main chip dimensions)
                for qcomp_id in qcomp_ids:
                    min_x, min_y, max_x, max_y = self.design._components[
                        qcomp_id].qgeometry_bounds()
                    self.min_x_main = min(min_x, self.min_x_main)
                    self.min_y_main = min(min_y, self.min_y_main)
                    self.max_x_main = max(max_x, self.max_x_main)
                    self.max_y_main = max(max_y, self.max_y_main)
            else:  # All components rendered
                for qcomp in self.design.components:
                    min_x, min_y, max_x, max_y = self.design.components[
                        qcomp].qgeometry_bounds()
                    self.min_x_main = min(min_x, self.min_x_main)
                    self.min_y_main = min(min_y, self.min_y_main)
                    self.max_x_main = max(max_x, self.max_x_main)
                    self.max_y_main = max(max_y, self.max_y_main)

            if case != 1:  # Render a subset of components using mask
                mask = table['component'].isin(qcomp_ids)
                table = table[mask]

        else:
            for qcomp in self.design.components:
                min_x, min_y, max_x, max_y = self.design.components[
                    qcomp].qgeometry_bounds()
                self.min_x_main = min(min_x, self.min_x_main)
                self.min_y_main = min(min_y, self.min_y_main)
                self.max_x_main = max(max_x, self.max_x_main)
                self.max_y_main = max(max_y, self.max_y_main)

        for _, qgeom in table.iterrows():
            self.render_element(qgeom, bool(table_type == 'junction'))

        if table_type == 'path':
            self.auto_wirebonds(table)

    def render_element(self, qgeom: pd.Series, is_junction: bool):
        """
        Render an individual shape whose properties are listed in a row of QGeometry table.
        Junction elements are handled separately from non-junction elements, as the former
        consist of two rendered shapes, not just one.

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

        qc_name = 'Lj_' + str(qgeom['component'])
        qc_elt = get_clean_name(qgeom['name'])
        qc_shapely = qgeom.geometry
        qc_chip_z = parse_units(self.design.get_chip_z(qgeom.chip))
        qc_width = parse_units(qgeom.width)

        name = f'{qc_name}{QAnsysRenderer.NAME_DELIM}{qc_elt}'

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
        self.logger.debug(f'Drawing a rectangle: {name}')
        poly_ansys = self.modeler.draw_rect_corner([x_min, y_min, qc_chip_z],
                                                   x_max - x_min, y_max - y_min,
                                                   qc_chip_z, **ansys_options)
        axis = 'x' if abs(x1 - x0) > abs(y1 - y0) else 'y'
        self.modeler.rename_obj(poly_ansys, 'JJ_rect_' + name)
        self.assign_mesh.append('JJ_rect_' + name)

        # Draw line
        poly_jj = self.modeler.draw_polyline([endpoints_3d[0], endpoints_3d[1]],
                                             closed=False,
                                             **dict(color=(128, 0, 128)))
        poly_jj = poly_jj.rename('JJ_' + name + '_')
        poly_jj.show_direction = True

    def render_element_poly(self, qgeom: pd.Series):
        """
        Render a closed polygon.

        Args:
            qgeom (pd.Series): GeoSeries of element properties.
        """
        ansys_options = dict(transparency=0.0)

        qc_name = self.design._components[qgeom['component']].name
        qc_elt = get_clean_name(qgeom['name'])

        qc_shapely = qgeom.geometry  # shapely geom
        qc_chip_z = parse_units(self.design.get_chip_z(qgeom.chip))
        qc_fillet = round(qgeom.fillet, 7)

        name = f'{qc_elt}{QAnsysRenderer.NAME_DELIM}{qc_name}'

        points = parse_units(list(
            qc_shapely.exterior.coords))  # list of 2d point tuples
        points_3d = to_vec3D(points, qc_chip_z)

        if is_rectangle(qc_shapely):  # Draw as rectangle
            self.logger.debug(f'Drawing a rectangle: {name}')
            x_min, y_min, x_max, y_max = qc_shapely.bounds
            poly_ansys = self.modeler.draw_rect_corner(
                *parse_units([[x_min, y_min, qc_chip_z], x_max - x_min,
                              y_max - y_min, qc_chip_z]), **ansys_options)
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
                isclosed=True)
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

        if qgeom['subtract']:
            self.chip_subtract_dict[qgeom.chip].add(name)

        # Potentially add to list of elements to metallize
        elif not qgeom['helper']:
            self.assign_perfE.append(name)

    def render_element_path(self, qgeom: pd.Series):
        """
        Render a path-type element.

        Args:
            qgeom (pd.Series): GeoSeries of element properties.
        """
        ansys_options = dict(transparency=0.0)

        qc_name = self.design._components[qgeom['component']].name
        qc_elt = get_clean_name(qgeom['name'])

        qc_shapely = qgeom.geometry  # shapely geom
        qc_chip_z = parse_units(self.design.get_chip_z(qgeom.chip))

        name = f'{qc_elt}{QAnsysRenderer.NAME_DELIM}{qc_name}'

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
                    'No modeler was found. Are you connected to an active Ansys Design?'
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
                isclosed=False)
            if idxs_to_fillet:
                self.modeler._fillet(qc_fillet, idxs_to_fillet, poly_ansys)

        if qc_width:
            x0, y0 = points[0]
            x1, y1 = points[1]
            vlen = math.sqrt((x1 - x0)**2 + (y1 - y0)**2)
            p0 = np.array([
                x0, y0, 0
            ]) + qc_width / (2 * vlen) * np.array([y0 - y1, x1 - x0, 0])
            p1 = np.array([
                x0, y0, 0
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

        if qgeom['subtract']:
            self.chip_subtract_dict[qgeom.chip].add(name)

        elif qgeom['width'] and (not qgeom['helper']):
            self.assign_perfE.append(name)

    def render_chips(self,
                     draw_sample_holder: bool = True,
                     box_plus_buffer: bool = True):
        """
        Render chips using info from design.get_chip_size method.

        Renders the ground plane of this chip (if one is present).
        Renders the wafer of the chip.

        Args:
            draw_sample_holder (bool, optional): Option to draw vacuum box around chip. Defaults to True.
            box_plus_buffer (bool): Either calculate a bounding box based on the location of rendered geometries
                                     or use chip size from design class. 
        """
        ansys_options = dict(transparency=0.0)

        for chip_name in self.chip_subtract_dict:
            ops = self.design._chips[chip_name]
            p = self.design.get_chip_size(chip_name)
            origin = parse_units([p['center_x'], p['center_y'], p['center_z']])
            size = parse_units([p['size_x'], p['size_y'], p['size_z']])
            vac_height = parse_units(
                [p['sample_holder_top'], p['sample_holder_bottom']])
            if chip_name == 'main':
                # Draw plane, wafer, and sample holder (vacuum box)
                # x and y dimensions of the vacuum box are identical to that of the 'main' chip
                self.min_x_main = parse_units(self.min_x_main)
                self.max_x_main = parse_units(self.max_x_main)
                self.min_y_main = parse_units(self.min_y_main)
                self.max_y_main = parse_units(self.max_y_main)
                comp_center_x = (self.min_x_main + self.max_x_main) / 2
                comp_center_y = (self.min_y_main + self.max_y_main) / 2
                min_x_edge = self.min_x_main - parse_units(
                    self._options['x_buffer_width_mm'])
                max_x_edge = self.max_x_main + parse_units(
                    self._options['x_buffer_width_mm'])
                min_y_edge = self.min_y_main - parse_units(
                    self._options['y_buffer_width_mm'])
                max_y_edge = self.max_y_main + parse_units(
                    self._options['y_buffer_width_mm'])

                if not box_plus_buffer:
                    # Expect all components are rendered and
                    # the overall bounding box lies within 9 X 6 chip
                    if not (origin[0] - size[0] / 2 <= self.min_x_main <
                            self.max_x_main <= origin[0] + size[0] / 2) and (
                                origin[1] - size[1] / 2 <= self.min_y_main <
                                self.max_y_main <= origin[1] + size[1] / 2):
                        self.logger.warning(
                            'A bounding box with buffer around the QComponents are outside of the size of chip denoted in DesignPlanar.\n'
                            'Chip size from DesignPlanar is:\n'
                            f' x={size[0]}, y={size[1]}, z={size[2]}; centered at x={origin[0]}, y={origin[1]}, z={origin[2]}. \n'
                            'Bounding box with buffer for rendered geometries is:\n'
                            f' min_x={self.min_x_main}, max_x={self.max_x_main}, min_y={self.min_y_main}, max_y={self.max_y_main}.'
                        )

                    plane = self.modeler.draw_rect_center(
                        origin,
                        x_size=size[0],
                        y_size=size[1],
                        name=f'ground_{chip_name}_plane',
                        **ansys_options)

                    whole_chip = self.modeler.draw_box_center(
                        [origin[0], origin[1], size[2] / 2],
                        [size[0], size[1], -size[2]],
                        name=chip_name,
                        material=ops['material'],
                        color=(186, 186, 205),
                        transparency=0.2,
                        wireframe=False)
                    if draw_sample_holder:
                        vacuum_box = self.modeler.draw_box_center(
                            [
                                origin[0], origin[1],
                                (vac_height[0] - vac_height[1]) / 2
                            ], [size[0], size[1],
                                sum(vac_height)],
                            name='sample_holder')
                else:
                    # A strict subset of components is rendered, or exported components extend beyond boundaries of 9 X 6 chip
                    x_width = max_x_edge - min_x_edge
                    y_width = max_y_edge - min_y_edge

                    plane = self.modeler.draw_rect_center(
                        [comp_center_x, comp_center_y, origin[2]],
                        x_size=x_width,
                        y_size=y_width,
                        name=f'ground_{chip_name}_plane',
                        **ansys_options)
                    whole_chip = self.modeler.draw_box_center(
                        [comp_center_x, comp_center_y, size[2] / 2],
                        [x_width, y_width, -size[2]],
                        name=chip_name,
                        material=ops['material'],
                        color=(186, 186, 205),
                        transparency=0.2,
                        wireframe=False)
                    if draw_sample_holder:
                        vacuum_box = self.modeler.draw_box_center(
                            [
                                comp_center_x, comp_center_y,
                                (vac_height[0] - vac_height[1]) / 2
                            ], [x_width, y_width,
                                sum(vac_height)],
                            name='sample_holder')
            else:
                # Only draw plane and wafer
                plane = self.modeler.draw_rect_center(
                    origin,
                    x_size=size[0],
                    y_size=size[1],
                    name=f'ground_{chip_name}_plane',
                    **ansys_options)

                whole_chip = self.modeler.draw_box_center(
                    [origin[0], origin[1], size[2] / 2],
                    [size[0], size[1], -size[2]],
                    name=chip_name,
                    material=ops['material'],
                    color=(186, 186, 205),
                    transparency=0.2,
                    wireframe=False)
            if self.chip_subtract_dict[
                    chip_name]:  # Any layer which has subtract=True qgeometries will have a ground plane
                self.assign_perfE.append(f'ground_{chip_name}_plane')

    def add_endcaps(self, open_pins: Union[list, None] = None):
        """
        Create endcaps (rectangular cutouts) for all pins in the list open_pins and add them to chip_subtract_dict.
        Each element in open_pins takes on the form (component_name, pin_name) and corresponds to a single pin.

        Args:
            open_pins (Union[list, None], optional): List of tuples of pins that are open. Defaults to None.
        """
        open_pins = open_pins if open_pins else []

        for comp, pin in open_pins:
            pin_dict = self.design.components[comp].pins[pin]
            width, gap = parse_units([pin_dict['width'], pin_dict['gap']])
            mid, normal = parse_units(pin_dict['middle']), pin_dict['normal']
            rect_mid = np.append(mid + normal * gap / 2, [0])
            # Assumption: pins only point in x or y directions
            # If this assumption is not satisfied, draw_rect_center no longer works -> must use draw_polyline
            endcap_name = f'endcap_{comp}_{pin}'
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
            self.chip_subtract_dict[pin_dict['chip']].add(endcap_name)

    def subtract_from_ground(self):
        """
        For each chip, subtract all "negative" shapes residing on its surface if any such shapes exist.
        """
        for chip, shapes in self.chip_subtract_dict.items():
            if shapes:
                import pythoncom
                try:
                    self.modeler.subtract(f'ground_{chip}_plane', list(shapes))
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
        """
        Add mesh to all elements in self.assign_mesh.
        """
        if self.assign_mesh:
            self.modeler.mesh_length(
                'small_mesh',
                self.assign_mesh,
                MaxLength=self._options['max_mesh_length_jj'])

    #Still implementing
    def auto_wirebonds(self, table):
        """
        Adds wirebonds to the Ansys model for path elements where;
        subtract = True and wire_bonds = True.
        Uses render options for determining of the;
        * wb_threshold -- the minimum distance between two vertices of a path for a
            wirebond to be added.
        * wb_offset -- offset distance for wirebond placement (along the direction
            of the cpw)
        * wb_size -- controls the width of the wirebond (wb_size * path['width'])
        """
        norm_z = np.array([0, 0, 1])

        wb_threshold = parse_units(self._options['wb_threshold'])
        wb_offset = parse_units(self._options['wb_offset'])

        #selecting only the qgeometry which meet criteria
        wb_table = table.loc[table['hfss_wire_bonds'] == True]
        wb_table2 = wb_table.loc[wb_table['subtract'] == True]

        #looping through each qgeometry
        for _, row in wb_table2.iterrows():
            geom = row['geometry']
            width = row['width']
            #looping through the linestring of the path to determine where WBs should be
            for index, i_p in enumerate(geom.coords[:-1], start=0):
                j_p = np.asarray(geom.coords[:][index + 1])
                vert_distance = parse_units(distance.euclidean(i_p, j_p))
                if vert_distance > wb_threshold:
                    #Gets number of wirebonds to fit in section of path
                    wb_count = int(vert_distance // wb_threshold)
                    #finds the position vector
                    wb_pos = (j_p - i_p) / (wb_count + 1)
                    #gets the norm vector for finding the orthonormal of path
                    wb_vec = wb_pos / np.linalg.norm(wb_pos)
                    #finds the orthonormal (for orientation)
                    wb_perp = np.cross(norm_z, wb_vec)[:2]
                    #finds the first wirebond to place (rest are in the loop)
                    wb_pos_step = parse_units(wb_pos + i_p) + (wb_vec *
                                                               wb_offset)
                    #Other input values could be modified, kept to minimal selection for automation
                    #for the time being. Loops to place N wirebonds based on length of path section.
                    for wb_i in range(wb_count):
                        self.modeler.draw_wirebond(
                            pos=wb_pos_step + parse_units(wb_pos * wb_i),
                            ori=wb_perp,
                            width=parse_units(width * self._options['wb_size']),
                            height=parse_units(width *
                                               self._options['wb_size']),
                            z=0,
                            wire_diameter='0.015mm',
                            NumSides=6,
                            name='g_wb',
                            material='pec',
                            solve_inside=False)

    def clean_active_design(self):
        """
        Remove all elements from Ansys Modeler.
        """
        if self.pinfo:
            if self.pinfo.get_all_object_names():
                project_name = self.pinfo.project_name
                design_name = self.pinfo.design_name
                select_all = ','.join(self.pinfo.get_all_object_names())

                oDesktop = self.pinfo.design.parent.parent._desktop  # self.pinfo.design does not work
                oProject = oDesktop.SetActiveProject(project_name)
                oDesign = oProject.SetActiveDesign(design_name)

                # The available editors: "Layout", "3D Modeler", "SchematicEditor"
                oEditor = oDesign.SetActiveEditor("3D Modeler")

                oEditor.Delete(["NAME:Selections", "Selections:=", select_all])
