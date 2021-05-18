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
"""TEST COMPONENT NOT FOR ACTUAL USE."""

from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import QComponent
import numpy as np


class SmileyFace(QComponent):
    """TEST COMPONENT It is for fun only.  Can view a smiley face. Can make it
    wink or frown.

    Default Options:
        * happy: True
        * wink: False
        * orientation: 0
    """

    component_metadata = Dict(short_name='Smile')
    """Component metadata"""

    default_options = Dict(happy=True, wink=False, orientation=0)
    """Default connector options"""

    TOOLTIP = """TEST COMPONENT It is for fun only"""

    def make(self):
        """Build the component."""
        face = draw.shapely.geometry.Point(0, 0).buffer(1)
        eye = draw.shapely.geometry.Point(0, 0).buffer(0.2)
        eye_l = draw.translate(eye, -0.4, 0.4)
        eye_r = draw.translate(eye, 0.4, 0.4)

        smile = draw.shapely.geometry.Point(0, 0).buffer(0.8)
        cut_sq = draw.shapely.geometry.box(-1, -0.3, 1, 1)
        smile = draw.subtract(smile, cut_sq)

        frown = draw.rotate(smile, 180)
        frown = draw.translate(frown, 0, 0.3)
        frown = draw.subtract(frown,
                              draw.shapely.geometry.Point(0, -0.8).buffer(0.7))

        face = draw.subtract(face, eye_l)

        if self.p.happy:
            face = draw.subtract(face, smile)
        else:
            face = draw.subtract(face, frown)

        if self.p.wink:
            face = draw.subtract(
                face,
                draw.shapely.geometry.LineString([(0.2, 0.4),
                                                  (0.6, 0.4)]).buffer(0.02))
        else:
            face = draw.subtract(face, eye_r)

        face = draw.rotate(face, self.p.orientation, origin=(0, 0))

        self.add_qgeometry('poly', {'Smiley': face})
