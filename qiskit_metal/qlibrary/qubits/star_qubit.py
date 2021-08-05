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
        radius='300um',
        y1 = '-100um',
        y2 = '-300um',
        x1 = '-50um',
        x2 = '50um',
        x3 = '120um',
        x4 = '-120um',
        a1 = '-130um',
        a2 = '-300um',
        a3 = '300um',
        b1 = '-25um',
        b2 = '25um',
        b3 = '75um',
        b4 = '-75um',
        b5 = '-300um',
        b6 = '300um',    
        c1 = '-115um',
        c2 = '-300um',
        c3 = '300um',
        d1 = '-40um',
        d2 = '40um',
        d3 = '100um',
        d4 = '-100um',
        d5 = '-300um',
        d6 = '300um', 
        pocket_w='70um',  # connector pocket width
        pocket_h='150um',  # connector pocket height    
        rotation1 = '72.0',
        rotation2 = '144.0',
        rotation3 = '216.0',
        rotation4 = '288.0',
        pos_x='0um',
        pos_y='0um',
        resolution='16',
        cap_style='round',  # round, flat, square
        # join_style = 'round', # round, mitre, bevel
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
        coordsA = [(p.b1,p.a1),(p.b2,p.a1),(p.b3,p.a2),(p.b6,p.a2),(p.b6,p.a3),(p.b5,p.a3),(p.b5,p.a2),(p.b4,p.a2)]
        trap_a = draw.Polygon(coordsA)
        coordsB = [(p.b1,p.a1),(p.b2,p.a1),(p.b3,p.a2),(p.b6,p.a2),(p.b6,p.a3),(p.b5,p.a3),(p.b5,p.a2),(p.b4,p.a2)]
        trap_b = draw.Polygon(coordsB)
        trap_b = draw.rotate(trap_b, p.rotation1, origin=(0, 0))
        coordsC = [(p.d1,p.c1),(p.d2,p.c1),(p.d3,p.c2),(p.d6,p.c2),(p.d6,p.c3),(p.d5,p.c3),(p.d5,p.c2),(p.d4,p.c2)]
        trap_c = draw.Polygon(coordsC)
        trap_c = draw.rotate(trap_c, p.rotation2, origin=(0, 0))
        coordsD = [(p.b1,p.a1),(p.b2,p.a1),(p.b3,p.a2),(p.b6,p.a2),(p.b6,p.a3),(p.b5,p.a3),(p.b5,p.a2),(p.b4,p.a2)]
        trap_d = draw.Polygon(coordsD)
        trap_d = draw.rotate(trap_d, p.rotation3, origin=(0, 0))
        coordsE = [(p.b1,p.a1),(p.b2,p.a1),(p.b3,p.a2),(p.b6,p.a2),(p.b6,p.a3),(p.b5,p.a3),(p.b5,p.a2),(p.b4,p.a2)]
        trap_e = draw.Polygon(coordsE)
        trap_e = draw.rotate(trap_e, p.rotation4, origin=(0, 0))

        # Define contacts
        pocket1 = draw.rectangle(p.pocket_w, p.pocket_h)
        pocket1 = draw.translate(pocket1, yoff=p.y2)

        pocket2 = draw.rectangle(p.pocket_w, p.pocket_h)
        pocket2 = draw.translate(pocket2, yoff=p.y2)
        pocket2 = draw.rotate(pocket2, p.rotation1, origin=(0, 0))

        pocket3 = draw.rectangle(p.pocket_w, p.pocket_h)
        pocket3 = draw.translate(pocket3, yoff=p.y2)
        pocket3 = draw.rotate(pocket3, p.rotation2, origin=(0, 0))

        pocket4 = draw.rectangle(p.pocket_w, p.pocket_h)
        pocket4 = draw.translate(pocket4, yoff=p.y2)
        pocket4 = draw.rotate(pocket4, p.rotation3, origin=(0, 0))

        pocket5 = draw.rectangle(p.pocket_w, p.pocket_h)
        pocket5 = draw.translate(pocket5, yoff=p.y2)
        pocket5 = draw.rotate(pocket5, p.rotation4, origin=(0, 0))


        # Subtract
        total1 = draw.subtract(circle, trap_1)
        total2 = draw.subtract(total1, trap_2)
        total3 = draw.subtract(total2, trap_3)
        total4 = draw.subtract(total3, trap_4)
        total = draw.subtract(total4, trap_5)

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
        self.add_qgeometry('junction', {'circle': contact5},
                           subtract=p.subtract,
                           helper=p.helper,
                           layer=p.layer,
                           chip=p.chip)