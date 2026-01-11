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

import heapq
import numpy as np
from qiskit_metal import Dict
from qiskit_metal.qlibrary.core import QRoutePoint
from qiskit_metal.qlibrary.tlines.anchored_path import RouteAnchors
from qiskit_metal.toolbox_metal import math_and_overrides as mao
from collections import OrderedDict
from qiskit_metal.toolbox_metal.exceptions import QiskitMetalDesignError


class RoutePathfinder(RouteAnchors):
    """
    Non-meandered CPW class that combines A* pathfinding algorithm with
    simple 1-, 2-, or S-shaped segment checks and user-specified anchor points.
    1. A* heap modified to prioritize paths with shortest length_travelled + Manhattan distance to destination.
    2. Checks if connect_simple is valid each time we pop from the heap. If so, use it, otherwise proceed with A*.
    3. Tweaks connect_simple to account for end anchor direction in determining which CPW (elbow or S-segment) to use.

    .. meta::
        :description: Route Pathfinder

    RouteAnchors Default Options:
        * anchors: OrderedDict -- Intermediate anchors only; doesn't include endpoints
        * advanced: Dict
            * avoid_collision: 'false' -- true/false, defines if the route needs to avoid collisions

    Default Options:
        * step_size: '0.25mm' -- Length of the step for the A* pathfinding algorithm
        * advanced: Dict
            * avoid_collision: 'true' -- true/false, defines if the route needs to avoid collisions
    """

    default_options = Dict(step_size='0.25mm',
                           advanced=Dict(avoid_collision='true'))
    """Default options"""

    TOOLTIP = """ Non-meandered CPW class that combines A* pathfinding algorithm with
    simple 1-, 2-, or S-shaped segment checks and user-specified anchor points."""

    def connect_astar_or_simple(self, start_pt: QRoutePoint,
                                end_pt: QRoutePoint) -> list:
        """Connect start and end via A* algo if connect_simple doesn't work.

        Args:
            start_direction (np.array): Vector indicating direction of starting point
            start (np.array): 2-D coordinates of first anchor
            end (np.array): 2-D coordinates of second anchor

        Returns:
            List of vertices of a CPW going from start to end

        Raises:
            QiskitMetalDesignError: If the connect_simple() has failed.
        """

        start_direction = start_pt.direction
        start = start_pt.position
        end_direction = end_pt.direction
        end = end_pt.position

        step_size = self.parse_options().step_size

        starting_dist = sum(
            abs(end - start))  # Manhattan distance between start and end
        key_starting_point = (starting_dist, start[0], start[1])
        pathmapper = {key_starting_point: [starting_dist, [start]]}
        # pathmapper maps tuple(total length of the path from self.start + Manhattan distance to destination, coordx, coordy) to [total length of
        # path from self.start, path]
        visited = set(
        )  # maintain record of points we've already visited to avoid self-intersections
        visited.add(tuple(start))
        # TODO: add to visited all of the current points in the route, to prevent self intersecting
        priority_queue = list()  # A* priority queue. Implemented as heap
        priority_queue.append(key_starting_point)
        # Elements in the heap are ordered by the following:
        # 1. The total length of the path from self.start + Manhattan distance to destination
        # 2. The x coordinate of the latest point
        # 3. The y coordinate of the latest point

        while priority_queue:
            tot_dist, x, y = heapq.heappop(
                priority_queue
            )  # tot_dist is the total length of the path from self.start + Manhattan distance to destination
            length_travelled, current_path = pathmapper[(tot_dist, x, y)]
            # Look in forward, left, and right directions a fixed distance away.
            # If the line segment connecting the current point and this next one does
            # not collide with any bounding boxes in design.components, add it to the
            # list of neighbors.
            neighbors = list()
            if len(current_path) == 1:
                # At starting point -> initial direction is start direction
                direction = start_direction
            else:
                # Beyond starting point -> look at vector difference of last 2 points along path
                direction = current_path[-1] - current_path[-2]
            # The dot product between direction and the vector connecting the current
            # point and a potential neighbor must be non-negative to avoid retracing.

            # Check if connect_simple works at each iteration of A*
            try:
                simple_path = self.connect_simple(
                    QRoutePoint(np.array([x, y]), direction),
                    QRoutePoint(end, end_direction))
            except QiskitMetalDesignError:
                simple_path = None
                # try the pathfinder algorithm
                pass

            if simple_path is not None:
                current_path.extend(simple_path)
                return current_path

            for disp in [
                    np.array([0, 1]),
                    np.array([0, -1]),
                    np.array([1, 0]),
                    np.array([-1, 0])
            ]:
                # Unit displacement in 4 cardinal directions
                if mao.dot(disp, direction) >= 0:
                    # Ignore backward direction
                    curpt = current_path[-1]
                    nextpt = curpt + step_size * disp
                    if self.unobstructed([curpt, nextpt]):
                        neighbors.append(nextpt)
            for neighbor in neighbors:
                if tuple(neighbor) not in visited:
                    new_remaining_dist = sum(abs(end - neighbor))
                    new_length_travelled = length_travelled + step_size
                    new_path = current_path + [neighbor]
                    if new_remaining_dist < 10**-8:
                        # Destination has been reached within acceptable error tolerance (errors due to rounding in Python)
                        return new_path[:-1] + [
                            end
                        ]  # Replace last element of new_path with end since they're basically the same
                    heapq.heappush(priority_queue,
                                   (new_length_travelled + new_remaining_dist,
                                    neighbor[0], neighbor[1]))
                    pathmapper[(new_length_travelled + new_remaining_dist,
                                neighbor[0], neighbor[1])] = [
                                    new_length_travelled, new_path
                                ]
                    visited.add(tuple(neighbor))
        return [
        ]  # Shouldn't actually reach here - if it fails, there's a convergence issue

    def make(self):
        """Generates path from start pin to end pin."""
        p = self.parse_options()
        anchors = p.anchors

        # Set the CPW pins and add the points/directions to the lead-in/out arrays
        self.set_pin("start")
        self.set_pin("end")

        # Align the lead-in/out to the input options set from the user
        start_point = self.set_lead("start")
        end_point = self.set_lead("end")

        self.intermediate_pts = OrderedDict()
        for arc_num, coord in anchors.items():
            arc_pts = self.connect_astar_or_simple(self.get_tip(),
                                                   QRoutePoint(coord))
            if arc_pts is None:
                self.intermediate_pts[arc_num] = [coord]
            else:
                self.intermediate_pts[arc_num] = np.concatenate(
                    [arc_pts, [coord]], axis=0)
        arc_pts = self.connect_astar_or_simple(self.get_tip(), end_point)
        if arc_pts is not None:
            self.intermediate_pts[len(anchors)] = np.array(arc_pts)

        # concatenate all points, transforming the dictionary into a single numpy array
        self.trim_pts()
        self.intermediate_pts = np.concatenate(list(
            self.intermediate_pts.values()),
                                               axis=0)

        # Make points into elements
        self.make_elements(self.get_points())
