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

"""
This is the main module that defines what an element is in Qiskit Metal.
See the docstring of BaseElement
    >> ?BaseElement

@author: Zlatko Minev, Thomas McConekey, ... (IBM)
@date: 2019
"""

#from copy import deepcopy

import pandas as pd
from shapely.geometry.base import BaseGeometry
# from collections import OrderedDict # dict are oreder in Python 3.6+ by default, this is jsut in case for backward compatability

from .. import Dict
from ..config import DEFAULT
from ..components.base import BaseComponent
from ..toolbox_python.utility_functions import data_frame_empty_typed

__all__ = ['is_element_table', 'ElementTables']


def is_element_table(obj):
    """Check if an object is a Metal BaseElementTable, i.e., an instance of
     `ElementTables`.

    The problem is that the `isinstance` built-in method fails
    when this module is reloaded.

    Arguments:
        obj {[object]} -- Test this object

    Returns:
        [bool] -- True if is a Metal element
    """
    if isinstance(obj, Dict):
        return False

    return hasattr(obj, '__i_am_element_table__')


#############################################################################
#
# Dicitonary that specifies the structue of the elment tables
#

ELEMENT_COLUMNS = dict(

    ################################################
    # DO NOT MODIFY THE base DICITONARY.
    # This is for Metal API use only.
    # To add a new element type, add a new key below.
    base=dict(
        component=str,  # name of the component to which the element belongs
        name=str,  # name of the element
        geometry=object,
        layer=int,
        type=str,  # metal, helper
        chip=str,  # is this redundant with layer?
        subtract=bool,
        fillet=object,
        color='',  # none by default, can overwrite, not used by all renderers
        __renderers__=dict(
            # ADD specific renderers here, all renderes must register here.
            # hfss = dict( ... ) # pick names as hfss_name
        )
    ),


    ################################################
    # Specifies a path, such as a CPW.
    path=dict(
        width=float,
        __renderers__=dict(
        )
    ),

    ################################################
    # Specifies a polygon
    poly=dict(
        __renderers__=dict(
        )
    ),

    ################################################
    # Specifies a curved object, such as a circle
    # Not yet implemented
    # curved = dict(
    # __renderers__= dict(
    # )
    # )
)


#############################################################################
#
# Class to create, store, and handle element tables.
#

