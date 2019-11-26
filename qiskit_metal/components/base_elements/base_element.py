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
@date: 2019
"""
from copy import deepcopy

from shapely.geometry.base import BaseGeometry

from ...config import DEFAULTS
from ..base_components.base_component import BaseComponent


class BaseElement():

    __name_delimiter = '_'  # for creating a full name

    def __init__(self,
                 name: str,
                 geom: BaseGeometry,
                 parent: BaseComponent,
                 chip=None):

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

        self.chip = DEFAULTS.chip if chip is None else chip

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

    def duplicate(self):
        """
        Return a copy of the object.

        TODO:
        -Deep copy all the geometry objects.
        -Do not copy the parent etc.
        """
        raise NotImplementedError()

    def _create_default_render_geom(self):
        """
        Create the default self.render_geom from the registered renderers.
        """
        raise NotImplementedError()
        #render_geom = Dict()
        #return render_geom

    def _create_default_render_params(self):
        """
        Create the default self.render_geom from the registered renderers.
        """
        raise NotImplementedError()
        #render_params = Dict()
        #return render_params
