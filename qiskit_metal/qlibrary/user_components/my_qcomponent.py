# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import QComponent

from ... import config
if not config.is_building_docs():
    from qiskit_metal import is_true


class MyQComponent(QComponent):
    """
    This class is a template
	Use this class as a blueprint to put together for your components - have fun
    """

    # Edit these to define your own tempate options for creation
    # Default drawing options
    default_options = Dict(width='500um',
                           height='300um',
                           pos_x='0um',
                           pos_y='0um',
                           rotation='0',
                           layer='1')
    """Default drawing options"""

    # Name prefix of component, if user doesn't provide name
    component_metadata = Dict(short_name='component')
    """Component metadata"""

    def make(self):
        """Convert self.options into QGeometry."""

        p = self.parse_options()  # Parse the string options into numbers

        # EDIT HERE - Replace the following with your code
        # Create some raw geometry
        # Use autocompletion for the `draw.` module (use tab key)
        rect = draw.rectangle(p.width, p.height, p.pos_x, p.pos_y)
        rect = draw.rotate(rect, p.rotation)
        geom = {'my_polygon': rect}
        self.add_qgeometry('poly', geom, layer=p.layer, subtract=False)