class ElementTables():
    """Class to create, store, and handle element tables.

    Metal class for the table of basic geometric objects: `elements`.
    A component, such as a qubit, is a collection of elements.
    For example, an element includes a rectangle, a cpw path, or a more general polygon.

    An element is a row in a table.

    All elements of a type (Path or Polygon, or otherwise) are stored in a
    single table of their element type.

    All elements of the same kind are stored in a table.
    A renderer has to know how to handle all types of elements in order to render them.
    """

    # Dummy private attribute used to check if an instanciated object is
    # indeed a BaseComponent class. The problem is that the `isinstance`
    # built-in method fails when this module is reloaded.
    # Used by `is_element` to check.
    __i_am_element_table__ = True

    # Table column names to use to create.
    # this dict should be updated by renderers.
    ELEMENT_COLUMNS = ELEMENT_COLUMNS

    # For creating names of columns of renderer properties
    name_delimiter = '_'

    @classmethod
    def add_renderer_extension(cls, renderer_name: str, elements: dict):
        """Add renderer element extension to ELEMENT_COLUMNS.
        Called when the load function of a renderer is called.

        Arguments:
            renderer_name {str} -- name of renderer
            elements {dict} --  dict of dict. keys give element type names,
                                such as base, poly, path, etc.
        """
        for element_type, element_column_ext_dict in elements.items():
            if not element_type in cls.ELEMENT_COLUMNS:
                cls.ELEMENT_COLUMNS[element_type] = dict(__renderers__=dict())
            cls.ELEMENT_COLUMNS[element_type]['__renderers__'].update(
                element_column_ext_dict)

    @classmethod
    def get_element_types(cls):
        """Return the names of the available elements to create.
        This does not include 'base', but is rather such as poly and path.

        Returns:
            list(str) -- list of name in self.ELEMENT_COLUMNS
        """
        names = list(cls.ELEMENT_COLUMNS.keys())
        names.remove('base')
        return names

    @property
    def tables(self):
        """Read-only dictionary of tables with keys self.get_element_types()

        Returns:
            dict of pandas dataframes

        """
        return self._tables

    def __init__(self, design):
        """The constructor for the `BaseElement` class.

        """
        self.design = design

        self._tables = Dict()
        self.create_tables()

    def create_tables(self):
        """
        Creates the default tables once. Populates the dict 'tables' of DataFrames,
        each with columns corresponding to the types of elements defined in ELEMENT_COLUMNS.

        Should only be done once when a new design is created.
        """
        for table_name in self.get_element_types():
            # Create dataframe with correct columns and d types
            assert isinstance(table_name, str)
            assert table_name.isidentifier()

            # Get column names
            # Base names, add concrete names, then add renderer names

            # Base names
            columns_base = self.ELEMENT_COLUMNS['base'].copy()
            columns_base_renderers = columns.pop('__renderers__')

            # Concrete names
            columns_concrete = self.ELEMENT_COLUMNS[table_name].copy()
            columns_concrete_renderer = columns_concrete.pop('__renderers__')

            assert isinstance(columns_base_renderers, dict) and\
                isinstance(columns_concrete_renderer, dict),\
                "Please make sure that all elements types have __renderers__\
                     which is a dictionary."

            # Combine all base names and renderer names
            columns = columns_base
            columns.update(columns_concrete)
            # add renderer columns: base and then concrete
            columns.update(self._prepend_renderer_names(
                table_name, columns_base_renderers))
            columns.update(self._prepend_renderer_names(
                table_name, columns_concrete_renderer))

            # Create df with correct column names
            table = data_frame_empty_typed(columns)
            table.name = table_name

            # Assign
            self.tables[table_name] = table

    def _prepend_renderer_names(self, table_name: str, rdict: dict):
        return {table_name + self.name_delimiter + k: v for k, v in rdict.items()}

    # def get_

        # """The constructor for the `BaseElement` class.

        # Arguments:
        #     name {str} -- Name of the element used to render, if needed. A simple string.
        #     geom {BaseGeometry} -- A 2D `shapely` geometry. `LineString` or `Polygon`.
        #     parent {BaseComponent} -- Parent class: a Metal BaseComponent

        # Keyword Arguments:
        #     chip {str} -- Which chip is the element on.
        #                   (default: {config.DEFAULT.chip, typically set to 'main'})
        #     fillet {float, str, or tuple} -- float or string of the radius of the fillet.
        #                   Can also pass a tuple of (raidus, [list of vertecies to fillet])
        #                   (default: None - no fillet)
        #     subtract {bool} -- subtract from ground plane of `chip` or not. There is one
        #                     ground plane  per chip.

        # Internal data structure:
        #     name {str} -- Name of the element used to render, if needed. A simple string.
        #     geom {BaseGeometry} -- Shapely BaseGeometry that defines the element properties.
        #     parent {BaseComponent} -- Parent class: a Metal BaseComponent
        #     chip {str} -- String name (used as pointer) to chip on which the element is rendered.
        #                  By  default config.DEFAULT.chip, typically set to 'main'}

        # Internal data structure related to renderers:

        #     render_geom {Dict} -- Geometry rendered by the render that is associated with
        #                     this element can be stored here. This is a dictonary of dictionaries.
        #                     Each key is a renderer name. The inner dictionary contains the
        #                     (name, object) pairs.
        #                     Default is created by method `_create_default_render_geom`.

        #     render_params {Dict} -- Dictionary of default params used in a renderer to render
        #                 this parameter.
        #                 Each key is a renderer name.
        #                 The value is a dictionary of (key, value) settings for the renderer.
        #                 Default is created by method `_create_default_render_geom`.
        # """

        # # Type checks
        # assert isinstance(name, str),\
        #     "Please use only strings as names for elements."
        # assert isinstance(geom, BaseGeometry),\
        #     "You must pass a shapely Polygon or LineString or\
        #      BaseGeometry objects to `geom` in oroder to create an element."
        # assert isinstance(parent, BaseGeometry),\
        #     "You must pass in only BaseComponent inherited objects to parent for elements."

        # # Arguments
        # self.name = name
        # self.geom = geom
        # self.parent = parent

        # # Different elements within the same components can be on different chips
        # self.chip = DEFAULT.chip if chip is None else chip

        # self.fillet = fillet

        # # Subtract from ground of not. bool. one ground per chip
        # self.subtract = subtract

        # # Renderer related
        # self.render_geom = self._create_default_render_geom()
        # self.render_params = self._create_default_render_params()

    # @property
    # def z_value(self):
    #     """Return the z elevation of the chip on which the element is siting
    #     """
    #     return self.parent.design.get_chip_z(self.chip)

    # @property
    # def full_name(self):
    #     """Return full name of the object, such as Q1_connector_pad
    #     Where the parent name is Q1 and the object name is "connector_pad"

    #     Returns:
    #         string
    #     """
    #     return self.parent.name + self.__name_delimiter + self.name

    # def _create_default_render_geom(self):
    #     """
    #     Create the default self.render_geom from the registered renderers.
    #     Sets up dictionary hierarchy.
    #     """
    #     raise NotImplementedError()
    #     #render_geom = Dict()
    #     # return render_geom

    # def _create_default_render_params(self):
    #     """
    #     Create the default self.render_geom from the registered renderers.
    #     """
    #     raise NotImplementedError()
    #     #render_params = Dict()
    #     # return render_params
