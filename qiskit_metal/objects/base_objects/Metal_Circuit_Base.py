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
Base class for circuit type objects in Qiskit Metal.

This should be thought of as the 'package' level of the system. Aspects
such as gemoetries of your package cavity, 3D vs. planar or multiple chips.

Default use should be Metal_Circuit_Planar, which is a child of Metal_Circuit_Base.
Any alternative systems should be made as a child of Metal_Circuit_Base.

@date: 2019
@author: Zlatko K. Minev
Updated 2019/09/25 - Thomas McConkey
'''
# pylint: disable=invalid-name

import numpy as np
from ...toolbox.attribute_dictionary import Dict
from ...config import DEFAULT, DEFAULT_OPTIONS
from ...draw_functions import draw_objs, LineString
from ...backend.import_export import save_metal#, load_metal
from .Metal_Utility import is_metal_object



class Metal_Circuit_Base(): # pylint: disable=invalid-name
    '''
    Base class for circuit type objects in Qiskit Metal.
    All circuits should be derived from this base class.

    Key properties:
    ----------------------
        objects (Dict) : Dict of all Metal_Objects
        connectors (Dict) : Dict of all connectors associated with
                            the Metal_Objects and custom connectors

    @date: 2019
    @author: Zlatko K. Minev
    '''
    __i_am_metal_circuit__ = True


#########INITIALIZATION##################################################
    def __init__(self,
                 objects = None,
                 connectors = None,
                 logger = None):

        self._OBJECTS = Dict() if objects is None else objects
        self._connectors =  Dict() if connectors is None else connectors

        # handy in saving and keeping everyting referenced in one object
        self._DEFAULT = DEFAULT
        self._DEFAULT_OPTIONS = DEFAULT_OPTIONS

        if logger is None:
            from ... import logger
            self.logger = logger

#########PROPERTIES##################################################
    ###OBJECT REPORTING
    @property
    def OBJECTS(self):
        '''
        Returns Dict object that keeps track of all Metal objects in the circuit
        '''
        return self._OBJECTS

    @property
    def objects(self):
        '''
        Returns Dict object that keeps track of all Metal objects in the circuit
        '''
        return self._OBJECTS

    ###CONNECTOR REPORTING
    @property
    def connectors(self):
        '''
        Return the Dict object that keeps track of all connectors in the circuit.
        '''
        return self._connectors

#########COMMANDS##################################################
    def reset_all_connectors(self):
        '''
        Delete all connectors in the circuit.
        '''
        self.connectors.clear()
        return self.connectors

    def reset_all_objects(self):
        '''
        Resets the OBJECTS dictionary
        '''
        self._OBJECTS.clear()
        return self._OBJECTS

    def reset_all_metal(self):
        '''
        Removes the metal device
        '''
        self.reset_all_objects()
        self.reset_all_connectors()
        return self


    clear_all_objects = reset_all_objects

    def __getitem__(self, key):
        return getattr(self, key)

#########DRAWING##################################################
    def plot_connectors(self, ax=None):
        '''
        Plots all connectors on the active axes. Draws the 1D line that
        represents the "port" of a connector point. These are referenced for smart placement
         of Metal objects, such as when using functions like Metal_CPW_Connect.
        '''
        if ax is None:
            import matplotlib.pyplot as plt
            ax = plt.gca()

        for name, conn in self.connectors.items():
            line = LineString(conn.points)

            draw_objs(line, ax=ax, kw=dict(lw=2,c='r'))

            ax.annotate(name, xy=conn.pos[:2], xytext=conn.pos +\
                        np.array(DEFAULT.annots.circ_connectors_ofst),\
                        **DEFAULT.annots.circ_connectors)

    def make_all_objects(self):
        """
        Remakes all objects with their current parameters. Easy way
        """
        #self.logger.debug('Circuit: Making all objects')
        for name, obj in self.objects.items(): # pylint: disable=unused-variable
            if is_metal_object(obj):
                #self.logger.debug(f' Making {name}')
                obj.make()

    def save_circuit(self, path):
        """Save the circuit as a pickled python object.
        Equivalent to
        ```python
            save_metal(r'C:/my-circuit.metal',circ)
        ```

        Arguments:
            path {[string]} -- [path to save file]
        """
        save_metal(path, self)
