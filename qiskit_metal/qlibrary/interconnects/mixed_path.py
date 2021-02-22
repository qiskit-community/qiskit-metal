# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
'''
@date: Sept-2020
@author: Marco Facchini
'''

import numpy as np
from qiskit_metal import Dict
from qiskit_metal.qlibrary.base import QRoutePoint

from collections import OrderedDict
from .meandered import RouteMeander
from .pathfinder import RoutePathfinder


# class RouteMixed(RouteFramed, RoutePathfinder, RouteMeander):
class RouteMixed(RoutePathfinder, RouteMeander):
    """
    The comprehensive Routing class
    Inherits `RoutePathfinder, RouteMeander` class, thus also QRoute and RouteAnchors

    Description:
        Implements fully featured Routing, allowing different type of connections between anchors

    Options:

    Meander:
        * spacing         - minimum spacing between adjacent meander curves (default: 200um)
        * asymmetry       - offset between the center-line of the meander and the center-line
          that stretches from the tip of lead-in to the x (or y) coordinate
          of the tip of the lead-out (default: '0um')

    """

    default_options = Dict(
        between_anchors=OrderedDict(
        ),  # Intermediate anchors only; doesn't include endpoints
        # Example: {1: "M", 2: "S", 3: "PF"}
        # startpin -> startpin + leadin -> anchors -> endpin + leadout -> endpin
    )
    """Default options"""

    def make(self):
        """
        Generates path from start pin to end pin.
        """
        p = self.parse_options()
        anchors = p.anchors
        between_anchors = p.between_anchors

        # Set the CPW pins and add the points/directions to the lead-in/out arrays
        self.set_pin("start")
        self.set_pin("end")

        # Align the lead-in/out to the input options set from the user
        start_point = self.set_lead("start")
        end_point = self.set_lead("end")

        # approximate length needed for individual meanders
        # the meander algorithm directly reads from self._length_segment
        count_meanders_list = [
            1 if x == "M" else 0 for x in list(between_anchors.values())
        ]
        self._length_segment = None
        if any(count_meanders_list):
            self._length_segment = ((self.p.total_length - (self.head.length + self.tail.length) \
                                   - self.free_manhattan_length_anchors()) / sum(count_meanders_list)) \
                                   + (self.free_manhattan_length_anchors() / len(count_meanders_list))

        # find the points to connect between each pair of anchors, or between anchors and leads
        # at first, store points "per segment" in a dictionary, so it is easier to apply length requirements
        self.intermediate_pts = OrderedDict()
        meanders = set()
        for arc_num, coord in anchors.items():
            # determine what is the connection strategy for this pair, based on user inputs
            connect_method = self.select_connect_method(arc_num)
            if connect_method == self.connect_meandered:
                meanders.add(arc_num)
            # compute points connecting the anchors, all but the last
            arc_pts = connect_method(self.get_tip(), QRoutePoint(coord))
            if arc_pts is None:
                self.intermediate_pts[arc_num] = [coord]
            else:
                self.intermediate_pts[arc_num] = np.concatenate(
                    [arc_pts, [coord]], axis=0)
        # compute last connection point to the output QRouteLead
        connect_method = self.select_connect_method(len(anchors))
        if connect_method == self.connect_meandered:
            meanders.add(len(anchors))
        arc_pts = connect_method(self.get_tip(), end_point)
        if arc_pts is not None:
            self.intermediate_pts[len(anchors)] = np.array(arc_pts)

        # concatenate all points, transforming the dictionary into a single numpy array
        self.trim_pts()
        dictionary_intermediate_pts = self.intermediate_pts
        self.intermediate_pts = np.concatenate(list(
            self.intermediate_pts.values()),
                                               axis=0)

        if any(count_meanders_list):
            # refine length of meanders
            total_delta_length = self.p.total_length - self.length
            individual_delta_length = total_delta_length / len(meanders)
            for m in meanders:
                arc_pts = dictionary_intermediate_pts[m][:-1]
                if m == 0:
                    meander_start_point = start_point
                else:
                    meander_start_point = QRoutePoint(anchors[m - 1])
                if m == len(anchors):
                    meander_end_point = end_point
                else:
                    meander_end_point = QRoutePoint(anchors[m])
                dictionary_intermediate_pts[m] = self.adjust_length(
                    individual_delta_length, arc_pts, meander_start_point,
                    meander_end_point)
                dictionary_intermediate_pts[m] = np.concatenate(
                    [dictionary_intermediate_pts[m], [anchors[m]]], axis=0)
        self.intermediate_pts = np.concatenate(list(
            dictionary_intermediate_pts.values()),
                                               axis=0)

        # Make points into elements
        self.make_elements(self.get_points())

    def select_connect_method(self, segment_num):
        """Translates the user-selected connection method into the right method to execute

        Args:
            segment_num (int): segment ID. Counts 0 as the first segment after the lead-in.

        Return:
            selected method
        """
        between_anchors = self.parse_options().between_anchors
        if segment_num in between_anchors:
            type_connect = between_anchors[segment_num]
        else:
            type_connect = "S"
        # print(type_connect)
        if type_connect == "S":
            return self.connect_simple
        if type_connect == "PF":
            return self.connect_astar_or_simple
        if type_connect == "M":
            return self.connect_meandered
