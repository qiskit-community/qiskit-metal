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

converted to v0.2: Thomas McConkey 2020-03-24
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
    con_line=Dict()
)

DEFAULT_OPTIONS['qubit.con_lines'] = Dict()

class BaseQubit(BaseComponent):
    # TODO
    pass

    '''
    Qubit base class. Use to subscript, not to generate directly.

    Has connection lines that can be added

    options_con_lines (Dict): None, provides easy way to pass connector lines
                            which merely update self.options.con_lines

    Default Options:
    --------------------------
    DEFAULT_OPTIONS[class_name]
    DEFAULT_OPTIONS[class_name+'.con_line'] : for individual connection lines
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
   

    def __init__(self, design, name, options=None, options_con_lines=None,
                 _make=True):

        super().__init__(design, name, options=options)

        if options_con_lines:
            self.options.con_lines.update(options_con_lines)

        self._set_options_con_lines()

        self.components.con_lines = Dict()

        if _make:
            self.make()

     def _set_options_con_lines(self):
        class_name = type(self).__name__
        assert class_name+'.con_lines' in DEFAULT_OPTIONS, """When you define your
        custom qubit class please add a connector lines options default dicitonary name as
        DEFAULT_OPTIONS[class_name+'.con_lines'] where class_name is the the name of your
        custom class. This should speciy the default creation options for the connector. """

        for name in self.options.con_lines:
            my_options_con_lines = self.options.con_lines[name]
            self.options.con_lines[name] = deepcopy(
                Dict(DEFAULT_OPTIONS[class_name+'.con_lines']))
            self.options.con_lines[name].update(my_options_con_lines)