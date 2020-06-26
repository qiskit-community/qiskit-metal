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
import functools
import inspect
import logging
from typing import TYPE_CHECKING, Union, List, Dict as Dict_

import pandas as pd
from geopandas import GeoSeries, GeoDataFrame

from .. import Dict
#from ..config import DEFAULT
from ..draw import BaseGeometry
from ..toolbox_python.utility_functions import data_frame_empty_typed

if TYPE_CHECKING:
    from ..components.base import QComponent
    from ..designs import QDesign

__all__ = ['is_element_table', 'QElementTables']  # , 'ElementTypes']

# from collections import OrderedDict
# dict are oreder in Python 3.6+ by default, this is jsut in case for backward compatability

# class ElementTypes:
#     """
#     Types of elements
#         positive : Elements that are positive mask
#         negative : Elements that will be subtracted from teh chip ground plane
#         helper   : Elements that are only used in a helper capacity,
#                    such as labels or mesh rectangles
#     """
#     positive = 0
#     negative = 1
#     helper   = 2


def is_element_table(obj):
    """Check if an object is a Metal BaseElementTable, i.e., an instance of
     `QElementTables`.

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
# Dicitonary that specifies the column names of various element tables.
#

# TODO: implement data types in construction of tables?
# TODO: when i copy over the table and manipualt ehtmee
# i seem to loose the assignments to bool etc.

ELEMENT_COLUMNS = dict(

    ################################################
    # DO NOT MODIFY THE base DICITONARY.
    # This is for Metal API use only.
    # To add a new element type, add a new key below.
    base=dict(
        component=str,  # Unique ID of the component to which the element belongs
        name=str,  # name of the element
        geometry=object,  # shapely object
        layer=int,  # gds type of layer
        subtract=bool,  # do we subtract from the groun place of the chip
        helper=bool,  # helper or not
        chip=str,  # chip name
        # type=str,  # metal, helper
        __renderers__=dict(
            # ADD specific renderers here, all renderes must register here.
            # hfss = dict( ... ) # pick names as hfss_name
            # hfss=dict(
            #     boundaray_name=str,
            #     material=str,
            #     perfectE=bool
            # ),
            # gds=dict(
            #     type=str,
            #     color=str,
            # )
        )
    ),


    ################################################
    # Specifies a path, such as a CPW.
    # Ideas: chamfer
    path=dict(
        width=float,
        fillet=object,  # TODO: not decided yet how to represent this
        __renderers__=dict(

        )
    ),

    ################################################
    # Specifies a polygon
    # Ideas: chamfer
    poly=dict(
        fillet=object,  # TODO: not decided yet how to represent this
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
TRUE_BOOLS = [True, 'True', 'true', 'Yes', 'yes', '1', 1]


class QElementTables(object):
    """Class to create, store, and handle element tables.

    A regular user would not need to create tables themselves.
    This is handled automatically by the design creation and plugins.

    Structure
    --------
    A component, such as a qubit, is a collection of elements.
    For example, an element includes a rectangle, a cpw path, or a more general polygon.

    An element is a row in a table.

    All elements of a type (Path or Polygon, or otherwise) are stored in a
    single table of their element type.

    All elements of the same kind are stored in a table.
    A renderer has to know how to handle all types of elements in order to render them.

    For plugin developers
    --------
    In the followin, we provide an example that illustrates for plugin developers how
    to add custom elements and custom element properties. For example, we will add, for a renderer
    called hfss, a string property called 'boundary', a bool property called 'perfectE', and a property called 'material'.

    For plugin developers, example use:

        .. code-block:: python
            :linenos:
            :emphasize-lines: 4,6

        import qiskit_metal as metal

        design = metal.designs.DesignPlanar()
        design.elements = metal.QElementTables(design)

        design.elements['path'] # return the path table - give access to ..
        design.elements.table['path']

        # Define interfaces
        design.elements.get_component(
                component_name,
                element_name,
                columns=all or geom or list?) # get all elemetns for compoentns

        >>> component	name	geometry	layer	type	chip	subtract	fillet	color	width


    Now, if we want to add custom elements through two fake renderers called hfss and gds:

    .. code-block:: python
        :linenos:
        :emphasize-lines: 1-15

        metal.QElementTables.add_renderer_extension('hfss', dict(
            base=dict(
                boundary=str,
                perfectE=bool,
                material=str,
                )
            ))

        metal.QElementTables.add_renderer_extension('gds', dict(
            path=dict(
                color=str,
                pcell=bool,
                )
            ))

        design = metal.designs.DesignPlanar()
        elements = metal.QElementTables(design)

        elements.tables['path']
        >>> component	name	geometry	layer	type	chip	subtract	fillet	color	width	hfss_boundary	hfss_perfectE	hfss_material	gds_color	gds_pcell

    """

    # Dummy private attribute used to check if an instanciated object is
    # indeed a elemnt table class. The problem is that the `isinstance`
    # built-in method fails when this module is reloaded.
    # Used by `is_element` to check.
    __i_am_element_table__ = True

    # Table column names to use to create.
    # this dict should be updated by renderers.
    ELEMENT_COLUMNS = ELEMENT_COLUMNS

    # For creating names of columns of renderer properties
    name_delimiter = '_'

    def __init__(self, design: 'QDesign'):
        """
        The constructor for the `BaseElement` class.

        Attributes:
            table {Dict} -- This is a dictiomnary of the table names as keys
                and the pandas DataFrames as values. The values get overwritten
                very often. Do not use a fixed reference.
        """
        self._design = design

        self._tables = Dict()
        self.create_tables()

    @property
    def design(self) -> 'QDesign':
        '''Return a reference to the parent design object'''
        return self._design

    @property
    def logger(self) -> logging.Logger:
        return self._design.logger

    @property
    def tables(self) -> Dict_[str, GeoDataFrame]:
        """The dictionary of tables containing elements.

        Returns:
            Dict_[str, GeoDataFrame] -- The keys of this dictionary are
                                        also obtained from `self.get_element_types()`
        """
        return self._tables

    @classmethod
    def add_renderer_extension(cls, renderer_name: str, elements: dict):
        """Add renderer element extension to ELEMENT_COLUMNS.
        Called when the load function of a renderer is called.

        Arguments:
            renderer_name {str} -- name of renderer
            elements {dict} --  dict of dict. keys give element type names,
                                such as base, poly, path, etc.
        """

        # Make sure that the base and all other element kinds have this renderer registerd
        for element_key in cls.ELEMENT_COLUMNS:
            if not renderer_name in cls.ELEMENT_COLUMNS[element_key]['__renderers__']:
                cls.ELEMENT_COLUMNS[element_key]['__renderers__'][renderer_name] = dict(
                )

        # Now update the dicitonaries with all elements that the renderer may have
        for element_key, element_column_ext_dict in elements.items():

            # The element the render is specifying is not in the specified elements;
            # then add it. This shouldn't really happen.
            # The rest of the renderer dict keys in __renderers__  are missing for
            # the created type. Avoid doing, else hope it works.
            if not element_key in cls.ELEMENT_COLUMNS:
                cls.ELEMENT_COLUMNS[element_key] = dict(__renderers__=dict())

            # Now add elements
            cls.ELEMENT_COLUMNS[element_key]['__renderers__'][renderer_name].update(
                element_column_ext_dict)

    # could use weakref memorizaiton
    # https://stackoverflow.com/questions/33672412/python-functools-lru-cache-with-class-methods-release-object
    @classmethod
    def get_element_types(cls) -> List[str]:
        """Return the names of the available elements to create.
        This does not include 'base', but is rather such as poly and path.

        Returns:
            list(str) -- list of name in self.ELEMENT_COLUMNS
        """
        # TODO: I should probably make this a variable and memeorize, only change when elements are added and removed
        # can be slow for perofmance to look up eahc time and recalcualte, since may call this often
        names = list(cls.ELEMENT_COLUMNS.keys())
        names.remove('base')
        return names

    def create_tables(self):
        """
        Creates the default tables once. Populates the dict 'tables' of GeoDataFrame,
        each with columns corresponding to the types of elements defined in ELEMENT_COLUMNS.

        Should only be done once when a new design is created.
        """
        self.logger.debug('Creating Element Tables.')

        for table_name in self.get_element_types():
            # Create GeoDataFrame with correct columns and d types
            assert isinstance(table_name, str)
            assert table_name.isidentifier()

            # Get column names
            # Base names, add concrete names, then add renderer names

            # Base names
            columns_base = self.ELEMENT_COLUMNS['base'].copy()
            columns_base_renderers = columns_base.pop('__renderers__')

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
            for renderer_key in columns_base_renderers:
                columns.update(self._prepend_renderer_names(
                    table_name, renderer_key, columns_base_renderers))
                columns.update(self._prepend_renderer_names(
                    table_name, renderer_key, columns_concrete_renderer))

            # Validate -- Throws an error if not valid
            self._validate_column_dictionary(table_name, columns)

            # Create df with correct column names
            table = GeoDataFrame(data_frame_empty_typed(columns))
            table.name = table_name  # not used elsewhere

            # Assign
            self.tables[table_name] = table

    def _validate_column_dictionary(self, table_name: str,  column_dict: dict):
        """Validate
        A possible error here is if the user did not pass a valid data type
        This raises TypeError: data type '' not understood

        Throws an error if not valid.

        Arguments:
            table_name {str} -- Name of element table (e.g., 'poly')
            column_dict {dict} --
        """
        __pre = 'ERROR CREATING ELEMENT TABLE FOR DESIGN: \
            \n  ELEMENT_TABLE_NAME = {table_name}\
            \n  KEY                = {k} \
            \n  VALUE              = {v}\n '

        for k, v in column_dict.items():
            assert isinstance(k, str), __pre.format(**locals()) +\
                ' Key needs to be a string!'
            assert k.isidentifier(), __pre.format(**locals()) +\
                ' Key needs to be a valid string identifier!'
            assert inspect.isclass(v), __pre.format(**locals()) +\
                ' Value needs to be a class!'

    def get_rname(self, renderer_name: str, key: str) -> str:
        """
        Get name for renderer property

        Arguments:
            renderer_name {str} -- Name of the renderer
            key {str} -- [description]

        Returns:
            str -- The unique named used as a column in the table
        """
        return renderer_name + self.name_delimiter + key

    def _prepend_renderer_names(self, table_name: str, renderer_key: str, rdict: dict):
        return {self.get_rname(renderer_key, k): v
                for k, v in rdict.get(renderer_key, {}).items()}

    def add_elements(self,
                     kind: str,
                     component_name: str,
                     geometry: dict,
                     subtract: bool = False,
                     helper: bool = False,
                     layer: Union[int, str] = 1,  # chip will be here
                     chip: str = 'main',
                     **other_options):
        """Main interface to add names

        Arguments:
            kind {str} -- Must be in get_element_types ('path', 'poly', etc.)
            geometry {dict} -- Dict of shapely geomety

        Keyword Arguments:
            subtract {bool} -- [description] (default: {False})
            helper {bool} -- [description] (default: {False})
            layer {Union[int, str]} -- [description] (default: {0})
            chip {str} -- Chip name (dafult: 'main')
            **other_options
        """
        # TODO: Add unit test

        # ensure correct types
        if not isinstance(subtract, bool):
            subtract = subtract in TRUE_BOOLS
        if not isinstance(helper, bool):
            helper = helper in TRUE_BOOLS

        if not (kind in self.get_element_types()):
            self.logger.error(f'Creator user error: Unkown element kind=`{kind}`'
                              f'Kind must be in {self.get_element_types()}. This failed for component'
                              f'name = `{component_name}`.\n'
                              f' The call was with subtract={subtract} and helper={helper}'
                              f' and layer={layer}, and options={other_options}')

        # Create options
        options = dict(component=component_name, subtract=subtract,
                       helper=helper, layer=int(layer), chip=chip, **other_options)

        table = self.tables[kind]

        # assert that all names in options are in table columns!
        # mauybe check
        df = GeoDataFrame.from_dict(
            geometry, orient='index', columns=['geometry'])
        df.index.name = 'name'
        df = df.reset_index()

        df = df.assign(**options)

        # Set new table. Unfortuanly, this creates a new instance.
        self.tables[kind] = table.append(df, sort=False, ignore_index=True)
        # concat([table,df], axis=0, join='outer', ignore_index=True,sort=False,
        #          verify_integrity=False, copy=False)

    def clear_all_tables(self):
        """Clear all the internal tables and all else.
        Use when clearing a design and starting from scratch.
        """
        self.tables.clear()
        self.create_tables()  # remake all tables

    def delete_component(self, name: str):
        """Delete component by name

        Arguments:
            name {str} -- Name of component (case sensitive)
        """
        # TODO: Add unit test
        # TODO: is this the best way to do this, or is there a faster way?
        comp_id = self.design.components[name].id
        for table_name in self.tables:
            df = self.tables[table_name]
            self.tables[table_name] = df[df['component'] != comp_id]

    def delete_component_id(self, component_id: int):
        """Drop the components within the elements.tables

        Args:
            component_id (int): Unique number to describe the component.
        """
        for table_name in self.tables:
            df_table_name = self.tables[table_name]
            #self.tables[table_name] = df_table_name.drop(df_table_name[df_table_name['component'] == component_id].index)
            self.tables[table_name] = df_table_name[df_table_name['component']
                                                    != component_id]

    def get_component(self, name: str, table_name: str = 'all') -> Union[GeoDataFrame, Dict_[str, GeoDataFrame]]:
        """Return the table for just a given component.
        If all, returns a dictionary with kets as table names and tables of components as values.

        Arguments:
            name {str} -- Name of component (case sensitive) (default: 'all')

        Keyword Arguments:
            table_name {str} -- Element table name ('poly', 'path', etc.) (default: {'all'})

        Returns:
            Union[GeoDataFrame, Dict_[str, GeoDataFrame]] -- Either a GeoDataFrame or a dict or GeoDataFrame.

        Example use:
            table = pd.concat(elements.get_component('Q1')) # , axis=0
        """

        if table_name == 'all':
            tables = {}
            for table_name in self.get_element_types():
                tables[table_name] = self.get_component(name, table_name)
            return tables
        else:
            df = self.tables[table_name]
            comp_id = self.design.components[name].id
            return df[df.component == comp_id]

    def get_component_bounds(self, name: str):
        """Returns a tuple containing minx, miny, maxx, maxy values
        for the bounds of the component as a whole.

        Arguments:
            name {str} -- component name
        """
        return self.get_component_geometry(name).total_bounds

    def rename_component(self, component_id: int, new_name: str):
        """Rename component by ID (integer) cast to string format.

        Arguments:
            name (int) -- Name of component (case sensitive)
            new_name (str) -- The new name of the component (case sensitive)
        """
        component_int_id = int(component_id)
        # TODO: is this the best way to do this, or is there a faster way?
        for table_name in self.tables:
            table = self.tables[table_name]
            table.component[table.component == component_int_id] = new_name

    def get_component_geometry_list(self, name: str, table_name: str = 'all') -> List[BaseGeometry]:
        """Return just the bare element geometry (shapely geometry objects) as a list, for the
        selected component.

        Arguments:
            name {str} -- Name of component (case sensitive)
            table_name {str} -- Element type ('poly', 'path', etc.).
                                Can also be 'all' to return all. This is the default.
        """
        if table_name == 'all':
            elements = []
            for table in self.get_element_types():
                elements += self.get_component_geometry_list(name, table)

        else:
            table = self.tables[table_name]
            comp_id = self.design.components[name].id
            elements = table.geometry[table.component == comp_id].to_list()

        return elements

    def get_component_geometry(self, name: str) -> GeoSeries:
        """
        Arguments:
            name {str} -- Name of component (case sensitive)

        Returns:
            GeoSeries -- [description]
        """
        comp_id = self.design.components[name].id
        elements = {}
        for table_name in self.get_element_types():
            table = self.tables[table_name]
            elements[table_name] = table.geometry[table.component == comp_id]
        return pd.concat(elements)

    def get_component_geometry_dict(self, name: str, table_name: str = 'all') -> List[BaseGeometry]:
        """Return just the bare element geometry (shapely geometry objects) as a dict,
           with key being the names of the elements and the values as the shapely geometry,
           for the selected component.

        Arguments:
            name {str} -- Name of component (case sensitive)
            table_name {str} -- Element type ('poly', 'path', etc.)
        """
        if table_name == 'all':
            elements = Dict()
            for table in self.get_element_types():
                elements[table] = self.get_component_geometry_list(name, table)
            return elements  # return pd.concat(elements, axis=0)

        else:
            table = self.tables[table_name]

            # mask the rows nad get only 2 columns
            comp_id = self.design.components[name].id
            df_comp_id = table.loc[table.component ==
                                   comp_id, ['name', 'geometry']]
            df_geometry = df_comp_id.geometry
            df_geometry.index = df_comp_id.name
            return df_geometry.to_dict()

    def check_element_type(self, table_name: str, log_issue: bool = True) -> bool:
        """Check if the name `table_name` is in the element tables.

        Arguments:
            table_name {str} -- Element type ('poly', 'path', etc.) or 'all'

        Keyword Arguments:
            log_issue {bool} -- Throw an erro in the log if name missing  (default: {True})

        Returns:
            bool -- True if the name is valid, else False
        """
        if not table_name in self.get_element_types() or table_name in 'all':
            if log_issue:
                self.logger.error(
                    f'Element Tables: Tried to access non-existing element table: `{table_name}`')
            return False
        else:
            return True
