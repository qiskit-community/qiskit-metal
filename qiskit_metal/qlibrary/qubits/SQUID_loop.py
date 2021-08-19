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
"""SQUID_loop.

.. code-block:
:      
    |                                                   |
    |                                                   |
    |-----seg a-----|JJ|-- seg b-------|                |
    |                                  |              plate 2
    |                                  |                |
  plate1                             seg c ---seg d-----|
    |                                  |                |
    |                                  |                |
    |--seg a lower--|JJ|--seg b lower--|                |
    |                                                   |
    |                                                   |
"""
from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core.base import QComponent
import numpy as np


class SQUID_LOOP(QComponent):
    """
    The base "SQUID_LOOP" inherits the "QComponent" class.

    This creates a simple SQUID loop consisting of two Josephson
    junctions (JJs) located on opposite sides of a rectangular loop.
    The design consists of eight separate rectangles: plate1, 
    segment a (and segment a lower), segment b (and segment b lower),
    segment c, segment d and plate 2. The two JJs are locatd between
    segments and a and b (and also between segments a lower and b
    lower.) 

    Default Options:
        * plate1_width: '5.5um' -- width of plate1 (left)  
        * plate1_height: '40um' -- height of plate1 (left)
        * plate1_x_pos: '0' -- origin of the plate1 (left)
        * plate1_y_pos: '0' -- origin of the plate1 (left) 
        * squid_gap: '10um' -- space between 'seg a' and 'seg a lower'
        * segment_a_length: '10um' -- lenght of seg a
        * segment_a_width: '1um' -- width of seg a 
        * JJ_gap: '0.5um' -- space between seg a and seg b
        * segment_b_length: '5um' -- length of seg b
        * segment_b_width: '1um' -- width of seg b
        * segment_c_width: '10um' -- length of seg c
        * segment_d_length: '10um' -- length of seg d
        * segment_d_width: '2um' -- width of seg d 
        * plate2_width: '6um' -- width of plate 2 (right)
        * plate2_height: '30um' -- height of plate 2 (right)
        * rotation: '0.0' -- rotation angle in degrees
        * x_pos: '0.0' -- final x-coordinate of plate 1 center
        * y_pos: '0.0' -- final y-coordinate of plate 1 center
        * layer: '1' -- layer 1 in design hierarchy
    """
    # Default drawing options
    default_options = Dict(plate1_width='5.5um',
                           plate1_height='40um',
                           plate1_x_pos='0',
                           plate1_y_pos='0',
                           squid_gap='10um',
                           segment_a_length='10um',
                           segment_a_width='1um',
                           JJ_gap='0.5um',
                           segment_b_length='5um',
                           segment_b_width='1um',
                           segment_c_width='1um',
                           segment_d_length='10um',
                           segment_d_width='2um',
                           plate2_width='6um',
                           plate2_height='30um',
                           rotation='0.0',
                           x_pos='0.0',
                           y_pos='0.0',
                           layer='1')
    """Default drawing options"""

    # Name prefix of component, if user doesn't provide name
    component_metadata = Dict(short_name='component')
    """Component metadata"""

    def make(self):
        """Convert self.options into QGeometry."""

        p = self.parse_options()  # Parse the string options into numbers

        # draw the lower pad as a rectangle
        plate1 = draw.rectangle(p.plate1_width, p.plate1_height, p.plate1_x_pos,
                                p.plate1_y_pos)

        segment_a = draw.rectangle(p.segment_a_length, p.segment_a_width,
                                   0.5 * (p.plate1_width + p.segment_a_length),
                                   0.5 * (p.squid_gap + p.segment_a_width))

        segment_a_lower = draw.translate(
            segment_a, 0.0, -1.0 * (p.squid_gap + p.segment_a_width))

        segment_b = draw.rectangle(
            p.segment_b_length, p.segment_b_width,
            0.5 * (p.plate1_width + p.segment_b_length) + p.JJ_gap +
            p.segment_a_length, 0.5 * (p.squid_gap + p.segment_b_width))

        segment_b_lower = draw.translate(
            segment_b, 0.0, -1.0 * (p.squid_gap + p.segment_b_width))

        segment_c = draw.rectangle(
            p.segment_c_width,
            p.squid_gap + p.segment_a_width + p.segment_b_width,
            0.5 * (p.plate1_width + p.segment_c_width) + p.segment_a_length +
            p.segment_b_length + p.JJ_gap, p.plate1_y_pos)

        segment_d = draw.rectangle(
            p.segment_d_length, p.segment_d_width,
            0.5 * (p.plate1_width + p.segment_d_length) + p.segment_a_length +
            p.segment_b_length + p.JJ_gap + p.segment_c_width, p.plate1_y_pos)

        plate2 = draw.rectangle(
            p.plate2_width, p.plate2_height, 0.5 *
            (p.plate1_width + p.plate2_width) + p.segment_a_length + p.JJ_gap +
            p.segment_b_length + p.segment_c_width + p.segment_d_length,
            p.plate1_y_pos)

        design1 = draw.union(plate1, segment_a, segment_a_lower, segment_b,
                             segment_b_lower, segment_c, segment_d, plate2)

        # now translate and rotate the final structure
        design1 = draw.rotate(design1, p.rotation, origin=(0, 0))
        design1 = draw.translate(design1, p.x_pos, p.y_pos)

        geom = {'design': design1}
        self.add_qgeometry('poly', geom, layer=p.layer, subtract=False)
