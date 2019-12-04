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

from copy import deepcopy

from ... import Dict, draw
from ...config import DEFAULT_OPTIONS
from .Metal_Design_Base import Metal_Design_Base
from .Metal_Utility import is_component

DEFAULT_OPTIONS.update({
    'Design_Planar': Dict({
        ####################################################
        # PlanarDesign global paramters
        'globals': Dict({
            'bounding_box': [[0, 0],
                             [0, 0],
                             ['0.890mm', '0.900mm']],     # Absolute Offset; [[-x,x],[-y,y],[-z,z]], mainly for HFSS currently
            # funciton used to draw the bounding box, found in 'draw.functions.py'
            'func_draw_bounding_box': 'draw_bounding_box'
        }),

        ####################################################
        # Substrate chips
        #  Chip parameters. Currently required to have one primary chip with a
        # ground_plane named 'ground_plane' for easy compatibility with HFSS
        # draw_substrate currently found in 'draw.functions.py'
        'chips': Dict({
            'main': Dict({
                'func_draw': 'draw_substrate',
                **DEFAULT_OPTIONS['draw_substrate']
            })
        }),
    })
})


class Design_Planar(Metal_Design_Base):  # pylint: disable=invalid-name
    """
    Contains design definitions and has some utility functions.
    All Metal components on chip are tracked by this parent as well as their connectors.


    Keyword Arguments:
    ------------------------
        components {[Dict]} -- [Pass an components dictionary] (default: {None})
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
        components (Dict) : Dict of all Metal_Objects
        connectors (Dict) : Dict of all connectors associated with the Metal_Objects and
                        custom connectors
    """

    def __init__(self,
                 components=None,
                 connectors=None,
                 oDesign_=None,
                 design_parameters=None):
        if not design_parameters:
            design_parameters = {}

        super().__init__(components=components, connectors=connectors)

        self.params = deepcopy(DEFAULT_OPTIONS['Design_Planar'])

        for key in design_parameters:
            self.params[key].update(design_parameters.get(key, {}))

        # TODO: Remove this. Track these elsewhere in renderer maybe or
        self.track_objs = {
            'qubits': {},
            'cpw': {},
            'launchers': {}
        }

        # TODO: Move into renderer
        self._mesh_assign = Dict()  # internal dict used to append mesh ops and reassign

        self.variables.cpw_width = DEFAULT_OPTIONS.cpw.width
        self.set_oDesign(oDesign_)


#########FUNCTIONS##################################################

    def get_chip_size(self, chip_name=None):
        '''
        Gets the size of the chip in the options dictionary
        Takes options.chip
        '''
        if chip_name is None:
            chip_name = 'main'
        elif isinstance(chip_name, dict):
            # Passed options
            chip_name = chip_name['chip']
        elif isinstance(chip_name, str):
            chip_name = chip_name
        else:
            raise ValueError('Unexpected get_chip_size arguemtn type.\
                              Should be dict, None or string name of chip.')

        return self.parse_value(self.params.chips[chip_name]['size'])

    def get_chip_z(self, chip_name='main'):
        '''
        Returns the z axis location of the plane which this chip is located at. Default of '0'
        Only of interest if making multiple chips
        NEEDED
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

#########HFSS_COMMANDS##################################################
#REQUIRES EPR PACKAGE TO FUNCTION PROPERLY#
    def set_oDesign(self, oDesign_):  # pylint: disable=invalid-name
        '''
        Set the HFSS design, connects the Design_Planar object to the HFSS design via the Ansys Electronic
        Desktop API. Example using EPR package;
                self.set_oDesign(pyEPR_HFSS().pinfo.design)
        '''
        self.oDesign = oDesign_  # pylint: disable=invalid-name
        self.oModeler = None
        if not oDesign_ is None:
            self.oModeler = self.oDesign.modeler  # pylint: disable=invalid-name

    def get_modeler(self):
        '''
        Return the hfss modeler object

        Returns oDesign and oModeler components from pyEPR
        '''
        return (self.oDesign, self.oModeler)

    def hfss_set_global_params(self, gparams=None):
        '''
        Set up global properties of the design.
        Updated global params.

        TODO: Move to hfss render

        Args:
            gparams (dict) : update global params with this dictionary.
        '''
        if not gparams:
            gparams = {}

        self.params.globals.update(gparams)
        gparams = self.params.globals

        _, modeler = self.get_modeler()

        import pyEPR
        units = self.default

        if 1:
            modeler.set_units(units, rescale=False)
            # pyEPR.hfss.LENGTH_UNIT = units  # HFSS seems to assume meters form a script no matter what

        # ??
        pyEPR.hfss.LENGTH_UNIT_ASSUMED = units  # used in parse_value_hfss

        return self

    def update_variables(self, variables=None, do_hfss=True):
        '''
            Update variable in the design, as defined in the design object and
            applies them to the HFSS design.
        '''
        if variables is None:
            variables = self.variables
        else:
            self.variables.update(variables)

        if do_hfss:
            design, _ = self.get_modeler()  # pylint: disable=invalid-name
            if design:
                for key, val in self.variables.items():
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
            func_draw = getattr(draw.functions, options['func_draw'])
            func_draw(self, options)

        # Bounding box
        func_draw_box = getattr(
            draw.functions, self.params.globals['func_draw_bounding_box'])
        func_draw_box(self, self.params.globals['bounding_box'])
