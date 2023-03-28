# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2023.
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


class SPole(QComponent):
    """
    Implements square CPW in the +z axis. Used in MultiPlanar designs.

Inherits `QComponent` class

    Default Options:
        * width: 'cpw_width' -- Width of square, defaults to 'cpw_width'.
        * gap: 'cpw_gap' -- Gap between CPW and grounding plane, defaults to 'cpw_gap'.
    """

    default_options = Dict(width='cpw_width', gap='cpw_gap')
    """Default options"""

    TOOLTIP = "Implements a straight CPW in the z axis."

    def make(self):
        p = self.p
        self.options.pos_x, self.options.pos_y = self.get_pin_location(
            p.name, p.pin)

        # Draw SPole
        pole = draw.rectangle(p.width, p.width, 0, 0)
        pole_etch = draw.rectangle(p.width + 2 * p.gap, p.width + 2 * p.gap, 0,
                                   0)

        # Rotate and Translate
        polys = [pole, pole_etch]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, self.options.pos_x, self.options.pos_y)
        [pole, pole_etch] = polys

        for layer in p.layers:
            self.add_qgeometry('poly', {'pole': pole},
                               subtract=False,
                               layer=layer,
                               chip=p.chip)
            self.add_qgeometry('poly', {'pole_etch': pole_etch},
                               subtract=True,
                               layer=layer,
                               chip=p.chip)

    def get_pin_location(self, name: str, pin: str) -> float:
        pos = self.design.components[name].pins[pin].middle
        return pos
