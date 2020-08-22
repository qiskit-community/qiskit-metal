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
@author: Dennis Wang, Marco Facchini
'''

import numpy as np
from collections import OrderedDict
from qiskit_metal import draw, Dict
from qiskit_metal.components.base import QRoute, QRoutePoint


class ConnectTheDots(QRoute):

    """
    08/14/20: Used only for reproduction of non-meandered CPWs on BlueJay.
    Creates and connects a series of anchors through which the CPW passes.
    This class is basically pathfinder.py with no built-in collision
    avoidance and no A* algorithm.
    """

    default_options = Dict(
        trace_gap='cpw_gap',
        anchors=OrderedDict()  # Intermediate anchors only; doesn't include endpoints
        # Example: {1: np.array([x1, y1]), 2: np.array([x2, y2])}
        # startpin -> startpin + leadin -> anchors -> endpin + leadout -> endpin
    )

    component_metadata = Dict(
        short_name='cpw'
        )

    def getpts_simple(self, start_pt: QRoutePoint, end_pt: QRoutePoint, avoid_collision: bool = True) -> list:

        """
        Try connecting start and end with single or 2-segment/S-shaped CPWs if possible.
        
        Args:
            start_pt (QRoutePoint): QRoutePoint of the start
            end_pt (QRoutePoint): QRoutePoint of the end
            avoid_collision (bool): (default = True) set False to disable the search-path algorithm and save performance

        Returns:
            List of vertices of a CPW going from start to end
        """

        start_direction = start_pt.direction
        start = start_pt.position
        end_direction = end_pt.direction
        end = end_pt.position

        # end_direction originates strictly from endpoint + leadout (NOT intermediate stopping anchors)
        # stop_direction aligned with longer rectangle edge regardless of nature of 2nd anchor

        # Absolute value of displacement between start and end in x direction
        offsetx = abs(end[0] - start[0])
        # Absolute value of displacement between start and end in y direction
        offsety = abs(end[1] - start[1])
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
            # If the endpoints don't share a common x or y value:
            # designate them as 2 corners of an axis aligned rectangle
            # and check if both start and end directions are aligned with
            # the displacement vectors between start/end and
            # either of the 2 remaining corners ("perfect alignment").
            corner1 = np.array([start[0], end[1]]) # x coordinate matches with start
            corner2 = np.array([end[0], start[1]]) # x coordinate matches with end
            if avoid_collision:
                # Check for collisions at the outset to avoid repeat work
                startc1end = bool(self.no_obstacles([start, corner1]) and self.no_obstacles([corner1, end]))
                startc2end = bool(self.no_obstacles([start, corner2]) and self.no_obstacles([corner2, end]))
            else:
                startc1end = startc2end = True
            if (np.dot(start_direction, corner1 - start) > 0) and startc1end:
                if (end_direction is None) or (np.dot(end_direction, corner1 - end) > 0):
                    return [start, corner1, end]
            elif (np.dot(start_direction, corner2 - start) > 0) and startc2end:
                if (end_direction is None) or (np.dot(end_direction, corner2 - end) > 0):
                    return [start, corner2, end]
            # In notation below, corners 3 and 4 correspond to
            # the ends of the segment bisecting the longer rectangle formed by start and end
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
            if avoid_collision:
                startc3c4end = bool(self.no_obstacles([start, corner3]) and self.no_obstacles([corner3, corner4]) and self.no_obstacles([corner4, end]))
                startc5c6end = bool(self.no_obstacles([start, corner5]) and self.no_obstacles([corner5, corner6]) and self.no_obstacles([corner6, end]))
            else:
                startc3c4end = startc5c6end = True
            if (np.dot(start_direction, stop_direction) < 0) and (np.dot(start_direction, corner3 - start) > 0) and startc3c4end:
                if (end_direction is None) or (np.dot(end_direction, corner4 - end) > 0):
                    # Perfectly aligned S-shaped CPW
                    return [start, corner3, corner4, end]
            # Relax constraints and check if imperfect 2-segment or S-segment works,
            # where "imperfect" means 1 or more dot products of directions
            # between successive segments is 0; otherwise return an empty list
            if (np.dot(start_direction, corner1 - start) >= 0) and startc1end:
                if (end_direction is None) or (np.dot(end_direction, corner1 - end) >= 0):
                    return [start, corner1, end]
            if (np.dot(start_direction, corner2 - start) >= 0) and startc2end:
                if (end_direction is None) or (np.dot(end_direction, corner2 - end) >= 0):
                    return [start, corner2, end]
            if (np.dot(start_direction, corner3 - start) >= 0) and startc3c4end:
                if (end_direction is None) or (np.dot(end_direction, corner4 - end) >= 0):
                    return [start, corner3, corner4, end]
            if (np.dot(start_direction, corner5 - start) >= 0) and startc5c6end:
                if (end_direction is None) or (np.dot(end_direction, corner6 - end) >= 0):
                    return [start, corner5, corner6, end]
        return []

    def make(self):
        """
        Generates path from start pin to end pin.
        """
        p = self.parse_options()
        anchors = p.anchors

        # Set the CPW pins and add the points/directions to the lead-in/out arrays
        self.set_pin("start")
        self.set_pin("end")

        # Align the lead-in/out to the input options set from the user
        meander_start_point = self.set_lead("start")
        meander_end_point = self.set_lead("end")

        # TODO: find out why the make runs twice for every component and stop it.
        #  Should only run once. The line below is just a patch to work around it.
        self.intermediate_pts = None

        for coord in list(anchors.values()):
            if not self.intermediate_pts:
                self.intermediate_pts = self.getpts_simple(meander_start_point, QRoutePoint(coord)
                                                           , avoid_collision=False)[1:]
            else:
                self.intermediate_pts += self.getpts_simple(self.get_tip(), QRoutePoint(coord)
                                                            , avoid_collision=False)[1:]

        last_pt = self.getpts_simple(self.get_tip(), meander_end_point, avoid_collision=False)[1:]
        if self.intermediate_pts:
            self.intermediate_pts += last_pt
        else:
            self.intermediate_pts = last_pt

        # Make points into elements
        self.make_elements(self.get_points())

