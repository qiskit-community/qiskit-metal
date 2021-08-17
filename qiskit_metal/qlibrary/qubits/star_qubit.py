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
"""This is the CircleCaterpillar module."""

from qiskit_metal import draw, Dict  # , QComponent
from qiskit_metal.qlibrary.core import QComponent
from shapely.geometry import CAP_STYLE
import numpy as np


class StarQubit(QComponent):
    """A single configurable circle.

    Inherits QComponent class.

    Default Options:
        * radius: '300um'
        * pos_x: '0um'
        * pos_y: '0um'
        * resolution: '16'
        * cap_style: 'round' -- Valid options are 'round', 'flat', 'square'
        * subtract: 'False'
        * helper: 'False'
        * chip: 'main'
        * layer: '1'
    """

    default_options = dict(
        radius='300um', # radius of the circle defining the star shape
        center_radius='100um', # Measure of how thick the central island is
        gap_couplers='25um', # Gap between the star and the coupling resonator
        gap_readout='10um', # Gap between the star and the readout resonator
        connector_length='75um', # Length of the rectangular part of the connector
        trap_offset='20um', #The offset between coordinates of the trpezoid to define the side wall angle
        junc_w = '120um', # junction width
        junc_h = '10um', # junction height  
        rotation1 = '72.0', # rotation for one of the coupling resonators 
        rotation2 = '144.0', # rotation for the readout resonator
        rotation3 = '216.0', # rotation for one of the coupling resonators 
        rotation4 = '288.0', # rotation for one of the coupling resonators 
        pos_x='0um',
        pos_y='0um',
        number_of_connectors='4', # Total number of coupling resonators
        resolution='16',
        cap_style='round',  # round, flat, square
        # join_style = 'round', # round, mitre, bevel
        # Connections
        # General
        subtract='False',
        helper='False',
        chip='main',
        layer='1'
    )
    """Default drawing options"""

    def make(self):
        """The make function implements the logic that creates the geoemtry
        (poly, path, etc.) from the qcomponent.options dictionary of
        parameters, and the adds them to the design, using
        qcomponent.add_qgeometry(...), adding in extra needed information, such
        as layer, subtract, etc."""
        p = self.p  # p for parsed parameters. Access to the parsed options.

        # Extracting coordinated from the user input values
        y1 = -p.center_radius # y-coordinate of the trapezoid
        y2 = -p.radius # y-coordinate of the trapezoid
        x1 = -p.center_radius/2 # x-coordinate of the trapezoid
        x2 = p.center_radius/2 # x-coordinate of the trapezoid
        x3 = p.center_radius + p.trap_offset # x-coordinate of the trapezoid
        x4 = -(p.center_radius + p.trap_offset) # x-coordinate of the trapezoid
        a1 = -(p.center_radius+p.gap_couplers) # y-coordinate of the polygon defining the coupling resonator
        a2 = -p.radius # y-coordinate of the polygon defining the coupling resonator
        a3 = p.radius # y-coordinate of the polygon defining the coupling resonator
        b1 = -p.center_radius/4 # x-coordinate of the polygon defining the coupling resonator
        b2 = p.center_radius/4 # x-coordinate of the polygon defining the coupling resonator
        b3 = (p.center_radius-p.gap_couplers) # x-coordinate of the polygon defining the coupling resonator
        b4 = -(p.center_radius-p.gap_couplers) # x-coordinate of the polygon defining the coupling resonator
        b5 = -p.radius # x-coordinate of the polygon defining the coupling resonator
        b6 = p.radius # x-coordinate of the polygon defining the coupling resonator   
        c1 = -(p.center_radius+p.gap_readout) # y-coordinate of the polygon defining the readout resonator
        c2 = -p.radius # y-coordinate of the polygon defining the readout resonator
        c3 = p.radius # y-coordinate of the polygon defining the readout resonator
        d1 = -(p.center_radius/2 - p.gap_readout) # x-coordinate of the polygon defining the readout resonator
        d2 =  p.center_radius/2- p.gap_readout # x-coordinate of the polygon defining the readout resonator
        d3 = p.center_radius # x-coordinate of the polygon defining the readout resonator
        d4 = -p.center_radius # x-coordinate of the polygon defining the readout resonator
        d5 = -p.radius # x-coordinate of the polygon defining the readout resonator
        d6 = p.radius # x-coordinate of the polygon defining the readout resonator
        pocket_w= p.connector_length  # connector pocket width
        pocket_h=p.connector_length*2  # connector pocket height    
        pocket_w1=p.gap_couplers  # Connector to the JJ
        pocket_h1=p.center_radius # Connector to the JJ  
        rotation1 = 72.0 # rotation for one of the coupling resonators 
        rotation2 = 144.0 # rotation for the readout resonator
        rotation3 = 216.0 # rotation for one of the coupling resonators 
        rotation4 = 288.0 # rotation for one of the coupling resonators

        # create a circle
        circle = draw.Point(p.pos_x, p.pos_y).buffer(
            p.radius,
            resolution=int(p.resolution),
            cap_style=getattr(CAP_STYLE, p.cap_style)
        )

        circle_outer = draw.Point(p.pos_x, p.pos_y).buffer(
            p.radius*1.2,
            resolution=int(p.resolution),
            cap_style=getattr(CAP_STYLE, p.cap_style)
        )
        #join_style = getattr(JOIN_STYLE, p.join_style)
        # create the trapezoids
        coords1 = [(x1,y1),(x2,y1),(x3,y2),(x4,y2)]
        trap_1 = draw.Polygon(coords1)
        coords2 = [(x1,y1),(x2,y1),(x3,y2),(x4,y2)]
        trap_2 = draw.Polygon(coords2)
        trap_2 = draw.rotate(trap_2, rotation1, origin=(0, 0))
        coords3 = [(x1,y1),(x2,y1),(x3,y2),(x4,y2)]
        trap_3 = draw.Polygon(coords3)
        trap_3 = draw.rotate(trap_3, rotation2, origin=(0, 0))
        coords4 = [(x1,y1),(x2,y1),(x3,y2),(x4,y2)]
        trap_4 = draw.Polygon(coords4)
        trap_4 = draw.rotate(trap_4, rotation3, origin=(0, 0))
        coords5 = [(x1,y1),(x2,y1),(x3,y2),(x4,y2)]
        trap_5 = draw.Polygon(coords5)
        trap_5 = draw.rotate(trap_5, rotation4, origin=(0, 0))

        # Define the connectors
        coords_coupling_resonator = [(b1,a1),(b2,a1),(b3,a2),(b6,a2),(b6,a3),(b5,a3),(b5,a2),(b4,a2)]
        trap_a = draw.Polygon(coords_coupling_resonator)
        trap_b = draw.rotate(trap_a, rotation1, origin=(0, 0))
        trap_d = draw.rotate(trap_a, rotation3, origin=(0, 0))
        trap_e = draw.rotate(trap_a, rotation4, origin=(0, 0))
        coords_readout = [(d1,c1),(d2,c1),(d3,c2),(d6,c2),(d6,c3),(d5,c3),(d5,c2),(d4,c2)]
        trap_c = draw.Polygon(coords_readout)
        trap_c = draw.rotate(trap_c, rotation2, origin=(0, 0))
        rect1 = draw.rectangle(pocket_w1, pocket_h1)
        rect1 = draw.translate(rect1, xoff=b2, yoff=a3)
        rect2 = draw.rectangle(pocket_w1, pocket_h1)
        rect2 = draw.translate(rect2, xoff=b1, yoff=a3)


        # Define contacts
        pocket1 = draw.rectangle(pocket_w, pocket_h)
        pocket1 = draw.translate(pocket1, yoff=y2)
        pocket2 = draw.rotate(pocket1, rotation1, origin=(0, 0))
        pocket3 = draw.rotate(pocket1, rotation2, origin=(0, 0))
        pocket4 = draw.rotate(pocket1, rotation3, origin=(0, 0))
        pocket5 = draw.rotate(pocket1, rotation4, origin=(0, 0))

        #Connectors for the ground plane
        pocketA = draw.rectangle(pocket_w*1.4, pocket_h)
        pocketA = draw.translate(pocketA, yoff=y2)
        pocketB = draw.rotate(pocketA, rotation1, origin=(0, 0))
        pocketC = draw.rotate(pocketA, rotation2, origin=(0, 0))
        pocketD = draw.rotate(pocketA, rotation3, origin=(0, 0))
        pocketE = draw.rotate(pocketA, rotation4, origin=(0, 0))
        circle_outer = draw.union(circle_outer,pocketA,pocketB,pocketC,pocketD,pocketE)

        #junction
        pocket6 = draw.rectangle(p.junc_w, p.junc_h)
        pocket6 = draw.translate(pocket6, yoff=1.2*(a3))

        # Define the final structure based on use input on how many connectors are needed
        if (p.number_of_connectors) ==0:
            traps = trap_3
        elif (p.number_of_connectors) ==1:
            traps = draw.union(trap_1, trap_3)
        elif (p.number_of_connectors) ==2:
            traps = draw.union(trap_1, trap_2, trap_3)
        elif (p.number_of_connectors) ==3:
            traps = draw.union(trap_1, trap_2, trap_3, trap_4)
        elif (p.number_of_connectors) ==4:
            traps = draw.union(trap_1, trap_2, trap_3, trap_4, trap_5)

        # Subtract
        total1 = draw.subtract(circle, traps)
        # Add connection to the junction
        total = draw.union(total1, rect1, rect2)

        contact1 = draw.subtract(circle,trap_a)
        contact1 = draw.union(contact1,pocket1)
        contact2 = draw.subtract(circle,trap_b)
        contact2 = draw.union(contact2,pocket2)
        contact3 = draw.subtract(circle,trap_c)
        contact3 = draw.union(contact3,pocket3)
        contact4 = draw.subtract(circle,trap_d)
        contact4 = draw.union(contact4,pocket4)
        contact5 = draw.subtract(circle,trap_e)
        contact5 = draw.union(contact5,pocket5)

        #########################################################################################
        # Add geometry and Qpin connections
        p_in=(0,y2)
        p_out=(0,1.25*y2)
        pins=draw.LineString([p_in, p_out])

        self.add_qgeometry('poly', {'circle': total},
                           subtract=p.subtract,
                           helper=p.helper,
                           layer=p.layer,
                           chip=p.chip)
        if (p.number_of_connectors) ==0:
            self.add_qgeometry('poly', {'circle': contact3},
                            subtract=p.subtract,
                            helper=p.helper,
                            layer=p.layer,
                            chip=p.chip)

            pins3=draw.rotate(pins, rotation2, origin=(0, 0))
            self.add_pin('pin3',
                     pins3.coords,
                     width=0.01,
                     input_as_norm=True)
        
        elif (p.number_of_connectors) ==1:
            self.add_qgeometry('poly', {'circle': contact1},
                            subtract=p.subtract,
                            helper=p.helper,
                            layer=p.layer,
                            chip=p.chip)
            self.add_qgeometry('poly', {'circle': contact3},
                            subtract=p.subtract,
                            helper=p.helper,
                            layer=p.layer,
                            chip=p.chip)
            # Add pin connections
            self.add_pin('pin1',
                     pins.coords,
                     width=0.01,
                     input_as_norm=True)

            pins3=draw.rotate(pins, rotation2, origin=(0, 0))
            self.add_pin('pin3',
                     pins3.coords,
                     width=0.01,
                     input_as_norm=True)


        elif (p.number_of_connectors) ==2:
            self.add_qgeometry('poly', {'circle': contact1},
                            subtract=p.subtract,
                            helper=p.helper,
                            layer=p.layer,
                            chip=p.chip)
            self.add_qgeometry('poly', {'circle': contact2},
                            subtract=p.subtract,
                            helper=p.helper,
                            layer=p.layer,
                            chip=p.chip)
            self.add_qgeometry('poly', {'circle': contact3},
                            subtract=p.subtract,
                            helper=p.helper,
                            layer=p.layer,
                            chip=p.chip)
            # Add pin connections
            self.add_pin('pin1',
                        pins.coords,
                        width=0.01,
                        input_as_norm=True)

            # Define second pin
            pins2=draw.rotate(pins, rotation1, origin=(0, 0))
            self.add_pin('pin2',
                        pins2.coords,
                        width=0.01,
                        input_as_norm=True)

            # Define third pin
            pins3=draw.rotate(pins, rotation2, origin=(0, 0))
            self.add_pin('pin3',
                        pins3.coords,
                        width=0.01,
                        input_as_norm=True)

        elif (p.number_of_connectors) ==3:
            self.add_qgeometry('poly', {'circle': contact1},
                            subtract=p.subtract,
                            helper=p.helper,
                            layer=p.layer,
                            chip=p.chip)
            self.add_qgeometry('poly', {'circle': contact2},
                            subtract=p.subtract,
                            helper=p.helper,
                            layer=p.layer,
                            chip=p.chip)
            self.add_qgeometry('poly', {'circle': contact3},
                            subtract=p.subtract,
                            helper=p.helper,
                            layer=p.layer,
                            chip=p.chip)
            self.add_qgeometry('poly', {'circle': contact4},
                            subtract=p.subtract,
                            helper=p.helper,
                            layer=p.layer,
                            chip=p.chip)
            # Add pin connections
            self.add_pin('pin1',
                        pins.coords,
                        width=0.01,
                        input_as_norm=True)

            # Define second pin
            pins2=draw.rotate(pins, rotation1, origin=(0, 0))
            self.add_pin('pin2',
                        pins2.coords,
                        width=0.01,
                        input_as_norm=True)

            # Define third pin
            pins3=draw.rotate(pins, rotation2, origin=(0, 0))
            self.add_pin('pin3',
                        pins3.coords,
                        width=0.01,
                        input_as_norm=True)

            # Define fourth pin
            pins4=draw.rotate(pins, rotation3, origin=(0, 0))
            self.add_pin('pin4',
                        pins4.coords,
                        width=0.01,
                        input_as_norm=True)

        elif (p.number_of_connectors) ==4:
            self.add_qgeometry('poly', {'circle': contact1},
                            subtract=p.subtract,
                            helper=p.helper,
                            layer=p.layer,
                            chip=p.chip)
            self.add_qgeometry('poly', {'circle': contact2},
                            subtract=p.subtract,
                            helper=p.helper,
                            layer=p.layer,
                            chip=p.chip)
            self.add_qgeometry('poly', {'circle': contact3},
                            subtract=p.subtract,
                            helper=p.helper,
                            layer=p.layer,
                            chip=p.chip)
            self.add_qgeometry('poly', {'circle': contact4},
                            subtract=p.subtract,
                            helper=p.helper,
                            layer=p.layer,
                            chip=p.chip)
            self.add_qgeometry('poly', {'circle': contact5},
                            subtract=p.subtract,
                            helper=p.helper,
                            layer=p.layer,
                            chip=p.chip)   
            # Add pin connections
            self.add_pin('pin1',
                        pins.coords,
                        width=0.01,
                        input_as_norm=True)

            # Define second pin
            pins2=draw.rotate(pins, rotation1, origin=(0, 0))
            self.add_pin('pin2',
                        pins2.coords,
                        width=0.01,
                        input_as_norm=True)

            # Define third pin
            pins3=draw.rotate(pins, rotation2, origin=(0, 0))
            self.add_pin('pin3',
                        pins3.coords,
                        width=0.01,
                        input_as_norm=True)

            # Define fourth pin
            pins4=draw.rotate(pins, rotation3, origin=(0, 0))
            self.add_pin('pin4',
                        pins4.coords,
                        width=0.01,
                        input_as_norm=True)

            # Define fifth pin
            pins5=draw.rotate(pins, rotation4, origin=(0, 0))
            self.add_pin('pin5',
                        pins5.coords,
                        width=0.01,
                        input_as_norm=True)
        self.add_qgeometry('junction', {'circle': pocket6},
                           subtract=p.subtract,
                           helper=p.helper,
                           layer=p.layer,
                           chip=p.chip,
                           width=p.junc_h)
        self.add_qgeometry('poly', {'circle': circle_outer},
                           subtract=True,
                           helper=p.helper,
                           layer=p.layer,
                           chip=p.chip)