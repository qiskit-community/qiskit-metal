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
@date: Aug-2020
@author: Dennis Wang, Marco Facchini
'''

import heapq
import numpy as np
from qiskit_metal import Dict
from qiskit_metal.components.base import QRoutePoint
from .anchored_path import RouteAnchors

# TODO: Stopping condition for A* in case it doesn't converge (time limit or user-provided exploration area?)


class RoutePathfinder(RouteAnchors):
    """
    Non-meandered CPW class that combines A* pathfinding algorithm with
    simple 1-, 2-, or S-shaped segment checks and user-specified anchor points.
    1. A* heap modified to prioritize paths with shortest length_travelled + Manhattan distance to destination.
    2. Checks if connect_simple is valid each time we pop from the heap. If so, use it, otherwise proceed with A*.
    3. Tweaks connect_simple to account for end anchor direction in determining which CPW (elbow or S-segment) to use.

    Options:
        * step_size - length of the step for the A* pathfinding algorithm

    Advanced Options:
        * avoid_collision - true/false, defines if the route needs to avoid collisions (default: 'true')

    """

    default_options = Dict(
        step_size='0.25mm',
        advanced=Dict(
            avoid_collision='true')
    )
    """Default options"""

    def connect_astar_or_simple(self, start_pt: QRoutePoint, end_pt: QRoutePoint, step_size: float = 0.25) -> list:
        """
        Connect start and end via A* algo if connect_simple doesn't work
        
        Args:
            start_direction (np.array): Vector indicating direction of starting point
            start (np.array): 2-D coordinates of first anchor
            end (np.array): 2-D coordinates of second anchor
            step_size (float): Minimum distance between adjacent vertices on CPW

        Returns:
            List of vertices of a CPW going from start to end
        """

        start_direction = start_pt.direction
        start = start_pt.position
        end_direction = end_pt.direction
        end = end_pt.position

        starting_dist = sum(abs(end - start)) # Manhattan distance between start and end
        pathmapper = {(starting_dist, start[0], start[1]): [starting_dist, [start]]}
        # pathmapper maps tuple(total length of the path from self.start + Manhattan distance to destination, coordx, coordy) to [total length of 
        # path from self.start, path]
        visited = set([(start[0], start[1])]) # maintain record of points we've already visited to avoid self-intersections
        h = [(starting_dist, start[0], start[1])] # priority queue (heap in Python implementation)
        # Elements in the heap are ordered by the following:
        # 1. The total length of the path from self.start + Manhattan distance to destination
        # 2. The x coordinate of the latest point
        # 3. The y coordinate of the latest point

        while h:
            tot_dist, x, y = heapq.heappop(h) # tot_dist is the total length of the path from self.start + Manhattan distance to destination
            length_travelled, current_path = pathmapper[(tot_dist, x, y)]
            # Look in forward, left, and right directions a fixed distance away.
            # If the line segment connecting the current point and this next one does
            # not collide with any bounding boxes in design.components, add it to the
            # list of neighbors.
            neighbors = []
            if len(current_path) == 1:
                # At starting point -> initial direction is start direction
                direction = start_direction
            else:
                # Beyond starting point -> look at vector difference of last 2 points along path
                direction = current_path[-1] - current_path[-2]
            # The dot product between direction and the vector connecting the current
            # point and a potential neighbor must be non-negative to avoid retracing.
            
            # Check if connect_simple works at each iteration of A*
            simple_path = self.connect_simple(QRoutePoint(np.array([x, y]), direction), QRoutePoint(end, end_direction))
            if simple_path:
                if len(current_path) > 1:
                    # Concatenate collinear line segments (joined at a point and have identical slopes)
                    # current_path = [..., [x_pen, y_pen], [x_end, y_end]]
                    # simple_path = [[x_end, y_end], [x_new, y_new], ...]
                    x_pen, y_pen = current_path[-2]
                    x_ult, y_ult = current_path[-1]
                    x_new, y_new = simple_path[1]
                    if (y_ult - y_pen) * (x_new - x_ult) == (y_new - y_ult) * (x_ult - x_pen):
                        # Concatenate collinear line segments (joined at a point and have identical slopes)
                        return current_path[:-1] + simple_path[1:]
                return current_path[:-1] + simple_path
            
            for disp in [np.array([0, 1]), np.array([0, -1]), np.array([1, 0]), np.array([-1, 0])]:
                # Unit displacement in 4 cardinal directions
                if np.dot(disp, direction) >= 0:
                    # Ignore backward direction
                    curpt = current_path[-1]
                    nextpt = curpt + step_size * disp
                    if self.unobstructed([curpt, nextpt]):
                        neighbors.append(nextpt)
            for neighbor in neighbors:
                if tuple(neighbor) not in visited:
                    new_remaining_dist = sum(abs(end - neighbor))
                    new_length_travelled = length_travelled + step_size
                    if len(current_path) > 1:
                        x_ult, y_ult = current_path[-1] # last point on origin's path
                        x_pen, y_pen = current_path[-2] # penultimate point on origin's path
                        x_cur, y_cur = neighbor
                        if (y_ult - y_pen) * (x_cur - x_ult) == (y_cur - y_ult) * (x_ult - x_pen):
                            # Concatenate collinear line segments (joined at a point and have identical slopes)
                            new_path = current_path[:-1] + [neighbor]
                        else:
                            new_path = current_path + [neighbor]
                    else:
                        new_path = current_path + [neighbor]
                    if new_remaining_dist < 10 ** -8:
                        # Destination has been reached within acceptable error tolerance (errors due to rounding in Python)
                        return new_path[:-1] + [end] # Replace last element of new_path with end since they're basically the same
                    heapq.heappush(h, (new_length_travelled + new_remaining_dist, neighbor[0], neighbor[1]))
                    pathmapper[(new_length_travelled + new_remaining_dist, neighbor[0], neighbor[1])] = [new_length_travelled, new_path]
                    visited.add(tuple(neighbor))
        return []  # Shouldn't actually reach here - if it fails, there's a convergence issue
    
    def make(self):
        """
        Generates path from start pin to end pin.
        """
        p = self.parse_options()
        anchors = p.anchors
        step_size = p.step_size

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
                self.intermediate_pts = self.connect_astar_or_simple(meander_start_point, QRoutePoint(coord), step_size)[1:]
            else:
                self.intermediate_pts += self.connect_astar_or_simple(self.get_tip(), QRoutePoint(coord), step_size)[1:]

        last_pt = self.connect_astar_or_simple(self.get_tip(), meander_end_point, step_size)[1:]
        if self.intermediate_pts:
            self.intermediate_pts += last_pt
        else:
            self.intermediate_pts = last_pt

        # Make points into elements
        self.make_elements(self.get_points())
