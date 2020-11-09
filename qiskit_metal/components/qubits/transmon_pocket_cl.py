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

'''
@date: 2019
@author: Zlatko K Minev
modified: Thomas McConkey - Added Charge Line


Pocket "axis"
        _________________
        |               |
        |_______________|       ^
        ________x________       |  N
        |               |       |
        |_______________|

Child of 'standard' transmon pocket
'''
# pylint: disable=invalid-name
# Modification of Transmon Pocket Object to include a charge line (would be better to just make as a child)

import numpy as np
from qiskit_metal import draw, Dict
from qiskit_metal.components.qubits.transmon_pocket import TransmonPocket


class TransmonPocketCL(TransmonPocket):  # pylint: disable=invalid-name
    """
    The base `TransmonPocketCL` class

    Inherits `TransmonPocket` class

    Description:
        Create a standard pocket transmon qubit for a ground plane,
        with two pads connected by a junction (see drawing below).

        Connector lines can be added using the `connection_pads`
        dictionary. Each connector line has a name and a list of default
        properties.

        This is a child of TransmonPocket, see TransmonPocket for the variables and
        description of that class.

    ::

        _________________
        |               |
        |_______________|       ^
        ________x________       |  N
        |               |       |
        |_______________|


    .. image::
        Component_Qubit_Transmon_Pocket_CL.png


    Charge Line:
        * make_CL (bool): If a chargeline should be included.
        * cl_gap (string): The cpw dielectric gap of the charge line.
        * cl_width (string): The cpw width of the charge line.
        * cl_length (string):  The length of the charge line 'arm' coupling the the qubit pocket.
          Measured from the base of the 90 degree bend.
        * cl_ground_gap (string):  How much ground is present between the charge line and the
          qubit pocket.
        * cl_pocket_edge (string): What side of the pocket the charge line is.
          -180 to +180 from the 'west edge', will round to the nearest 90.
        * cl_off_center (string):  Distance from the center axis the qubit pocket is referenced to
    """
    component_metadata = Dict(
        short_name='Q',
        _qgeometry_table_poly='True'
    )
    """Component metadata"""

    default_options = Dict(
        make_CL=True,
        cl_gap='6um',  # the cpw dielectric gap of the charge line
        cl_width='10um',  # the cpw trace width of the charge line
        # the length of the charge line 'arm' coupling the the qubit pocket.
        cl_length='20um',
        # Measured from the base of the 90 degree bend
        cl_ground_gap='6um',  # how much ground between the charge line and the qubit pocket
        # -180 to +180 from the 'left edge', will round to the nearest 90.
        cl_pocket_edge='0',
        cl_off_center='100um',  # distance from the center axis the qubit pocket is built on
    )
    """Default drawing options"""

    def make(self):
        """Define the way the options are turned into QGeometry."""
        super().make()

        if self.options.make_CL == True:
            self.make_charge_line()


#####################################################################


    def make_charge_line(self):
        """Creates the charge line if the user has charge line option to TRUE
        """

        # Grab option values
        name = 'Charge_Line'

        p = self.p

        cl_arm = draw.box(0, 0, -p.cl_width, p.cl_length)
        cl_cpw = draw.box(0, 0, -8*p.cl_width, p.cl_width)
        cl_metal = draw.cascaded_union([cl_arm, cl_cpw])

        cl_etcher = draw.buffer(cl_metal, p.cl_gap)

        port_line = draw.LineString(
            [(-8*p.cl_width, 0), (-8*p.cl_width, p.cl_width)])

        polys = [cl_metal, cl_etcher, port_line]

        # Move the charge line to the side user requested
        cl_rotate = 0
        if (abs(p.cl_pocket_edge) > 135) or (abs(p.cl_pocket_edge) < 45):
            polys = draw.translate(polys, -(p.pocket_width/2 + p.cl_ground_gap + p.cl_gap),
                                   -(p.pad_gap + p.pad_height)/2)
            if (abs(p.cl_pocket_edge) > 135):
                p.cl_rotate = 180
        else:
            polys = draw.translate(
                polys, -(p.pocket_height/2 + p.cl_groundGap + p.cl_gap), -(p.pad_width)/2)
            cl_rotate = 90
            if (p.cl_pocket_edge < 0):
                cl_rotate = -90

        # Rotate it to the pockets orientation
        polys = draw.rotate(polys, p.orientation + cl_rotate, origin=(0, 0))

        # Move to the final position
        polys = draw.translate(polys, p.pos_x, p.pos_y)

        [cl_metal, cl_etcher, port_line] = polys

        # Generating pins
        points = list(draw.shapely.geometry.shape(port_line).coords)
        self.add_pin(name, points, p.cl_width)  # TODO: chip

        # Adding to element table
        self.add_qgeometry('poly', dict(cl_metal=cl_metal))
        self.add_qgeometry('poly', dict(cl_etcher=cl_etcher), subtract=True)
