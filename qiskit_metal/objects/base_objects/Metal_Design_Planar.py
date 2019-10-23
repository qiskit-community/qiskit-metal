# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


'''
Planar design class for Qiskit Metal.
For use with drawing of any 2D planar design structures. Provides a number of functions for HFSS drawing.

@date: Created on Tue May 14 17:16:47 2019
@author: Zlatko K. Minev
Updated 2019/09/25 - Thomas McConkey
'''
# pylint: disable=invalid-name

from collections import OrderedDict

from ...toolbox.attribute_dictionary import Dict
from ...config import DEFAULT_OPTIONS
from ...draw_utility import parse_units_user
from ... import draw_functions

from .Metal_Design_Base import Metal_Design_Base
from .Metal_Utility import is_metal_object

DEFAULT_OPTIONS.update({
    'Design_Planar': Dict({
        ####################################################
        # PlanarDesign global paramters
        'globals': Dict({
            'global_units': 'mm',
            'bounding_box': [[0, 0],
                             [0, 0],
                             ['0.890mm', '0.900mm']],     # Absolute Offset; [[-x,x],[-y,y],[-z,z]], mainly for HFSS currently
            # funciton used to draw the bounding box, found in 'draw_functions.py'
            'func_draw_bounding_box': 'draw_bounding_box'
        }),

        ####################################################
        # Substrate chips
        #  Chip parameters. Currently required to have one primary chip with a
        # ground_plane named 'ground_plane' for easy compatibility with HFSS
        # draw_substrate currently found in 'draw_functions.py'
        'chips': Dict({
            'main': Dict({
                'func_draw': 'draw_substrate',
                **DEFAULT_OPTIONS['draw_substrate']
            })
        }),

        ####################################################
        # Variables
        # Design variables, chip parameter, and design
        # Is where to place variable names which are wanted for optemetrics in HFSS
        'variables': {
        },

    })
    })


class Design_Planar(Metal_Design_Base): # pylint: disable=invalid-name
    """
    Contains design definitions and has some utility functions.
    All Metal objects on chip are tracked by this parent as well as their connectors.


    Keyword Arguments:
    ------------------------
        objects {[Dict]} -- [Pass an objects dictionary] (default: {None})
        connectors {[Dict]} -- [Tracks all connectrs in the design that can be used for
                                named connections. Made from points] (default: {None})
        oDesign_ {[pyEPR.hfss.HfssDesign]} -- [Used to draw in HFSS] (default: {None})
        design_parameters {[type]} -- [Special options for the design] (default: {None})

    Design_Planar properties:
    ------------------------
        params (Dict) : Collection of all parameters
            Sets up using default parameters, based on `DEFAULT_OPTIONS['PlanarDesign']`
            Keep each element as same object, update, do not change instance.

    Metal_Design_Base properties:
    ----------------------
        objects (Dict) : Dict of all Metal_Objects
        connectors (Dict) : Dict of all connectors associated with the Metal_Objects and
                        custom connectors
    """
    def __init__(self,
                 objects=None,
                 connectors=None,
                 oDesign_=None,
                 design_parameters=None):
        if not design_parameters:
            design_parameters = {}

        super().__init__(objects=objects, connectors=connectors)

        self.params = Dict({
            'globals': DEFAULT_OPTIONS['Design_Planar']['globals'],
            'variables': DEFAULT_OPTIONS['Design_Planar']['variables'],
            'chips': DEFAULT_OPTIONS['Design_Planar']['chips']
        })
        for key in design_parameters:
            self.params[key].update(design_parameters.get(key, {}))

        self.track_objs = {
            'qubits': {},
            'cpw': {},
            'launchers': {}
        }

        self._mesh_assign = Dict()  # internal dict used to append mesh ops and reassign

        self.set_oDesign(oDesign_)

#Likely can be safely removed (2019/09/25)
    # def add_track_object(self, options, track_me, name=None):
    #     '''
    #         Assumes there is a categoty and name
    #     '''
    #     if name is None:
    #         name = options['name']
    #     if options['category'] not in self.track_objs.keys():
    #         self.track_objs[options['category']] = OrderedDict()
    #     self.track_objs[options['category']][name] = track_me


