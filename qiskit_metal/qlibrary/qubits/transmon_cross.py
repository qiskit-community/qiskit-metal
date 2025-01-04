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
from qiskit_metal.qlibrary.core import BaseQubit


class TransmonCross(BaseQubit):  # pylint: disable=invalid-name
    """The base `TransmonCross` class.

    Inherits `BaseQubit` class.

    Simple Metal Transmon Cross object. Creates the X cross-shaped island,
    the "junction" on the south end, and up to 3 connectors on the remaining arms
    (claw or gap).

    'claw_width' and 'claw_gap' define the width/gap of the CPW line that
    makes up the connector. Note, DC SQUID currently represented by single
    inductance sheet

    Add connectors to it using the `connection_pads` dictionary. See BaseQubit for more
    information.

    Sketch:
        Below is a sketch of the qubit
        ::

                                        claw_length
            Claw:       _________                    Gap:
                        |   ________________             _________    ____________
                  ______|  |                             _________|  |____________
                        |  |________________
                        |_________


    .. image::
        transmon_cross.png

    .. meta::
        Transmon Cross

    BaseQubit Default Options:
        * connection_pads: Empty Dict -- The dictionary which contains all active connection lines for the qubit.
        * _default_connection_pads: empty Dict -- The default values for the (if any) connection lines of the qubit.

    Default Options:
        * cross_width: '20um' -- Width of the CPW center trace making up the Crossmon
        * cross_length: '200um' -- Length of one Crossmon arm (from center)
        * cross_gap: '20um' -- Width of the CPW gap making up the Crossmon
        * _default_connection_pads: Dict
            * connector_type: '0' -- 0 = Claw type, 1 = gap type
            * claw_length: '30um' -- Length of the claw 'arms', measured from the connector center trace
            * ground_spacing: '5um' -- Amount of ground plane between the connector and Crossmon arm (minimum should be based on fabrication capabilities)
            * claw_width: '10um' -- The width of the CPW center trace making up the claw/gap connector
            * claw_gap: '6um' -- The gap of the CPW center trace making up the claw/gap connector
            * connector_location: '0' -- 0 => 'west' arm, 90 => 'north' arm, 180 => 'east' arm
    """

    default_options = Dict(
        cross_width='20um',
        cross_length='200um',
        cross_gap='20um',
        chip='main',
        _default_connection_pads=Dict(
            connector_type='0',  # 0 = Claw type, 1 = gap type
            claw_length='30um',
            ground_spacing='5um',
            claw_width='10um',
            claw_gap='6um',
            claw_cpw_length='40um',
            claw_cpw_width='10um',
            connector_location=
            '0'  # 0 => 'west' arm, 90 => 'north' arm, 180 => 'east' arm
        ))
    """Default options."""

    component_metadata = Dict(short_name='Cross',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='True')
    """Component metadata"""

    TOOLTIP = """Simple Metal Transmon Cross."""

    ##############################################MAKE######################################################

    def make(self):
        """This is executed by the GUI/user to generate the qgeometry for the
        component."""
        self.make_pocket()
        self.make_connection_pads()

###################################TRANSMON#############################################################

    def make_pocket(self):
        """Makes a basic Crossmon, 4 arm cross."""

        # self.p allows us to directly access parsed values (string -> numbers) from the user option
        p = self.p

        cross_width = p.cross_width
        cross_length = p.cross_length
        cross_gap = p.cross_gap

        # access to chip name
        chip = p.chip

        # Creates the cross and the etch equivalent.
        cross_line = draw.shapely.ops.unary_union([
            draw.LineString([(0, cross_length), (0, -cross_length)]),
            draw.LineString([(cross_length, 0), (-cross_length, 0)])
        ])

        cross = cross_line.buffer(cross_width / 2, cap_style=2)
        cross_etch = cross.buffer(cross_gap, cap_style=3, join_style=2)

        # The junction/SQUID
        #rect_jj = draw.rectangle(cross_width, cross_gap)
        #rect_jj = draw.translate(rect_jj, 0, -cross_length-cross_gap/2)
        rect_jj = draw.LineString([(0, -cross_length),
                                   (0, -cross_length - cross_gap)])

        #rotate and translate
        polys = [cross, cross_etch, rect_jj]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)

        [cross, cross_etch, rect_jj] = polys

        # generate qgeometry
        self.add_qgeometry('poly', dict(cross=cross), chip=chip)
        self.add_qgeometry('poly',
                           dict(cross_etch=cross_etch),
                           subtract=True,
                           chip=chip)
        self.add_qgeometry('junction',
                           dict(rect_jj=rect_jj),
                           width=cross_width,
                           chip=chip)


############################CONNECTORS##################################################################################################

    def make_connection_pads(self):
        """Goes through connector pads and makes each one."""
        for name in self.options.connection_pads:
            self.make_connection_pad(name)

    def make_connection_pad(self, name: str):
        """Makes individual connector pad.

        Args:
            name (str) : Name of the connector pad
        """

        # self.p allows us to directly access parsed values (string -> numbers) from the user option
        p = self.p
        cross_width = p.cross_width
        cross_length = p.cross_length
        cross_gap = p.cross_gap

        # access to chip name
        chip = p.chip

        pc = self.p.connection_pads[name]  # parser on connector options
        c_g = pc.claw_gap
        c_l = pc.claw_length
        c_w = pc.claw_width
        c_c_w = pc.claw_cpw_width
        c_c_l = pc.claw_cpw_length
        g_s = pc.ground_spacing
        con_loc = pc.connector_location

        claw_cpw = draw.box(-c_w, -c_c_w / 2, -c_c_l - c_w, c_c_w / 2)

        if pc.connector_type == 0:  # Claw connector
            t_claw_height = 2*c_g + 2 * c_w + 2*g_s + \
                2*cross_gap + cross_width  # temp value

            claw_base = draw.box(-c_w, -(t_claw_height) / 2, c_l,
                                 t_claw_height / 2)
            claw_subtract = draw.box(0, -t_claw_height / 2 + c_w, c_l,
                                     t_claw_height / 2 - c_w)
            claw_base = claw_base.difference(claw_subtract)

            connector_arm = draw.shapely.ops.unary_union([claw_base, claw_cpw])
            connector_etcher = draw.buffer(connector_arm, c_g)
        else:
            connector_arm = draw.box(0, -c_w / 2, -4 * c_w, c_w / 2)
            connector_etcher = draw.buffer(connector_arm, c_g)

        # Making the pin for  tracking (for easy connect functions).
        # Done here so as to have the same translations and rotations as the connector. Could
        # extract from the connector later, but since allowing different connector types,
        # this seems more straightforward.
        port_line = draw.LineString([(-c_c_l - c_w, -c_c_w / 2),
                                     (-c_c_l - c_w, c_w / 2)])

        claw_rotate = 0
        if con_loc > 135:
            claw_rotate = 180
        elif con_loc > 45:
            claw_rotate = -90

        # Rotates and translates the connector polygons (and temporary port_line)
        polys = [connector_arm, connector_etcher, port_line]
        polys = draw.translate(polys, -(cross_length + cross_gap + g_s + c_g),
                               0)
        polys = draw.rotate(polys, claw_rotate, origin=(0, 0))
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)
        [connector_arm, connector_etcher, port_line] = polys

        # Generates qgeometry for the connector pads
        self.add_qgeometry('poly', {f'{name}_connector_arm': connector_arm},
                           chip=chip)
        self.add_qgeometry('poly',
                           {f'{name}_connector_etcher': connector_etcher},
                           subtract=True,
                           chip=chip)

        self.add_pin(name, port_line.coords, c_c_w)
