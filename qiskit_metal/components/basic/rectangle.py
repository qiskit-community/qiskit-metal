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


from copy import deepcopy
from ...toolbox_python.attr_dict import Dict
from ..._defaults import DEFAULT_OPTIONS
from ..base import BaseComponent
from ... import draw
# from copy import deepcopy
# from ...toolbox_python.attr_dict import Dict


class Rectangle(BaseComponent):
    """A single configurable square."""

    def make(self):
        p = self.p  # p for parsed parameters. Access to the parsed options.

        # create the geometry
        rect = draw.rectangle(p.width, p.height, p.pos_x, p.pos_y)
        rect = draw.rotate(rect, p.rotation)

        # add elements
        self.add_elements('poly', {'rectangle': rect}, subtract=p.subtract,
                          helper=p.helper, layer=p.layer, chip=p.chip)


class Rectangle_fromPAS(BaseComponent):
    """A single configurable square."""

    """The class will add default_rectangle class Dict to BaseComponent class before calling make.
    """
    default_rectangle = Dict(
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

    def __init__(self, design: 'DesignBase', name: str, rectangle: Dict = default_rectangle):
        """Will add the default rectangle values to DesignBase class, and call Rectangle.make().

        Arguments:
            design {DesignBase} -- DesignBase is the base class for Qiskit Metal Designs.
                                    A design is the most top-level object in all of Qiskit Metal.
            name {str} -- The type of component  to use as template.

        Keyword Arguments:
            rectangle {Dict} -- Initial key/values of Rectangle. (default: {default_rectangle})
        """
        
        self.rectangle = deepcopy(rectangle)

        design.default_generic['Rectangle_fromPAS'] = self.rectangle
        
        # We want to edit the design that is passed to init.
        # __init__ the BaseComponent class.
        # Specifically, choose when to execute the make method of Rectangle class
        super().__init__(design, name, make=False)
        self.make()

    def make(self):
        p = self.p  # p for parsed parameters. Access to the parsed options.

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
