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

"""File contains dictionary for Rectangle and Rectangle_fromPAS and their make().
"""


from ...toolbox_python.attr_dict import Dict
from ..base import BaseComponent
from ... import draw


class Rectangle(BaseComponent):
    """A single configurable square."""

    """The class will add default_options class Dict to BaseComponent class before calling make.
    """

    default_options = Dict(
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

    def make(self):
        p = self.p  # p for parsed parameters. Access to the parsed options.

        # create the geometry
        rect = draw.rectangle(p.width, p.height, p.pos_x, p.pos_y)
        rect = draw.rotate(rect, p.rotation)

        # add elements
        self.add_elements('poly', {'rectangle': rect}, subtract=p.subtract,
                          helper=p.helper, layer=p.layer, chip=p.chip)


class RectangleFromPAS(BaseComponent):
    """A single configurable square."""

    """The class will add default_options class Dict to BaseComponent class before calling make.
    """

    default_options = Dict(
        width='500um',
        height='300um',
        pos_x='0um',
        pos_y='0um',
        rotation='0',
        subtract='False',
        helper='False',
        chip='main',
        layer='1',
        FOR_TEST="Happy Days"
    )

    def make(self):
        p = self.p  # p for parsed parameters. Access to the parsed options.

        # create the geometry
        rect = draw.rectangle(p.width, p.height, p.pos_x, p.pos_y)
        rect = draw.rotate(rect, p.rotation)

        # add elements
        self.add_elements('poly', {'rectangle': rect}, subtract=p.subtract,
                          helper=p.helper, layer=p.layer, chip=p.chip)
