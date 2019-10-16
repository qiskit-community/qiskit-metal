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
Base object. All Metal objects should be derived from this base class
Users making new custom objects should have this function be a parent of their new class to
insure compatibility with the package. 

2019-08-15
@author: Zlatko K. Minev
'''
# pylint: disable=invalid-name

from copy import deepcopy
from ...toolbox.attribute_dictionary import Dict
from ...config import DEFAULT_OPTIONS


class Metal_Object(): # pylint: disable=invalid-name
    r'''
    Base class for all Qiskit Metal objects .
    All Metal objects should be derived from this base class.

    Default options (self.options):
    --------------------
        chip  : specifies which chip the object is located on
        _hfss : options used for export to hfss
        _gds  : options used for gds export
    '''

    _img = 'Metal_Object.png'

    _gui_param_show = ['options', 'objects', 'objects_hfss'] # must be dicitonaries
    __i_am_metal__ = True

    def __init__(self, circ, name, options=None):
        from .Metal_Utility import is_metal_circuit

        assert is_metal_circuit(circ)

        self.circ = circ
        self.name = name

        # Options
        # Default blank option structure required
        # Should hfss and gds be part of base?
        self.options = Dict(
            _hfss=Dict(),            
            _gds=Dict(),
            chip='main',
        ) # maybe set these out in cofig or check for plugins, etc.
        # Default options applied
        class_name = type(self).__name__
        self.options.update(deepcopy(Dict(DEFAULT_OPTIONS[class_name])))
        # Custom passed options applied
        if options:
            self.options.update(options)

        # Objects - storage dictionaries
        self.objects = Dict() #container for shapely polygons
        self.objects_hfss = Dict()  # container for hfss objects
        self.objects_gds = Dict() #container for gds objects (not yet implemented)

        # Add self to circuit objects dictionary
        self.circ.objects[name] = self

    def __getitem__(self, key):
        '''
        Utiltiy funciton. Used in gui dictinary access.
        `key` should be in _gui_param_show
        '''
        return getattr(self, key)

    @property
    def OBJECTS(self): # pylint: disable=invalid-name
        '''
        returns object dictoanry containing all Metal Objects in the circuit
        '''
        return self.circ.OBJECTS

    def get_connectors(self):
        '''
        Returns the all defined connectors
        '''
        return self.circ.connectors

    def update_objects(self):
        """
        Calls the make function (check that this properly updates object dictionary)
        """
        self.make() # (check that this properly updates object dictionary)

    def make(self):
        '''
        References options (be they default or provided by the user) to make the shapely polygons
        This method should be overwritten by the childs make function.

        Should work in user unit space
        '''

    def hfss_draw(self):
        '''
        Draw in HFSS
        This method should be overwritten by the childs hfss_draw function.
        '''
    #Needs cleaning up and expanding. Should children classes have the gds_draw function internally?
    #Seperate? Leave as part of parent class?
    #Currently makes new cell for each object. Could be conflict between negative/positive polygon representation?
    def gds_draw(self, **kwargs):
        '''
        Export to GDS object

        Pass layer, etc in klwargs
        '''

        #TODO: Hanbdle as plugin
        import gdspy
        import shapely
        from ...draw_utility import Polygon, _func_obj_dict

        cell = gdspy.Cell(self.name)
        def my_func(me, *args, **kwargs):
            if isinstance(me, shapely.geometry.Polygon):
                poly = Polygon(me).coords_ext
                cell.add(gdspy.Polygon(poly, *args, **kwargs))

        kwargs = {**dict(layer=0),**kwargs}
        _func_obj_dict(my_func, self.objects, _override=False, **kwargs)

        return cell

    def get_chip_elevation(self):
        '''
        Returns the default chip elevation for the chip specified in
        self.options.chip
        '''
        return self.circ.get_substrate_z(self.options)