#########COMMANDS##################################################
    def get_chip_size(self, options):
        '''
        Gets the size of the chip in the options dictionary
        Takes options.chip
        '''
        return parse_units_user(self.params.chips[options['chip']]['size'])

    def get_substrate_z(self, chip_name='main'):
        '''
        Returns the z axis location of the plane which this chip is located at. Default of '0'
        Only of interest if making multiple chips
        '''
        if isinstance(chip_name, dict):
            chip_name = chip_name.get('chip', 'main')
            if isinstance(chip_name, dict):
                chip_name = 'main'
        if chip_name in self.params.chips:
            return self.params.chips[chip_name]['elevation']
        else:
            raise Exception(
                'ERROR: You specified a chip name that is not defined. ')

    def get_ground_plane(self, options):
        ''' assumes options is a dict that has a key 'chip' '''
        return self.params.chips[options.get('chip', 'main')]['ground_plane']


#########GDS_COMMANDS##################################################
    def gds_draw_all(self, path = None):
        r'''
        Create full gds export cell

        path : str : if passed will save

        Can see with
            gdspy.LayoutViewer()

        can save with
            # Save all created cells in file 'first.gds'
            path = r'C:\zkm\2019-hfss\gds'
            gdspy.write_gds(path+r'\first.gds')
        '''
        import gdspy

        gdspy.current_library.cell_dict.clear()
        device = gdspy.Cell('TOP_CELL')
        for _, obj in self.objects.items():
            if is_metal_object(obj):
                cell = obj.gds_draw()
                device.add(gdspy.CellReference(cell))

        if path:
            gdspy.write_gds(path)

        return gdspy.current_library.cell_dict

#########HFSS_COMMANDS##################################################
#REQUIRES EPR PACKAGE TO FUNCTION PROPERLY#
    def set_oDesign(self, oDesign_): # pylint: disable=invalid-name
        '''
        Set the HFSS design, connects the Design_Planar object to the HFSS design via the Ansys Electronic
        Desktop API. Example using EPR package;
                self.set_oDesign(pyEPR_HFSS().pinfo.design)
        '''
        self.oDesign = oDesign_ # pylint: disable=invalid-name
        self.oModeler = None
        if not oDesign_ is None:
            self.oModeler = self.oDesign.modeler # pylint: disable=invalid-name

    def get_modeler(self):
        '''
        Return the hfss modeler object

        Returns oDesign and oModeler objects from pyEPR
        '''
        return (self.oDesign, self.oModeler)

    def hfss_set_global_params(self, gparams=None):
        '''
        Set up global properties of the design.
        Updated global params.

        Args:
            gparams (dict) : update global params with this dictionary.
        '''
        if not gparams:
            gparams = {}

        self.params.globals.update(gparams)
        gparams = self.params.globals

        _, modeler = self.get_modeler()

        import pyEPR
        units = gparams.get('global_units', 'mm')
        modeler.set_units(units)
        pyEPR.hfss.LENGTH_UNIT_ASSUMED = units  # used in parse_units

        return self

    def update_variables(self, variables=None):
        '''
            Update variable in the design, as defined in the design object and
            applies them to the HFSS design.
        '''
        if variables is None:
            variables = self.params.variables
        else:
            self.params.variables.update(variables)

        design, _ = self.get_modeler() # pylint: disable=invalid-name
        if design:
            for key, val in self.params.variables.items():
                design.set_variable(key, val)

    def mesh_obj(self, rect_mesh, mesh_name, **kwargs):
        '''
        "RefineInside:="        , False,
        "Enabled:="             , True,
        "RestrictElem:="        , False,
        "NumMaxElem:="          , "1000",
        "RestrictLength:="      , True,
        "MaxLength:="           , "0.1mm"

        Example use:
        modeler.assign_mesh_length('mesh2', ["Q1_mesh"], MaxLength=0.1)'''
        assert isinstance(mesh_name, str)

        if not mesh_name in self._mesh_assign:
            self._mesh_assign[mesh_name] = Dict()
        self._mesh_assign[mesh_name] = self.oModeler.append_mesh(mesh_name,
                                                                 rect_mesh,
                                                                 self._mesh_assign[mesh_name],
                                                                 **kwargs)

    def draw_chips(self, chips=None):
        '''
            Draw the groundplane and substrate for each chip
            Then adds the bounding box as specified by the global params.
        '''
        if chips is None:
            chips = {}

        self.params.chips.update(chips)
        chips = self.params.chips

        for chip_name in self.params.chips.keys():
            if not chip_name == 'main':
                self.params.chips[chip_name].update(dict(
                    ground_plane='ground_plane_'+chip_name,
                    substrate='substrate'+chip_name
                ))

        # Draw each chip
        for chip_name, options in chips.items():
            func_draw = getattr(draw_functions, options['func_draw'])
            func_draw(self, options)

        # Bounding box
        func_draw_box = getattr(
            draw_functions, self.params.globals['func_draw_bounding_box'])
        func_draw_box(self, self.params.globals['bounding_box'])