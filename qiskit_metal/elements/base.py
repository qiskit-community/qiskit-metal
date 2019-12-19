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

from shapely.geometry.base import BaseGeometry

from .. import Dict
from ..config import DEFAULT
from ..components.base import BaseComponent

__all__ = ['is_element', 'BaseElement']


def is_element(obj):
    """Check if an object is a Metal BaseElement, i.e., an instance of
     `BaseElement`.

    The problem is that the `isinstance` built-in method fails
    when this module is reloaded.

    Arguments:
        obj {[object]} -- Test this object

    Returns:
        [bool] -- True if is a Metal element
    """
    if isinstance(obj, Dict):
        return False

    return hasattr(obj, '__i_am_element__')


class BaseElement():
    """Main Metal class for the basic geometric object: an `element`.
    A component, such as a qubit, is a collection of elements.
    For example, an element includes a rectangle, a cpw path, or a more general polygon.

    This is the base class, from which which all elements are dervied.
    A renderer has to know how to handle all types of elements in order to render them.
    """

    __name_delimiter = '_'  # for creating a full name

    # Dummy private attribute used to check if an instanciated object is
    # indeed a BaseComponent class. The problem is that the `isinstance`
    # built-in method fails when this module is reloaded.
    # Used by `is_element` to check.
    __i_am_element__ = True

    def __init__(self,
                 name: str,
                 geom: BaseGeometry,
                 parent: BaseComponent,
                 chip=None,
                 fillet=None,
                 subtract=False,
                 ):
        """The constructor for the `BaseElement` class.

        Arguments:
            name {str} -- Name of the element used to render, if needed. A simple string.
            geom {BaseGeometry} -- A 2D `shapely` geometry. `LineString` or `Polygon`.
            parent {BaseComponent} -- Parent class: a Metal BaseComponent

        Keyword Arguments:
            chip {str} -- Which chip is the element on.
                          (default: {config.DEFAULT.chip, typically set to 'main'})
            fillet {float, str, or tuple} -- float or string of the radius of the fillet.
                          Can also pass a tuple of (raidus, [list of vertecies to fillet])
                          (default: None - no fillet)
            subtract {bool} -- subtract from ground plane of `chip` or not. There is one
                            ground plane  per chip.

        Internal data structure:
            name {str} -- Name of the element used to render, if needed. A simple string.
            geom {BaseGeometry} -- Shapely BaseGeometry that defines the element properties.
            parent {BaseComponent} -- Parent class: a Metal BaseComponent
            chip {str} -- String name (used as pointer) to chip on which the element is rendered.
                         By  default config.DEFAULT.chip, typically set to 'main'}


        Internal data structure related to renderers:

            render_geom {Dict} -- Geometry rendered by the render that is associated with
                            this element can be stored here. This is a dictonary of dictionaries.
                            Each key is a renderer name. The inner dictionary contains the
                            (name, object) pairs.
                            Default is created by method `_create_default_render_geom`.

            render_params {Dict} -- Dictionary of default params used in a renderer to render
                        this parameter.
                        Each key is a renderer name.
                        The value is a dictionary of (key, value) settings for the renderer.
                        Default is created by method `_create_default_render_geom`.
        """

        # Type checks
        assert isinstance(name, str),\
            "Please use only strings as names for elements."
        assert isinstance(geom, BaseGeometry),\
            "You must pass a shapely Polygon or LineString or\
             BaseGeometry objects to `geom` in oroder to create an element."
        assert isinstance(parent, BaseGeometry),\
            "You must pass in only BaseComponent inherited objects to parent for elements."

        # Arguments
        self.name = name
        self.geom = geom
        self.parent = parent

        # Different elements within the same components can be on different chips
        self.chip = DEFAULT.chip if chip is None else chip

        self.fillet = fillet

        # Subtract from ground of not. bool. one ground per chip
        self.subtract = subtract

        # Renderer related
        self.render_geom = self._create_default_render_geom()
        self.render_params = self._create_default_render_params()

    @property
    def z_value(self):
        """Return the z elevation of the chip on which the element is siting
        """
        return self.parent.design.get_chip_z(self.chip)

    @property
    def full_name(self):
        """Return full name of the object, such as Q1_connector_pad
        Where the parent name is Q1 and the object name is "connector_pad"

        Returns:
            string
        """
        return self.parent.name + self.__name_delimiter + self.name

    def duplicate(self, new_name: str, overwrite: bool):
        """
        Return a copy of the object.

        TODO:
        -Deep copy all the geometry objects.
        -Do not copy the parent etc.

        Arguments:
            new_name {str} -- New component name
            overwrite {bool} -- If name exists, do we override?

        Raises:
            NotImplementedError: [description]
        """
        # check that new_name is not already defined in component
        # if overwrite then do overwite

        raise NotImplementedError()

    def _create_default_render_geom(self):
        """
        Create the default self.render_geom from the registered renderers.
        Sets up dictionary hierarchy.
        """
        raise NotImplementedError()
        #render_geom = Dict()
        # return render_geom

    def _create_default_render_params(self):
        """
        Create the default self.render_geom from the registered renderers.
        """
        raise NotImplementedError()
        #render_params = Dict()
        # return render_params
