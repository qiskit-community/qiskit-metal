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
"""This is the StarQubit module."""

from qiskit_metal import draw, Dict  # , QComponent
from qiskit_metal.qlibrary.core import QComponent
from shapely.geometry import CAP_STYLE


class StarQubit(QComponent):
    """A single configurable circle with multiple pads.

    Inherits `BaseQubit` class.

    Create a circular transmon qubit with up to 4 connectors and one readout.

    .. image::
        StarQubit.png

    Default Options:
        * radius: '300um' -- Radius of the circle defining the star shape
        * center_radius: '100um' -- Measure of how thick the central island is
        * gap_couplers: '25um' -- Gap between the star and the coupling resonator
        * gap_readout: '10um' -- Gap between the star and the readout resonator
        * connector_length: '75um' -- Length of the rectangular part of the connector
        * trap_offset: '20um' -- Offset between trapezoid coordinates for side wall angle
        * junc_h: '30um' -- Junction height
        * cpw_width='0.01', -- Junction width
        * rotation_cpl1: '0.0' -- Rotation for one of the coupling resonators '36.0', '0.0',
        * rotation_cpl2: '72.0' -- Rotation for the readout resonator '108.0','72.0',
        * rotation_rdout: '144.0' -- Rotation for one of the coupling resonators '180.0','144.0',
        * rotation_cpl3: '216.0' -- Rotation for one of the coupling resonators'252.0','216.0',
        * rotation_cpl4: '288.0' -- Rotation for one of the coupling resonators '324.0','288.0',
        * number_of_connectors: '4' -- Total number of coupling resonators
        * resolution: '16'
        * cap_style: 'round' -- round, flat, square
        * subtract: 'False'
        * helper: 'False'
    """
    component_metadata = Dict(short_name='Star',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='True')
    """Component metadata"""

    default_options = dict(radius='300um',
                           center_radius='100um',
                           gap_couplers='25um',
                           gap_readout='10um',
                           connector_length='75um',
                           trap_offset='20um',
                           junc_h='100um',
                           cpw_width='0.01',
                           rotation_cpl1='0.0',
                           rotation_cpl2='72.0',
                           rotation_rdout='144.0',
                           rotation_cpl3='216.0',
                           rotation_cpl4='288.0',
                           number_of_connectors='4',
                           resolution='16',
                           cap_style='round',
                           subtract='False',
                           helper='False')
    """Default drawing options"""

    def make(self):
        """The make function implements the logic that creates the geometry
        (poly, path, etc.) from the qcomponent.options dictionary of
        parameters, and the adds them to the design, using
        qcomponent.add_qgeometry(...), adding in extra needed information, such
        as layer, subtract, etc.
        """
        p = self.p

        # Extracting coordinated from the user input values

        # Coordinates of the trapezoid to subtract from circle
        coord_y1 = -p.center_radius
        coord_y2 = -p.radius
        coord_x1 = -p.center_radius / 2
        coord_x2 = p.center_radius / 2
        coord_x3 = p.center_radius + p.trap_offset
        coord_x4 = -(p.center_radius + p.trap_offset)

        # Coordinates of the polygon defining the coupling resonator (a=x, b=y)
        coord_a1 = -(p.center_radius + p.gap_couplers)
        coord_a2 = -p.radius
        coord_a3 = p.radius
        coord_b1 = -(p.center_radius / 4)
        coord_b2 = (p.center_radius / 4)
        coord_b3 = (p.center_radius - (p.gap_couplers))
        coord_b4 = -(p.center_radius - (p.gap_couplers))
        coord_b5 = -p.radius
        coord_b6 = p.radius

        # Coordinates of the polygon defining the readout resonator (c=x, d=y)
        coord_c1 = -(p.center_radius + p.gap_readout)
        coord_c2 = -p.radius
        coord_c3 = p.radius
        coord_d1 = -(p.center_radius / 2 - p.gap_readout)
        coord_d2 = p.center_radius / 2 - p.gap_readout
        coord_d3 = p.center_radius
        coord_d4 = -p.center_radius
        coord_d5 = -p.radius
        coord_d6 = p.radius

        # Connector pocket width/height
        pocket_w = p.connector_length
        pocket_h = p.connector_length * 2

        # Connector to the JJ width/height
        pocket_w1 = p.gap_couplers
        pocket_h1 = p.center_radius

        # create a circle
        circle = draw.Point(0,
                            0).buffer(p.radius,
                                      resolution=int(p.resolution),
                                      cap_style=getattr(CAP_STYLE, p.cap_style))
        # create the outer circle to be subtracted
        circle_outer = draw.Point(0, 0).buffer(
            p.radius * (1 + (p.connector_length / p.radius)),
            resolution=int(p.resolution),
            cap_style=getattr(CAP_STYLE, p.cap_style))

        # coordinated for trapezoid to be cut out
        coords1 = [((coord_x1), (coord_y1)), ((coord_x2), (coord_y1)),
                   ((coord_x3), (coord_y2)), ((coord_x4), (coord_y2))]
        trap_0 = draw.Polygon(coords1)
        trap_1 = draw.rotate(trap_0, p.rotation_cpl1, origin=(0, 0))
        trap_2 = draw.rotate(trap_0, p.rotation_cpl2, origin=(0, 0))
        trap_3 = draw.rotate(trap_0, p.rotation_rdout, origin=(0, 0))
        trap_4 = draw.rotate(trap_0, p.rotation_cpl3, origin=(0, 0))
        trap_5 = draw.rotate(trap_0, p.rotation_cpl4, origin=(0, 0))

        # Define the coordinates of the polygon to define connectors
        coords_coupling_resonator = [((coord_b1), (coord_a1)),
                                     ((coord_b2), (coord_a1)),
                                     ((coord_b3), (coord_a2)),
                                     ((coord_b6), (coord_a2)),
                                     ((coord_b6), (coord_a3)),
                                     ((coord_b5), (coord_a3)),
                                     ((coord_b5), (coord_a2)),
                                     ((coord_b4), (coord_a2))]

        # rotate these trapezoids to form the contacts
        trap_z = draw.Polygon(coords_coupling_resonator)
        trap_a = draw.rotate(trap_z, p.rotation_cpl1, origin=(0, 0))
        trap_b = draw.rotate(trap_z, p.rotation_cpl2, origin=(0, 0))
        trap_d = draw.rotate(trap_z, p.rotation_cpl3, origin=(0, 0))
        trap_e = draw.rotate(trap_z, p.rotation_cpl4, origin=(0, 0))

        # Define the coordinates of the polygon to define readout
        coords_readout = [((coord_d1), (coord_c1)), ((coord_d2), (coord_c1)),
                          ((coord_d3), (coord_c2)), ((coord_d6), (coord_c2)),
                          ((coord_d6), (coord_c3)), ((coord_d5), (coord_c3)),
                          ((coord_d5), (coord_c2)), ((coord_d4), (coord_c2))]
        trap_c = draw.Polygon(coords_readout)
        trap_c = draw.rotate(trap_c, p.rotation_rdout, origin=(0, 0))

        # create rectangular connectors to junction
        rect1 = draw.rectangle(pocket_w1, pocket_h1)
        rect1 = draw.translate(rect1, xoff=coord_b2 * 1.1, yoff=p.radius)
        rect1 = draw.rotate(rect1, p.rotation_cpl1, origin=(0, 0))
        rect2 = draw.rectangle(pocket_w1, pocket_h1)
        rect2 = draw.translate(rect2, xoff=coord_b1 * 1.1, yoff=p.radius)
        rect2 = draw.rotate(rect2, p.rotation_cpl1, origin=(0, 0))

        # Define contacts
        pocket0 = draw.rectangle(pocket_w, pocket_h)
        pocket0 = draw.translate(pocket0, xoff=0, yoff=(coord_y2))
        pocket1 = draw.rotate(pocket0, p.rotation_cpl1, origin=(0, 0))
        pocket2 = draw.rotate(pocket0, p.rotation_cpl2, origin=(0, 0))
        pocket3 = draw.rotate(pocket0, p.rotation_rdout, origin=(0, 0))
        pocket4 = draw.rotate(pocket0, p.rotation_cpl3, origin=(0, 0))
        pocket5 = draw.rotate(pocket0, p.rotation_cpl4, origin=(0, 0))

        #Connectors for the ground plane
        pocket_z = draw.rectangle(pocket_w * 1.4, pocket_h)
        pocket_z = draw.translate(pocket_z, xoff=0, yoff=(coord_y2))
        pocket_a = draw.rotate(pocket_z, p.rotation_cpl1, origin=(0, 0))
        pocket_b = draw.rotate(pocket_z, p.rotation_cpl2, origin=(0, 0))
        pocket_c = draw.rotate(pocket_z, p.rotation_rdout, origin=(0, 0))
        pocket_d = draw.rotate(pocket_z, p.rotation_cpl3, origin=(0, 0))
        pocket_e = draw.rotate(pocket_z, p.rotation_cpl4, origin=(0, 0))
        if (p.number_of_connectors) == 0:
            circle_outer = draw.union(circle_outer, pocket_c)
        elif (p.number_of_connectors) == 1:
            circle_outer = draw.union(circle_outer, pocket_a, pocket_c)
        elif (p.number_of_connectors) == 2:
            circle_outer = draw.union(circle_outer, pocket_a, pocket_b,
                                      pocket_c)
        elif (p.number_of_connectors) == 3:
            circle_outer = draw.union(circle_outer, pocket_a, pocket_b,
                                      pocket_c, pocket_d)
        elif (p.number_of_connectors) == 4:
            circle_outer = draw.union(circle_outer, pocket_a, pocket_b,
                                      pocket_c, pocket_d, pocket_e)

        #junction
        jjunction = draw.LineString([[0, 0], [0, coord_x2]])
        jjunction = draw.translate(jjunction, yoff=(1.15 * (p.radius)))
        jjunction = draw.rotate(jjunction, p.rotation_cpl1, origin=(0, 0))

        # Define the final structure based
        if (p.number_of_connectors) == 0:
            traps = trap_3
        elif (p.number_of_connectors) == 1:
            traps = draw.union(trap_1, trap_3)
        elif (p.number_of_connectors) == 2:
            traps = draw.union(trap_1, trap_2, trap_3)
        elif (p.number_of_connectors) == 3:
            traps = draw.union(trap_1, trap_2, trap_3, trap_4)
        elif (p.number_of_connectors) == 4:
            traps = draw.union(trap_1, trap_2, trap_3, trap_4, trap_5)

        # Subtract
        total1 = draw.subtract(circle, traps)
        # Add connection to the junction
        total = draw.union(total1, rect1, rect2)

        # Define the connectors
        contact_cpl1 = draw.subtract(circle, trap_a)
        contact_cpl1 = draw.union(contact_cpl1, pocket1)
        contact_cpl2 = draw.subtract(circle, trap_b)
        contact_cpl2 = draw.union(contact_cpl2, pocket2)
        contact_rdout = draw.subtract(circle, trap_c)
        contact_rdout = draw.union(contact_rdout, pocket3)
        contact_cpl3 = draw.subtract(circle, trap_d)
        contact_cpl3 = draw.union(contact_cpl3, pocket4)
        contact_cpl4 = draw.subtract(circle, trap_e)
        contact_cpl4 = draw.union(contact_cpl4, pocket5)

        ##################################################################
        # Add geometry and Qpin connections
        p_in = (0, p.radius)
        p_out = (0, 1.25 * (p.radius))
        pins = draw.LineString([p_in, p_out])
        pins_cpl1 = draw.rotate(pins, p.rotation_cpl1 + 180, origin=(0, 0))
        pins_cpl2 = draw.rotate(pins, p.rotation_cpl2 + 180, origin=(0, 0))
        pins_rdout = draw.rotate(pins, p.rotation_rdout + 180, origin=(0, 0))
        pins_cpl3 = draw.rotate(pins, p.rotation_cpl3 + 180, origin=(0, 0))
        pins_cpl4 = draw.rotate(pins, p.rotation_cpl4 + 180, origin=(0, 0))
        objects = [
            total, jjunction, contact_rdout, contact_cpl1, contact_cpl2,
            contact_cpl3, contact_cpl4, pins_rdout, pins_cpl1, pins_cpl2,
            pins_cpl3, pins_cpl4, circle_outer
        ]
        objects = draw.rotate(objects, p.orientation, origin=(0, 0))
        objects = draw.translate(objects, p.pos_x, p.pos_y)
        [
            total, jjunction, contact_rdout, contact_cpl1, contact_cpl2,
            contact_cpl3, contact_cpl4, pins_rdout, pins_cpl1, pins_cpl2,
            pins_cpl3, pins_cpl4, circle_outer
        ] = objects

        self.add_qgeometry('poly', {'circle_inner': total},
                           subtract=p.subtract,
                           helper=p.helper,
                           layer=p.layer,
                           chip=p.chip)
        self.add_qgeometry('poly', {'contact_rdout': contact_rdout},
                           subtract=p.subtract,
                           helper=p.helper,
                           layer=p.layer,
                           chip=p.chip)
        self.add_pin('pin_rdout',
                     pins_rdout.coords,
                     width=p.cpw_width,
                     input_as_norm=True)
        if (p.number_of_connectors) >= 1:
            self.add_qgeometry('poly', {'contact_cpl1': contact_cpl1},
                               subtract=p.subtract,
                               helper=p.helper,
                               layer=p.layer,
                               chip=p.chip)
            # Add pin connections
            self.add_pin('pin_cpl1',
                         pins_cpl1.coords,
                         width=p.cpw_width,
                         input_as_norm=True)
        if (p.number_of_connectors) >= 2:
            self.add_qgeometry('poly', {'contact_cpl2': contact_cpl2},
                               subtract=p.subtract,
                               helper=p.helper,
                               layer=p.layer,
                               chip=p.chip)
            # Add pin connections
            self.add_pin('pin_cpl2',
                         pins_cpl2.coords,
                         width=p.cpw_width,
                         input_as_norm=True)
        if (p.number_of_connectors) >= 3:
            self.add_qgeometry('poly', {'contact_cpl3': contact_cpl3},
                               subtract=p.subtract,
                               helper=p.helper,
                               layer=p.layer,
                               chip=p.chip)
            # Add pin connections
            self.add_pin('pin_cpl3',
                         pins_cpl3.coords,
                         width=p.cpw_width,
                         input_as_norm=True)
        if (p.number_of_connectors) >= 4:
            self.add_qgeometry('poly', {'contact_cpl4': contact_cpl4},
                               subtract=p.subtract,
                               helper=p.helper,
                               layer=p.layer,
                               chip=p.chip)
            # Add pin connections
            self.add_pin('pin_cpl4',
                         pins_cpl4.coords,
                         width=p.cpw_width,
                         input_as_norm=True)
        self.add_qgeometry('junction', {'poly': jjunction},
                           subtract=p.subtract,
                           helper=p.helper,
                           layer=p.layer,
                           chip=p.chip,
                           width=p.junc_h)
        self.add_qgeometry('poly', {'circle_outer': circle_outer},
                           subtract=True,
                           helper=p.helper,
                           layer=p.layer,
                           chip=p.chip)