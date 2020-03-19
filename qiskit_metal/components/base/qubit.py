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
@author: Zlatko Minev, Thomas McConekey, ... (IBM)
@date: 2019
"""

from .base import BaseComponent
from ...toolbox_python.attr_dict import Dict
from copy import deepcopy
from ..._defaults import DEFAULT_OPTIONS, DEFAULT


###
# Setup default options

DEFAULT_OPTIONS['qubit'] = Dict(
    pos_x='0um',
    pos_y='0um',
    connectors=Dict()
)

DEFAULT_OPTIONS['qubit.connector'] = Dict()

class BaseQubit(BaseComponent):
    # TODO
    pass

    '''
    Qubit base class. Use to subscript, not to generate directly.

    Has connectors that can be added

    options_connectors (Dict): None, provides easy way to pass connectors
                            which merely update self.options.connectors

    Default Options:
    --------------------------
    DEFAULT_OPTIONS[class_name]
    DEFAULT_OPTIONS[class_name+'.connector'] : for individual connectors
        When you define your
        custom qubit class please add a connector options default dicitonary name as
        DEFAULT_OPTIONS[class_name+'.connector'] where class_name is the the name of your
        custom class. This should speciy the default creation options for the connector.


    GUI interfaceing
    ---------------------------
        _img : set the name of the file such as 'Metal_Object.png'. YOu must place this
                file in the qiskit_metal._gui._imgs diretory
    '''

    _img = 'Metal_Qubit.png'
    #__gui_creation_args__ = ['options_connectors']

    def __init__(self, design, name, options=None, options_connectors=None,
                 _make=True):

        super().__init__(design, name, options=options)

        if options_connectors:
            self.options.connectors.update(options_connectors)

        self._set_options_connectors()

        self.components.connectors = Dict()

        if _make:
            self.make()