# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2020.
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


class MyQComponent1(QComponent):
    """Demonstration1 - Straight segment with variable width/length"""

    ### def __init__() <- comes from QComponent
    ###   Initiaizes base variables such as self.id, self.name and self.options
    ###   Also launches the first execution of make()

    ### def rebuild() <- comes from QComponent
    ###   Clear output from previous runs of make() (geom/pin/net) and re-runs it

    def make(self):
        """calculates the geometries of the QComponent"""
        rect = draw.rectangle(0.5, 0.1, 0, 0)  #width, height, pos_x, pos_y
        # add_geometry() expects shapely, thus the use of drawn module above
        self.add_qgeometry('poly', {'my_polygon': rect},
                           layer=1,
                           subtract=False)
        self.add_pin('in', rect.exterior.coords[:-3:-1],
                     0.1)  #name, tangent, width


class MyQComponent2(QComponent):
    """Demonstration2 - Straight segment with variable width/length"""

    # Your knobs to modify the cell behavior
    default_options = Dict(width='0.5mm',
                           height='0.1mm',
                           pos_x='0mm',
                           pos_y='0mm',
                           layer='1')
    """Default drawing options"""

    def make(self):
        """calculates the geometries of the QComponent"""
        p = self.parse_options(
        )  # short-handle alias for the options interpreter

        rect = draw.rectangle(p.width, p.height, p.pos_x, p.pos_y)
        self.add_qgeometry('poly', {'my_polygon': rect},
                           layer=p.layer,
                           subtract=False)
        self.add_pin('in', rect.exterior.coords[:-3:-1], p.height)


class MyQComponent3(QComponent):
    """Demonstration2 - Straight segment with variable width/length"""

    default_options = Dict(width='0.5mm',
                           height='0.1mm',
                           pos_x='0mm',
                           pos_y='0mm',
                           layer='1')
    """Default drawing options"""

    # Name prefix of component + import of renderer-specific default_options
    component_metadata = Dict(
        short_name='Trace',
        _qgeometry_table_path='False',  #wirebonds
        _qgeometry_table_poly='True',
        _qgeometry_table_junction='False')  #gds imports and analysis inputs
    """Component metadata"""

    def make(self):
        """calculates the geometries of the QComponent"""
        p = self.parse_options()  # short-handle alias. Options interpreter

        rect = draw.rectangle(p.width, p.height, p.pos_x, p.pos_y)
        self.add_qgeometry('poly', {'my_polygon': rect},
                           layer=p.layer,
                           subtract=False)
        self.add_pin('in', rect.exterior.coords[:-3:-1], p.height)


class MyQComponent4(QComponent):
    """Demonstration3 - Straight segment with variable width/length"""

    default_options = Dict(width='0.5mm',
                           height='0.1mm',
                           gap='0.02mm',
                           pos_x='0mm',
                           pos_y='0mm',
                           layer='1')
    """Default drawing options"""

    # Name prefix of component + import of renderer-specific default_options
    component_metadata = Dict(
        short_name='Trace',
        _qgeometry_table_path='True',  #wirebonds
        _qgeometry_table_poly='False',
        _qgeometry_table_junction='False')  #gds
    """Component metadata"""

    def make(self):
        """calculates the geometries of the QComponent"""
        p = self.parse_options()

        line = draw.LineString([(-p.width / 2, 0), (p.width / 2, 0)])
        line = draw.translate(line, p.pos_x, p.pos_y)
        self.add_qgeometry('path', {'trace': line},
                           width=p.height,
                           layer=p.layer,
                           subtract=False)
        line2 = draw.LineString([((-p.width / 2) - 2 * p.gap, 0),
                                 ((p.width / 2) + 2 * p.gap, 0)])
        line2 = draw.translate(line2, p.pos_x, p.pos_y)
        self.add_qgeometry('path', {'cut': line2},
                           width=p.height + 2 * p.gap,
                           layer=p.layer,
                           subtract=True)
        self.add_pin('in', line.coords[::-1], p.height, input_as_norm=True)
