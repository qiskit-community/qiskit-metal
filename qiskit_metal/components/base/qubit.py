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

from copy import deepcopy
from ...toolbox_python.attr_dict import Dict
from .base import QComponent

class BaseQubit(QComponent):
    '''
    Qubit base class. Use to subscript, not to generate directly.

    Has connection lines that can be added

    options_con_lines (Dict): None, provides easy way to pass connector lines
                            which merely update self.options.con_lines

    Default Options:
    --------------------------
    default_options
    ._default_con_lines : the default values for the (if any) connection lines of the
        qubit.
    .con_lines : the dictionary which contains all active connection lines for the qubit.
        The structure should follow the format of .con_lines = dict{name_of_con_line=dict{},
        name_of_con_line2 = dict{value1 = X,value2 = Y...},...etc.}

        When you define your custom qubit class please add a connector options default
        dicitonary names as described above.


    GUI interfaceing
    ---------------------------
        _img : set the name of the file such as 'Metal_Object.png'. YOu must place this
                file in the qiskit_metal._gui._imgs diretory
    '''

    _img = 'Metal_Qubit.png'
    default_options = Dict(
        pos_x='0um',
        pos_y='0um',
        con_lines=Dict(),
        _default_con_lines=Dict()
    )

    def __init__(self, design, name, options=None, options_con_lines=None,
                 make=True):

        super().__init__(design, name, options=options, make=False)

        if options_con_lines:
            self.options.con_lines.update(options_con_lines)

        self._set_options_con_lines()

        if make:
            self.do_make()

    def _set_options_con_lines(self):
        #class_name = type(self).__name__
        assert '_default_con_lines' in self.design.template_options[self.class_name], f"""When
        you define your custom qubit class please add a connector lines options default
        dicitonary name as default_options['_default_con_lines']. This should speciy the default
        creation options for the connector. """

        del self.options._default_con_lines #Not sure if it best to remove it from options to keep
        #the self.options cleaner or not, since the options currently copies in the template. This is
        #potential source of bugs in the future
        for name in self.options.con_lines:
            my_options_con_lines = self.options.con_lines[name]
            self.options.con_lines[name] = deepcopy(
                self.design.template_options[self.class_name]['_default_con_lines'])
            self.options.con_lines[name].update(my_options_con_lines)

