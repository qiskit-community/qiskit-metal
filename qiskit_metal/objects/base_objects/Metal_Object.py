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
Base class for all Metal objects.

All Metal objects should be derived from this base class
Users making new custom objects should have this function be a parent of
their new class to insure compatibility with the package.

@date: 2019-08-15
@author: Zlatko K. Minev
'''
# pylint: disable=invalid-name

from copy import deepcopy

from .Metal_Utility import is_metal_circuit
from ...toolbox.attribute_dictionary import Dict
from ...config import DEFAULT_OPTIONS


DEFAULT_OPTIONS['Metal_Object'] = Dict(
    chip='main'
)


class Metal_Object():  # pylint: disable=invalid-name
    r'''
    Base class for all Qiskit Metal objects.

    All Metal objects should be derived from this base class.

    Creation Attributes:
    --------------------
        design () :

    Default options (Metal_Object.options):
    --------------------
        chip  : specifies which chip the object is located on
        _hfss : options used for export to hfss
        _gds  : options used for gds export

    Internals:
    ------------------
        _options_inherit : Inherit options from functions or objects that are called in the options dictionary.
            Used in the creation of a default options for the object.
        _img (str) : Name of the image to display in the GUI toolbar. Save to `qiskit_metal/_gui/_imgs`
        _gui_param_show (list) : Let's the gui know which Dict attributed of the object to show.
            These must be Dict.
    '''

    # Image to display in the GUI toolbar
    _img = 'Metal_Object.png'

    # must be dictionaries
    _gui_param_show = ['options', 'objects', 'objects_hfss']

    # Dummy attribute used to check if object is indeed Metal.
    # `isinstance` fails with module reloading.
    __i_am_metal__ = True

    # Inherit options from functions or objects that are called in the options dictionary
    _options_inherit = {}

    def __init__(self, design, name, options=None):

        assert is_metal_circuit(
            design), "Error you did not pass in a valid Metal Design object as a parent of this component."

        self.circ = design
        self.name = name

        self.options = self.create_default_options()

        if options:
            self.options.update(options)

        # Objects - storage dictionaries
        self.objects = Dict()  # container for shapely polygons
        self.objects_hfss = Dict()  # container for hfss objects
        self.objects_gds = Dict()  # container for gds objects (not yet implemented)

        # Add self to circuit objects dictionary
        self.circ.objects[name] = self

    @classmethod
    def create_default_options(cls):
        """
        Creates default options for the Metal Object class required for the class
        to function; i.e., be created, made, and rendered. Provides the blank option
        structure required.

        The options can be extended by plugins, such as renderers
        """

        # Every object should posses there
        options = deepcopy(DEFAULT_OPTIONS['Metal_Object'])

        # Specific object default options
        default_options = Dict(DEFAULT_OPTIONS[cls.__name__])
        options.update(deepcopy(default_options))

        # Specific object sub-options
        for key, value in cls._options_inherit.items():
            options[key] = deepcopy(
                Dict(DEFAULT_OPTIONS[value])
            )

        # Plugin extensiosn
        options._hfss = Dict()
        options._gds = Dict()

        return options

    def __getitem__(self, key):
        '''
        Utiltiy funciton. Used in gui dictinary access.
        `key` should be in _gui_param_show
        '''
        return getattr(self, key)

    @property
    def OBJECTS(self):  # pylint: disable=invalid-name
        '''
        returns object dictionary containing all Metal Objects in the circuit
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
        self.make()  # (check that this properly updates object dictionary)

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
    # Needs cleaning up and expanding. Should children classes have the gds_draw function internally?
    # Seperate? Leave as part of parent class?
    # Currently makes new cell for each object. Could be conflict between negative/positive polygon representation?

    def gds_draw(self, **kwargs):
        '''
        Export to GDS object

        Pass layer, etc in klwargs
        '''

        # TODO: Hanbdle as plugin
        import gdspy
        import shapely
        from ...draw_utility import Polygon, _func_obj_dict

        cell = gdspy.Cell(self.name)

        def my_func(me, *args, **kwargs):
            if isinstance(me, shapely.geometry.Polygon):
                poly = Polygon(me).coords_ext
                cell.add(gdspy.Polygon(poly, *args, **kwargs))

        kwargs = {**dict(layer=0), **kwargs}
        _func_obj_dict(my_func, self.objects, _override=False, **kwargs)

        return cell

    def get_chip_elevation(self):
        '''
        Returns the default chip elevation for the chip specified in
        self.options.chip
        '''
        return self.circ.get_substrate_z(self.options)
