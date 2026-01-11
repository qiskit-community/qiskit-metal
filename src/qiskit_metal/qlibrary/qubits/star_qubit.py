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

from shapely.geometry import CAP_STYLE
from qiskit_metal import draw, Dict  # , QComponent
from qiskit_metal.qlibrary.core import QComponent


class StarQubit(QComponent):
    """A single configurable circle with multiple pads.

    Inherits `BaseQubit` class.

    Create a circular transmon qubit with up to 4 connectors and one readout.

    .. image::
        StarQubit.png

    .. meta::
        :description: Star Qubit

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
        self.make_inner_star()
        self.make_coupling_resonators(4)
        self.make_readout_resonator()
        self.make_outer_circle()

    def make_circle(self):
        """This function creates a circle to be accessed later.
        """
        p = self.p
        # create a circle
        circle = draw.Point(0,
                            0).buffer(p.radius,
                                      resolution=int(p.resolution),
                                      cap_style=getattr(CAP_STYLE, p.cap_style))

        return circle

    def make_pockets(self):
        """This function creates the pockets.
        """
        p = self.p

        # Connector pocket width/height
        pocket_w = p.connector_length
        pocket_h = p.connector_length * 2
        # Connector to the JJ width/height
        pocket_w1 = p.gap_couplers
        pocket_h1 = p.center_radius
        pockets = [pocket_w, pocket_h, pocket_w1, pocket_h1]

        return pockets

    def make_rotation(self, obj, num):
        """This function rotates objects.
        """
        p = self.p
        if num == 1:
            rotation = [p.rotation_rdout]
            x = 1
        elif num == 2:
            rotation = [p.rotation_rdout + 180]
            x = 1
        elif num == 3:
            rotation = [
                p.rotation_cpl1 + 180, p.rotation_cpl2 + 180,
                p.rotation_cpl3 + 180, p.rotation_cpl4 + 180
            ]
            x = 4
        elif num == 4:
            rotation = [
                p.rotation_cpl1, p.rotation_cpl2, p.rotation_cpl3,
                p.rotation_cpl4
            ]
            x = 4
        elif num == 5:
            rotation = [
                p.rotation_cpl1, p.rotation_cpl2, p.rotation_rdout,
                p.rotation_cpl3, p.rotation_cpl4
            ]
            x = 5

        obj_array = [0] * x
        for i in range(x):
            obj_array[i] = draw.rotate(obj, rotation[i], origin=(0, 0))

        return obj_array

    def make_coordinates_trap(self):
        """This function creates the coordinates for trapezoid
        """
        p = self.p
        # Coordinates of the trapezoid to subtract from circle
        coord_y1 = -p.center_radius
        coord_y2 = -p.radius
        coord_x1 = -p.center_radius / 2
        coord_x2 = p.center_radius / 2
        coord_x3 = p.center_radius + p.trap_offset
        coord_x4 = -(p.center_radius + p.trap_offset)
        # coordinated for trapezoid to be cut out
        coords = [((coord_x1), (coord_y1)), ((coord_x2), (coord_y1)),
                  ((coord_x3), (coord_y2)), ((coord_x4), (coord_y2))]

        return coords

    def make_resonator_coordinates(self):
        """This function creates the coordinates for trapezoid
        """
        p = self.p

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

        # Define the coordinates of the polygon to define connectors
        coords_coupling_resonator = [((coord_b1), (coord_a1)),
                                     ((coord_b2), (coord_a1)),
                                     ((coord_b3), (coord_a2)),
                                     ((coord_b6), (coord_a2)),
                                     ((coord_b6), (coord_a3)),
                                     ((coord_b5), (coord_a3)),
                                     ((coord_b5), (coord_a2)),
                                     ((coord_b4), (coord_a2))]

        return coords_coupling_resonator

    def make_readout_coordinates(self):
        """This function creates the coordinates for trapezoid
        """
        p = self.p

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

        # Define the coordinates of the polygon to define readout
        coords_readout = [((coord_d1), (coord_c1)), ((coord_d2), (coord_c1)),
                          ((coord_d3), (coord_c2)), ((coord_d6), (coord_c2)),
                          ((coord_d6), (coord_c3)), ((coord_d5), (coord_c3)),
                          ((coord_d5), (coord_c2)), ((coord_d4), (coord_c2))]

        return coords_readout

    def make_pin_coordinates(self):
        """This function creates the coordinates for the pins
        """
        p = self.p
        p_in = (0, p.radius)
        p_out = (0, 1.25 * (p.radius))
        pins = draw.LineString([p_in, p_out])

        return pins

    def make_inner_star(self):
        """This function creates the coordinates for the pins
        """
        p = self.p
        # Extracting coordinated from the user input values
        coords = self.make_coordinates_trap()
        coords1 = self.make_resonator_coordinates()
        trap_0 = draw.Polygon(coords)
        traps = self.make_rotation(trap_0, 5)

        # Define the final structure based on use input
        if (p.number_of_connectors) == 0:
            traps = traps[2]
        elif (p.number_of_connectors) == 1:
            traps = draw.union(traps[0], traps[2])
        elif (p.number_of_connectors) == 2:
            traps = draw.union(traps[0], traps[1], traps[2])
        elif (p.number_of_connectors) == 3:
            traps = draw.union(traps[0], traps[1], traps[2], traps[3])
        elif (p.number_of_connectors) == 4:
            traps = draw.union(traps[0], traps[1], traps[2], traps[3], traps[4])

        # Subtract from circle
        circle = self.make_circle()
        total1 = draw.subtract(circle, traps)

        # create rectangular connectors to junction
        pockets = self.make_pockets()
        rect1 = draw.rectangle(pockets[2], pockets[3])
        rect1 = draw.translate(rect1, xoff=coords1[0][0] * 1.1, yoff=p.radius)
        rect1 = draw.rotate(rect1, p.rotation_cpl1, origin=(0, 0))
        rect2 = draw.rectangle(pockets[2], pockets[3])
        rect2 = draw.translate(rect2, xoff=coords1[1][0] * 1.1, yoff=p.radius)
        rect2 = draw.rotate(rect2, p.rotation_cpl1, origin=(0, 0))

        #junction
        jjunction = draw.LineString([[0, 0], [0, coords[1][0]]])
        jjunction = draw.translate(jjunction, yoff=(1.15 * (p.radius)))
        jjunction = draw.rotate(jjunction, p.rotation_cpl1, origin=(0, 0))

        # Add connection to the junction
        total = draw.union(total1, rect1, rect2)

        objects = [total, jjunction]
        objects = draw.rotate(objects, p.orientation, origin=(0, 0))
        objects = draw.translate(objects, p.pos_x, p.pos_y)
        [total, jjunction] = objects

        self.add_qgeometry('poly', {'circle_inner': total},
                           subtract=p.subtract,
                           helper=p.helper,
                           layer=p.layer,
                           chip=p.chip)

        self.add_qgeometry('junction', {'poly': jjunction},
                           subtract=p.subtract,
                           helper=p.helper,
                           layer=p.layer,
                           chip=p.chip,
                           width=p.junc_h)

    def make_coupling_resonators(self, num):
        """This function draws the coulping resonators.
           Adds pins. And adds the drawn geometry to qgeomtery table.
        """
        p = self.p
        # rotate these trapezoids to form the contacts

        coords = self.make_coordinates_trap()
        coords1 = self.make_resonator_coordinates()
        trap_z = draw.Polygon(coords1)
        traps_connection = self.make_rotation(trap_z, 4)

        # Define contacts
        pockets = self.make_pockets()
        pocket0 = draw.rectangle(pockets[0], pockets[1])
        pocket0 = draw.translate(pocket0, xoff=0, yoff=(coords[3][1]))
        pockets = self.make_rotation(pocket0, 4)

        # Define the connectors
        circle = self.make_circle()
        contacts = [0] * num
        for i in range(num):
            contacts[i] = draw.subtract(circle, traps_connection[i])
            contacts[i] = draw.union(contacts[i], pockets[i])

        pins = self.make_pin_coordinates()
        pins_cpl = self.make_rotation(pins, 3)

        objects = [contacts, pins_cpl]
        objects = draw.rotate(objects, p.orientation, origin=(0, 0))
        objects = draw.translate(objects, p.pos_x, p.pos_y)
        [contacts, pins_cpl] = objects

        ##################################################################
        # Add geometry and Qpin connections

        if (p.number_of_connectors) >= 1:
            self.add_qgeometry('poly', {'contact_cpl1': contacts[0]},
                               subtract=p.subtract,
                               helper=p.helper,
                               layer=p.layer,
                               chip=p.chip)
            # Add pin connections
            self.add_pin('pin_cpl1',
                         pins_cpl[0].coords,
                         width=p.cpw_width,
                         input_as_norm=True)
        if (p.number_of_connectors) >= 2:
            self.add_qgeometry('poly', {'contact_cpl2': contacts[1]},
                               subtract=p.subtract,
                               helper=p.helper,
                               layer=p.layer,
                               chip=p.chip)
            # Add pin connections
            self.add_pin('pin_cpl2',
                         pins_cpl[1].coords,
                         width=p.cpw_width,
                         input_as_norm=True)
        if (p.number_of_connectors) >= 3:
            self.add_qgeometry('poly', {'contact_cpl3': contacts[2]},
                               subtract=p.subtract,
                               helper=p.helper,
                               layer=p.layer,
                               chip=p.chip)
            # Add pin connections
            self.add_pin('pin_cpl3',
                         pins_cpl[2].coords,
                         width=p.cpw_width,
                         input_as_norm=True)
        if (p.number_of_connectors) >= 4:
            self.add_qgeometry('poly', {'contact_cpl4': contacts[3]},
                               subtract=p.subtract,
                               helper=p.helper,
                               layer=p.layer,
                               chip=p.chip)
            # Add pin connections
            self.add_pin('pin_cpl4',
                         pins_cpl[3].coords,
                         width=p.cpw_width,
                         input_as_norm=True)

    def make_readout_resonator(self):
        """This function draws the readout resonator.
           Adds pins. And adds the drawn geometry to qgeomtery table.
        """

        p = self.p
        coords_readout = self.make_readout_coordinates()
        circle = self.make_circle()
        pockets = self.make_pockets()
        coords = self.make_coordinates_trap()

        # Make the readout resonator with the pocket
        contact_rdout = draw.Polygon(coords_readout)
        contact_rdout = draw.subtract(circle, contact_rdout)
        contact_rdout = self.make_rotation(contact_rdout, 1)

        # Define contacts
        pocket0 = draw.rectangle(pockets[0], pockets[1])
        pocket0 = draw.translate(pocket0, xoff=0, yoff=(coords[3][1]))
        pocket0 = self.make_rotation(pocket0, 1)

        # Join the coupler and contact
        contact_rdout = draw.union(contact_rdout[0], pocket0[0])

        pins = self.make_pin_coordinates()
        pins_rdout = self.make_rotation(pins, 2)

        objects = [contact_rdout, pins_rdout]
        objects = draw.rotate(objects, p.orientation, origin=(0, 0))
        objects = draw.translate(objects, p.pos_x, p.pos_y)
        [contact_rdout, pins_rdout] = objects

        ##################################################################
        # Add geometry and Qpin connections

        self.add_qgeometry('poly', {'contact_rdout': contact_rdout},
                           subtract=p.subtract,
                           helper=p.helper,
                           layer=p.layer,
                           chip=p.chip)
        self.add_pin('pin_rdout',
                     pins_rdout[0].coords,
                     width=p.cpw_width,
                     input_as_norm=True)

    def make_outer_circle(self):
        """This function draws the outer circle.
        """

        p = self.p

        coords = self.make_coordinates_trap()

        circle_outer = draw.Point(0, 0).buffer(
            p.radius * (1 + (p.connector_length / p.radius)),
            resolution=int(p.resolution),
            cap_style=getattr(CAP_STYLE, p.cap_style))

        #Connectors for the ground plane
        pockets = self.make_pockets()
        pocket_z = draw.rectangle(pockets[0] * 1.4, pockets[1])
        pocket_z = draw.translate(pocket_z, xoff=0, yoff=(coords[2][1]))
        pockets_ground = self.make_rotation(pocket_z, 5)

        if (p.number_of_connectors) == 0:
            circle_outer = draw.union(circle_outer, pockets_ground[2])
        elif (p.number_of_connectors) == 1:
            circle_outer = draw.union(circle_outer, pockets_ground[0],
                                      pockets_ground[2])
        elif (p.number_of_connectors) == 2:
            circle_outer = draw.union(circle_outer, pockets_ground[0],
                                      pockets_ground[1], pockets_ground[2])
        elif (p.number_of_connectors) == 3:
            circle_outer = draw.union(circle_outer, pockets_ground[0],
                                      pockets_ground[1], pockets_ground[2],
                                      pockets_ground[3])
        elif (p.number_of_connectors) == 4:
            circle_outer = draw.union(circle_outer, pockets_ground[0],
                                      pockets_ground[1], pockets_ground[2],
                                      pockets_ground[3], pockets_ground[4])

        ##################################################################
        # Add geometry and Qpin connections
        objects = [circle_outer]
        objects = draw.rotate(objects, p.orientation, origin=(0, 0))
        objects = draw.translate(objects, p.pos_x, p.pos_y)
        [circle_outer] = objects
        self.add_qgeometry('poly', {'circle_outer': circle_outer},
                           subtract=True,
                           helper=p.helper,
                           layer=p.layer,
                           chip=p.chip)
