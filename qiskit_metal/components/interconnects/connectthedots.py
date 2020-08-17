# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

'''
@date: 2020
@author: Dennis Wang
'''

import numpy as np
from collections import OrderedDict
from qiskit_metal import draw, Dict
from qiskit_metal.components import QComponent

class ConnectTheDots(QComponent):

    """
    08/14/20: Used only for reproduction of non-meandered CPWs on BlueJay.
    Creates and connects a series of anchors through which the CPW passes.
    This class is basically pathfinder.py with no built-in collision
    avoidance and no A* algorithm.
    """

    default_options = Dict(
        pin_inputs=Dict(
            start_pin=Dict(
                component='', # Name of component to start from, which has a pin
                pin=''), # Name of pin used for pin_start
            end_pin=Dict(
                component='', # Name of component to end on, which has a pin
                pin='') # Name of pin used for pin_end
                ),
        chip='main',
        layer='1',
        leadin=Dict(
            start='22um',
            end='22um'),
        cpw_width='cpw_width',
        cpw_gap='cpw_gap',
        anchors=OrderedDict() # Intermediate anchors only; doesn't include endpoints
        # Example: {1: np.array([x1, y1]), 2: np.array([x2, y2])}
        # startpin -> startpin + leadin -> anchors -> endpin + leadout -> endpin
    )

    def getpts_simple(self, start_direction: np.array, start: np.array, end: np.array, end_direction=None) -> list:

        """
        Connect start and end with single or 2-segment/S-shaped CPWs ignoring collision avoidance.
        
        Args:
            start_direction (np.array): Vector indicating direction of starting point
            start (np.array): 2-D coordinates of first anchor
            end (np.array): 2-D coordinates of second anchor

        Returns:
            List of vertices of a CPW going from start to end
        """

        # end_direction originates strictly from endpoint + leadout (NOT intermediate stopping anchors)
        # stop_direction aligned with longer rectangle edge regardless of nature of 2nd anchor

        offsetx = abs(end[0] - start[0]) # Absolute value of displacement between start and end in x direction
        offsety = abs(end[1] - start[1]) # Absolute value of displacement between start and end in y direction
        if offsetx >= offsety: # "Wide" rectangle -> end_arrow points along x
            stop_direction = np.array([end[0] - start[0], 0])
        else: # "Tall" rectangle -> end_arrow points along y
            stop_direction = np.array([0, end[1] - start[1]])

        if (start[0] == end[0]) or (start[1] == end[1]):
            # Matching x or y coordinates -> check if endpoints can be connected with a single segment
            if np.dot(start_direction, end - start) >= 0:
                # Start direction and end - start for CPW must not be anti-aligned
                if (end_direction is None) or (np.dot(end - start, end_direction) <= 0):
                    # If leadout + end has been reached, the single segment CPW must not be aligned with its direction
                    return [start, end]
        else:
            # If the endpoints don't share a common x or y value, designate them as 2 corners of an axis aligned rectangle
            # and check if both start and end directions are aligned with the displacement vectors between start/end and
            # either of the 2 remaining corners ("perfect alignment").
            corner1 = np.array([start[0], end[1]]) # x coordinate matches with start
            corner2 = np.array([end[0], start[1]]) # x coordinate matches with end
            # Check for collisions at the outset to avoid repeat work
            if np.dot(start_direction, corner1 - start) > 0:
                if (end_direction is None) or (np.dot(end_direction, corner1 - end) > 0):
                    return [start, corner1, end]
            elif np.dot(start_direction, corner2 - start) > 0:
                if (end_direction is None) or (np.dot(end_direction, corner2 - end) > 0):
                    return [start, corner2, end]
            # In notation below, corners 3 and 4 correspond to the ends of the segment bisecting the longer rectangle formed by start and end
            # while the segment formed by corners 5 and 6 bisect the shorter rectangle
            if stop_direction[0]: # "Wide" rectangle -> vertical middle segment is more natural
                corner3 = np.array([(start[0] + end[0]) / 2, start[1]])
                corner4 = np.array([(start[0] + end[0]) / 2, end[1]])
                corner5 = np.array([start[0], (start[1] + end[1]) / 2])
                corner6 = np.array([end[0], (start[1] + end[1]) / 2])
            else: # "Tall" rectangle -> horizontal middle segment is more natural
                corner3 = np.array([start[0], (start[1] + end[1]) / 2])
                corner4 = np.array([end[0], (start[1] + end[1]) / 2])
                corner5 = np.array([(start[0] + end[0]) / 2, start[1]])
                corner6 = np.array([(start[0] + end[0]) / 2, end[1]])
            if (np.dot(start_direction, stop_direction) < 0) and (np.dot(start_direction, corner3 - start) > 0):
                if (end_direction is None) or (np.dot(end_direction, corner4 - end) > 0):
                    # Perfectly aligned S-shaped CPW
                    return [start, corner3, corner4, end]
            # Relax constraints and check if imperfect 2-segment or S-segment works, where "imperfect" means 1 or more dot products of directions
            # between successive segments is 0; otherwise return an empty list
            if np.dot(start_direction, corner1 - start) >= 0:
                if (end_direction is None) or (np.dot(end_direction, corner1 - end) >= 0):
                    return [start, corner1, end]
            if np.dot(start_direction, corner2 - start) >= 0:
                if (end_direction is None) or (np.dot(end_direction, corner2 - end) >= 0):
                    return [start, corner2, end]
            if np.dot(start_direction, corner3 - start) >= 0:
                if (end_direction is None) or (np.dot(end_direction, corner4 - end) >= 0):
                    return [start, corner3, corner4, end]
            if np.dot(start_direction, corner5 - start) >= 0:
                if (end_direction is None) or (np.dot(end_direction, corner6 - end) >= 0):
                    return [start, corner5, corner6, end]

    def make(self):
        """
        Generates path from start pin to end pin.
        """
        p = self.parse_options()
        leadstart = p.leadin.start
        leadend = p.leadin.end
        w = p.cpw_width
        anchors = p.anchors

        component_start = p.pin_inputs['start_pin']['component']
        pin_start = p.pin_inputs['start_pin']['pin']
        component_end = p.pin_inputs['end_pin']['component']
        pin_end = p.pin_inputs['end_pin']['pin']

        # Starting and ending pin (connector) dictionaries
        connector1 = self.design.components[component_start].pins[pin_start] # startpin
        connector2 = self.design.components[component_end].pins[pin_end] # endpin

        n1 = connector1.normal
        n2 = connector2.normal

        m1 = connector1.middle
        m2 = connector2.middle

        self._pts = [m1, m1 + n1 * (w / 2 + leadstart)] # Initialize list of vertices with startpin

        for coord in list(anchors.values()):
            # Process startpin + leadin, anchors, and endpin + leadout
            self._pts += self.getpts_simple(self._pts[-1] - self._pts[-2], self._pts[-1], coord)[1:]
        # Treat endpin + leadout as an edge case since CPW cannot overlap with it, in which case we must specify an end direction
        penultimate_pt = m2 + n2 * (w / 2 + leadend) # penultimate_pt = endpin + leadout
        # n2 originates from m2 and points towards penultimate_pt

        self._pts += self.getpts_simple(self._pts[-1] - self._pts[-2], self._pts[-1], penultimate_pt, n2)[1:]
        self._pts += [m2] # Add endpin

        # Create CPW geometry using list of vertices
        line = draw.LineString(self._pts)

        # Add CPW to elements table
        self.add_qgeometry('path', {'center_trace': line}, width=p.cpw_width, layer=p.layer)
        self.add_qgeometry('path', {'gnd_cut': line}, width=p.cpw_width+2*p.cpw_gap, subtract=True)

        # Create new pins for the CPW itself
        self.add_pin('simple_start', connector1.points[::-1], p.cpw_width)
        self.add_pin('simple_end', connector2.points[::-1], p.cpw_width)

        # Add to netlist
        self.design.connect_pins(self.design.components[component_start].id, pin_start, self.id, 'simple_start')
        self.design.connect_pins(self.design.components[component_end].id, pin_end, self.id, 'simple_end')
        