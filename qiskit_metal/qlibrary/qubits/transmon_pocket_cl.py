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
"""Transmon Pocket CL.

Pocket "axis"
        _________________
        |               |
        |_______________|       ^
        ________x________       |  N
        |               |       |
        |_______________|

Child of 'standard' transmon pocket.
"""
# pylint: disable=invalid-name
# Modification of Transmon Pocket Object to include a charge line (would be better to just make as a child)

import numpy as np
from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket


class TransmonPocketCL(TransmonPocket):  # pylint: disable=invalid-name
    """The base `TransmonPocketCL` class.

    Inherits `TransmonPocket` class.

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
        TransmonPocketCL.png

    .. meta::
        :description: Transmon Pocket Charge Line

    BaseQubit Default Options:
        * connection_pads: empty Dict -- The dictionary which contains all active connection lines for the qubit.
        * _default_connection_pads: empty Dict -- The default values for the (if any) connection lines of the qubit.

    TransmonPocket Default Options:
        * pad_gap: '30um' -- The distance between the two charge islands, which is also the resulting 'length' of the pseudo junction
        * inductor_width: '20um' -- Width of the pseudo junction between the two charge islands (if in doubt, make the same as pad_gap). Really just for simulating in HFSS / other EM software
        * pad_width: '455um' -- The width (x-axis) of the charge island pads
        * pad_height: '90um' -- The size (y-axis) of the charge island pads
        * pocket_width: '650um' -- Size of the pocket (cut out in ground) along x-axis
        * pocket_height: '650um' -- Size of the pocket (cut out in ground) along y-axis
        * _default_connection_pads: Dict
            * pad_gap: '15um' -- Space between the connector pad and the charge island it is nearest to
            * pad_width: '125um' -- Width (x-axis) of the connector pad
            * pad_height: '30um' -- Height (y-axis) of the connector pad
            * pad_cpw_shift: '5um' -- Shift the connector pad cpw line by this much away from qubit
            * pad_cpw_extent: '25um' -- Shift the connector pad cpw line by this much away from qubit
            * cpw_width: 'cpw_width' -- Center trace width of the CPW line
            * cpw_gap: 'cpw_gap' -- Dielectric gap width of the CPW line
            * cpw_extend: '100um' -- Depth the connector line extends into ground (past the pocket edge)
            * pocket_extent: '5um' -- How deep into the pocket should we penetrate with the cpw connector (into the fround plane)
            * pocket_rise: '65um' -- How far up or downrelative to the center of the transmon should we elevate the cpw connection point on the ground plane
            * loc_W: '+1' -- Width location  only +-1
            * loc_H: '+1' -- Height location only +-1

    Default Options:
        * make_CL: True -- If a charge line should be included.
        * cl_gap: '6um' -- The cpw dielectric gap of the charge line
        * cl_width: '10um' -- The cpw trace width of the charge line
        * cl_length: '20um' --  The length of the charge line 'arm' coupling the the qubit pocket.
          Measured from the base of the 90 degree bend.
        * cl_ground_gap: '6um' -- How much ground is present between the charge line and the
          qubit pocket.
        * cl_pocket_edge: '0' -- What side of the pocket the charge line is.
          -180 to +180 from the 'west edge', will round to the nearest 90.
        * cl_off_center: '50um' -- Distance from the center axis the qubit pocket is referenced to
    """
    component_metadata = Dict(short_name='Q', _qgeometry_table_poly='True')
    """Component metadata"""

    default_options = Dict(
        make_CL=True,
        cl_gap='6um',  # the cpw dielectric gap of the charge line
        cl_width='10um',  # the cpw trace width of the charge line
        # the length of the charge line 'arm' coupling the the qubit pocket.
        cl_length='20um',
        # Measured from the base of the 90 degree bend
        cl_ground_gap=
        '6um',  # how much ground between the charge line and the qubit pocket
        # -180 to +180 from the 'left edge', will round to the nearest 90.
        cl_pocket_edge='0',
        cl_off_center=
        '50um',  # distance from the center axis the qubit pocket is built on
    )
    """Default drawing options"""

    TOOLTIP = """Create a standard pocket transmon qubit for a ground plane,
    with two pads connected by a junction"""

    def make(self):
        """Define the way the options are turned into QGeometry."""
        super().make()

        if self.options.make_CL == True:
            self.make_charge_line()


#####################################################################

    def make_charge_line(self):
        """Creates the charge line if the user has charge line option to
        TRUE."""

        # Grab option values
        name = 'Charge_Line'

        p = self.p

        cl_arm = draw.box(0, 0, -p.cl_width, p.cl_length)
        cl_cpw = draw.box(0, 0, -8 * p.cl_width, p.cl_width)
        cl_metal = draw.unary_union([cl_arm, cl_cpw])

        cl_etcher = draw.buffer(cl_metal, p.cl_gap)

        port_line = draw.LineString([(-8 * p.cl_width, 0),
                                     (-8 * p.cl_width, p.cl_width)])

        polys = [cl_metal, cl_etcher, port_line]

        # Move the charge line to the side user requested
        cl_rotate = 0
        if (abs(p.cl_pocket_edge) > 135) or (abs(p.cl_pocket_edge) < 45):
            polys = draw.translate(
                polys, -(p.pocket_width / 2 + p.cl_ground_gap + p.cl_gap),
                p.cl_off_center)
            if (abs(p.cl_pocket_edge) > 135):
                cl_rotate = 180
        else:
            polys = draw.translate(
                polys, -(p.pocket_height / 2 + p.cl_ground_gap + p.cl_gap),
                p.cl_off_center)
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
        self.add_pin(name, points, p.cl_width)

        # Adding to qgeometry table
        self.add_qgeometry('poly', dict(cl_metal=cl_metal))
        self.add_qgeometry('poly', dict(cl_etcher=cl_etcher), subtract=True)
