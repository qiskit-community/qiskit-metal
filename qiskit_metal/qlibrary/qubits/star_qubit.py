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
        y1 = '-100um', # y-coordinate of the trapezoid
        y2 = '-300um', # y-coordinate of the trapezoid
        x1 = '-50um', # x-coordinate of the trapezoid
        x2 = '50um', # x-coordinate of the trapezoid
        x3 = '120um', # x-coordinate of the trapezoid
        x4 = '-120um', # x-coordinate of the trapezoid
        a1 = '-130um', # y-coordinate of the polygon defining the coupling resonator
        a2 = '-300um', # y-coordinate of the polygon defining the coupling resonator
        a3 = '300um', # y-coordinate of the polygon defining the coupling resonator
        b1 = '-25um', # x-coordinate of the polygon defining the coupling resonator
        b2 = '25um', # x-coordinate of the polygon defining the coupling resonator
        b3 = '75um', # x-coordinate of the polygon defining the coupling resonator
        b4 = '-75um', # x-coordinate of the polygon defining the coupling resonator
        b5 = '-300um', # x-coordinate of the polygon defining the coupling resonator
        b6 = '300um', # x-coordinate of the polygon defining the coupling resonator   
        c1 = '-115um', # y-coordinate of the polygon defining the readout resonator
        c2 = '-300um', # y-coordinate of the polygon defining the readout resonator
        c3 = '300um', # y-coordinate of the polygon defining the readout resonator
        d1 = '-40um', # x-coordinate of the polygon defining the readout resonator
        d2 = '40um', # x-coordinate of the polygon defining the readout resonator
        d3 = '100um', # x-coordinate of the polygon defining the readout resonator
        d4 = '-100um', # x-coordinate of the polygon defining the readout resonator
        d5 = '-300um', # x-coordinate of the polygon defining the readout resonator
        d6 = '300um', # x-coordinate of the polygon defining the readout resonator
        junc_w = '120um', # junction width
        junc_h = '5um', # junction height
        pocket_w='70um',  # connector pocket width
        pocket_h='150um',  # connector pocket height    
        pocket_w1='2um',  # connector pocket width
        pocket_h1='20um',  # connector pocket height 
        pocket_w2='2um',  # connector pocket width
        pocket_h2='20um',  # connector pocket height 
        rotation1 = '72.0', # rotation for one of the coupling resonators 
        rotation2 = '144.0', # rotation for the readout resonator
        rotation3 = '216.0', # rotation for one of the coupling resonators 
        rotation4 = '288.0', # rotation for one of the coupling resonators 
        pos_x='0um',
        pos_y='0um',
        resolution='16',
        cap_style='round',  # round, flat, square
        # join_style = 'round', # round, mitre, bevel
        # Connections
        # General
        subtract='False',
        helper='False',
        chip='main',
        layer='1',
    )
    """Default drawing options"""

    def make(self):
        """The make function implements the logic that creates the geoemtry
        (poly, path, etc.) from the qcomponent.options dictionary of
        parameters, and the adds them to the design, using
        qcomponent.add_qgeometry(...), adding in extra needed information, such
        as layer, subtract, etc."""
        p = self.p  # p for parsed parameters. Access to the parsed options.

        # create a circle
        circle = draw.Point(p.pos_x, p.pos_y).buffer(
            p.radius,
            resolution=int(p.resolution),
            cap_style=getattr(CAP_STYLE, p.cap_style)
        )
            #join_style = getattr(JOIN_STYLE, p.join_style)
        
        # create the trapezoids
        coords1 = [(p.x1,p.y1),(p.x2,p.y1),(p.x3,p.y2),(p.x4,p.y2)]
        trap_1 = draw.Polygon(coords1)
        coords2 = [(p.x1,p.y1),(p.x2,p.y1),(p.x3,p.y2),(p.x4,p.y2)]
        trap_2 = draw.Polygon(coords2)
        trap_2 = draw.rotate(trap_2, p.rotation1, origin=(0, 0))
        coords3 = [(p.x1,p.y1),(p.x2,p.y1),(p.x3,p.y2),(p.x4,p.y2)]
        trap_3 = draw.Polygon(coords3)
        trap_3 = draw.rotate(trap_3, p.rotation2, origin=(0, 0))
        coords4 = [(p.x1,p.y1),(p.x2,p.y1),(p.x3,p.y2),(p.x4,p.y2)]
        trap_4 = draw.Polygon(coords4)
        trap_4 = draw.rotate(trap_4, p.rotation3, origin=(0, 0))
        coords5 = [(p.x1,p.y1),(p.x2,p.y1),(p.x3,p.y2),(p.x4,p.y2)]
        trap_5 = draw.Polygon(coords5)
        trap_5 = draw.rotate(trap_5, p.rotation4, origin=(0, 0))

        # Define the connectors
        coords_coupling_resonator = [(p.b1,p.a1),(p.b2,p.a1),(p.b3,p.a2),(p.b6,p.a2),(p.b6,p.a3),(p.b5,p.a3),(p.b5,p.a2),(p.b4,p.a2)]
        trap_a = draw.Polygon(coords_coupling_resonator)
        trap_b = draw.rotate(trap_a, p.rotation1, origin=(0, 0))
        trap_d = draw.rotate(trap_a, p.rotation3, origin=(0, 0))
        trap_e = draw.rotate(trap_a, p.rotation4, origin=(0, 0))
        coords_readout = [(p.d1,p.c1),(p.d2,p.c1),(p.d3,p.c2),(p.d6,p.c2),(p.d6,p.c3),(p.d5,p.c3),(p.d5,p.c2),(p.d4,p.c2)]
        trap_c = draw.Polygon(coords_readout)
        trap_c = draw.rotate(trap_c, p.rotation2, origin=(0, 0))
        rect1 = draw.rectangle(p.pocket_w1, p.pocket_h1)
        rect1 = draw.translate(rect1, xoff=p.b2, yoff=p.a3)
        rect2 = draw.rectangle(p.pocket_w2, p.pocket_h2)
        rect2 = draw.translate(rect2, xoff=p.b1, yoff=p.a3)


        # Define contacts
        pocket1 = draw.rectangle(p.pocket_w, p.pocket_h)
        pocket1 = draw.translate(pocket1, yoff=p.y2)
        pocket2 = draw.rotate(pocket1, p.rotation1, origin=(0, 0))
        pocket3 = draw.rotate(pocket1, p.rotation2, origin=(0, 0))
        pocket4 = draw.rotate(pocket1, p.rotation3, origin=(0, 0))
        pocket5 = draw.rotate(pocket1, p.rotation4, origin=(0, 0))

        #junction
        pocket6 = draw.rectangle(p.junc_w, p.junc_h)
        pocket6 = draw.translate(pocket6, yoff=1.05*(p.a3))

        # Join all trapezoids
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

        # add qgeometry
        self.add_qgeometry('poly', {'circle': total},
                           subtract=p.subtract,
                           helper=p.helper,
                           layer=p.layer,
                           chip=p.chip)
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
        self.add_qgeometry('junction', {'circle': pocket6},
                           subtract=p.subtract,
                           helper=p.helper,
                           layer=p.layer,
                           chip=p.chip,
                           width=p.junc_h)
#########################################################################################
        # Add Qpin connections
        p_in=(0,p.y2)
        p_out=(0,1.25*p.y2)
        pins=draw.LineString([p_in, p_out])
        
        self.add_pin('pin1',
                     pins.coords,
                     width=0.01,
                     input_as_norm=True)

        # Define second pin
        pins2=draw.rotate(pins, p.rotation1, origin=(0, 0))
        self.add_pin('pin2',
                     pins2.coords,
                     width=0.01,
                     input_as_norm=True)

        # Define third pin
        pins3=draw.rotate(pins, p.rotation2, origin=(0, 0))
        self.add_pin('pin3',
                     pins3.coords,
                     width=0.01,
                     input_as_norm=True)

        # Define fourth pin
        pins4=draw.rotate(pins, p.rotation3, origin=(0, 0))
        self.add_pin('pin4',
                     pins4.coords,
                     width=0.01,
                     input_as_norm=True)

        # Define fifth pin
        pins5=draw.rotate(pins, p.rotation4, origin=(0, 0))
        self.add_pin('pin5',
                     pins5.coords,
                     width=0.01,
                     input_as_norm=True)