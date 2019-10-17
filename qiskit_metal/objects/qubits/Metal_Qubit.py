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
@date: 2019
@author: Zlatko K Minev
'''
# pylint: disable=invalid-name

from copy import deepcopy
from ..base_objects.Metal_Object import Metal_Object, Dict
from ...config import DEFAULT_OPTIONS


###
# Setup default options
DEFAULT_OPTIONS['Metal_Qubit.connector'] = Dict()
DEFAULT_OPTIONS['Metal_Qubit'] = Dict(
    pos_x='0um',
    pos_y='0um',
    connectors=Dict(),
    _hfss=Dict(
        Lj='10nH',
        Cj=0,  # Warning - do not use non zero for pyEPR analysis at present, need to use upgrade
        _Rj=0,
    ),
    _gds=Dict()
)


class Metal_Qubit(Metal_Object):  # pylint: disable=invalid-name
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

        self.objects.connectors = Dict()

        if _make:
            self.make()

    def _set_options_connectors(self):
        class_name = type(self).__name__
        assert class_name+'.connectors' in DEFAULT_OPTIONS, """When you define your
        custom qubit class please add a connector options default dicitonary name as
        DEFAULT_OPTIONS[class_name+'.connectors'] where class_name is the the name of your
        custom class. This should speciy the default creation options for the connector. """

        for name in self.options.connectors:
            my_options_connector = self.options.connectors[name]
            self.options.connectors[name] = deepcopy(
                Dict(DEFAULT_OPTIONS[class_name+'.connector']))
            self.options.connectors[name].update(my_options_connector)
