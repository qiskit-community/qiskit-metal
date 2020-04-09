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

from ..._defaults import DEFAULT_OPTIONS
from ..base import BaseComponent
from ... import draw
#from copy import deepcopy
#from ...toolbox_python.attr_dict import Dict


class Rectangle(BaseComponent):
    """A single configurable square."""

    def make(self):
        # parse the options dictionary to floats
        p = self.parse_value(self.options)

        # create the geometry
        rect = draw.rectangle(p.width, p.height, p.pos_x, p.pos_y)
        rect = draw.rotate(rect, p.rotation)

        # add elements
        self.add_elements('poly', {'rectangle': rect}, subtract=p.subtract,
                          helper=p.helper, layer=p.layer, chip=p.chip)


DEFAULT_OPTIONS['Rectangle'] = dict(
    width='500um',
    height='300um',
    pos_x='0um',
    pos_y='0um',
    rotation='0',
    subtract='False',
    helper='False',
    chip='main',
    layer='1'
)
