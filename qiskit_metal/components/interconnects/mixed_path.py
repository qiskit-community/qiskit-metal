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
@date: Sept-2020
@author: Marco Facchini
'''

from typing import List, Tuple, Union

from numpy.linalg import norm

import numpy as np
from qiskit_metal import Dict
from qiskit_metal.components.base import QRoutePoint

from collections.abc import Mapping

from collections import OrderedDict
from .framed_path import RouteFramed
from .meandered import RouteMeander
from .pathfinder import RoutePathfinder


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
        between_anchors=OrderedDict(),  # Intermediate anchors only; doesn't include endpoints
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

        # Set the CPW pins and add the points/directions to the lead-in/out arrays
        self.set_pin("start")
        self.set_pin("end")

        # Align the lead-in/out to the input options set from the user
        meander_start_point = self.set_lead("start")
        meander_end_point = self.set_lead("end")

        # find the points to connect between each pair of anchors, or between anchors and leads
        # at first, store points "per segment" in a dictionary, so it is easier to apply length requirements
        self.intermediate_pts = OrderedDict()
        for arc_num, coord in anchors.items():
            # determine what is the connection strategy for this pair, based on user inputs
            connect_method = self.select_connect_method(arc_num)
            # compute points connecting the anchors, all but the last
            arc_pts = connect_method(self.get_tip(), QRoutePoint(coord))
            if arc_pts is None:
                # something went wrong and the connect algorythm was unable to connect the dots
                # TODO: determine best way to handle this. Currently just draws a straight line
                self.intermediate_pts[arc_num] = [coord]
            else:
                self.intermediate_pts[arc_num] = np.concatenate([arc_pts, [coord]], axis=0)
        # compute last connection point to the output QRouteLead
        connect_method = self.select_connect_method(len(anchors))
        arc_pts = connect_method(self.get_tip(), meander_end_point)
        if arc_pts is not None:
            self.intermediate_pts[len(anchors)] = np.array(arc_pts)

        # TODO: self.adjust_length(intermediate_dict)

        # concatenate all points, transforming the dictionary into a single numpy array
        self.trim_pts()
        self.intermediate_pts = np.concatenate(list(self.intermediate_pts.values()), axis=0)
        # Make points into elements
        self.make_elements(self.get_points())

    def select_connect_method(self, segment_num):
        between_anchors = self.parse_options().between_anchors
        if segment_num in between_anchors:
            type_connect = between_anchors[segment_num]
        else:
            type_connect = "S"
        print(type_connect)
        if type_connect == "S":
            return self.connect_simple
        if type_connect == "PF":
            return self.connect_astar_or_simple
        if type_connect == "M":
            return self.connect_meandered

    def trim_pts(self):
        if isinstance(self.intermediate_pts, Mapping):
            keys_to_delete = set()
            for key, value in self.intermediate_pts.items():
                if value is None:
                    keys_to_delete.add(key)
                try:
                    # value is a list
                    if not value:
                        keys_to_delete.add(key)
                except ValueError:
                    # value is a numpy
                    if not value.size:
                        keys_to_delete.add(key)
            for key in keys_to_delete:
                del self.intermediate_pts[key]
