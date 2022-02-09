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
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround


class OpenToGroundCustom(OpenToGround):
    """A custom sample_shapes open to ground termination. Functions as a pin for auto drawing.

    Inherits `QComponent` and `OpenToGround` class.

    .. image::
        OpenToGround.png

    .. meta::
        Open to Ground

    Default Options:
        * width: '15um' -- The width of the 'cpw' terminating to ground (this is merely
          for the purpose of generating a value to pass to the pin)
        * gap: '8.733um' -- The gap of the 'cpw'
        * termination_gap: '6um' -- The length of dielectric from the end of the cpw center trace to the ground.

    Values (unless noted) are strings with units included, (e.g., '30um')
    """
    component_metadata = Dict(short_name='term', _qgeometry_table_poly='True')
    """Component metadata"""

    default_options = Dict(width='15um', gap='8.733um', termination_gap='6um')
    """Default connector options"""

    TOOLTIP = """A customized basic open to ground termination. """

    def make(self):
        """Build the component."""
        super().make()
