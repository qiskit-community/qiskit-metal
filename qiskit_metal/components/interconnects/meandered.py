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
@author: Marco Facchini, John Blair, Zlatko Minev
'''

from typing import List, Tuple, Union

from numpy.linalg import norm

import numpy as np
from qiskit_metal import Dict
from qiskit_metal.toolbox_metal.parsing import is_true
from qiskit_metal.components.base import QRoute, QRoutePoint


class RouteMeander(QRoute):
    """
    The base `CPW meandered` class

    Inherits `QRoute` class

    Description:
        Implements a simple CPW, with a single meander

    Options:

    Meander:
        * spacing         - minimum spacing between adjacent meander curves (default: 200um)
        * asymmetry       - offset between the center-line of the meander and the center-line
          that stretches from the tip of lead-in to the x (or y) coordinate
          of the tip of the lead-out (default: '0um')

    Leads:
        * start_jogged_extension   - (optional) lead-in, jogged extension of lead-in. Described as list of tuples
        * end_jogged_extension     - (optional) lead-in, jogged extension of lead-out. Described as list of tuples

    """

    component_metadata = Dict(
        short_name='cpw'
        )
    """Component metadata"""

    default_options = Dict(
        meander=Dict(
            spacing='200um',
            asymmetry='0um'
        ),
        snap='true',
    )
    """Default options"""

    def make(self):
        """
        The make function implements the logic that creates the geometry
        (poly, path, etc.) from the qcomponent.options dictionary of parameters,
        and the adds them to the design, using qcomponent.add_qgeometry(...),
        adding in extra needed information, such as layer, subtract, etc.
        """
        # parsed options
        snap = is_true(self.p.snap)

        # Set the CPW pins and add the points/directions to the lead-in/out arrays
        self.set_pin("start")
        self.set_pin("end")

        # Align the lead-in/out to the input options set from the user
        meander_start_point = self.set_lead("start")
        meander_end_point = self.set_lead("end")

        if snap:
            # TODO: adjust the terminations to be sure the meander connects well on both ends
            # start_points.align_to(end_points)
            pass

        arc_pts = self.connect_meandered(meander_start_point, meander_end_point)

        self.intermediate_pts = arc_pts

        # Make points into elements
        self.make_elements(self.get_points())

    def connect_meandered(self, start_pt: QRoutePoint, end_pt: QRoutePoint) -> np.ndarray:
        """
        Meanders using a fixed length and fixed spacing.

        Args:
            start_pt (QRoutePoint): QRoutePoint of the start
            end_pt (QRoutePoint): QRoutePoint of the end

        Returns:
            np.ndarray: Array of points

        Adjusts the width of the meander:
            * Includes the start but not the given end point
            * If it cannot meander just returns the initial start point
        """

        ################################################################
        # Setup

        # Parameters
        meander_opt = self.p.meander
        spacing = meander_opt.spacing  # Horizontal spacing between meanders
        asymmetry = meander_opt.asymmetry
        snap = is_true(self.p.snap)  # snap to xy grid
        # TODO: snap add 45 deg snap by changing snap function using angles

        # take care of anchors (do not have set directions)
        anchor_lead = 0
        if end_pt.direction is None:
            # end_direction originates strictly from endpoint + leadout (NOT intermediate stopping anchors)
            self.assign_direction_to_anchor(start_pt, end_pt)
            anchor_lead = spacing
        # TODO: need to add the lead to the code below somewhere
        # TODO: how do I determine the length of the meander if I do not know yet the length of all other segments
        #  and what if there is more than one meander segment?
        # TODO: the entire code below relies on component input leads objects and length, how to generalize?

        # Meander length
        length_meander = self.p.total_length - (self.head.length + self.tail.length)
        if self.p.snap:
            # handle y distance
            length_meander -= 0  # (end.position - endm.position)[1]

        # Coordinate system (example: x to the right => sideways up)
        forward, sideways = self.get_unit_vectors(start_pt, end_pt, snap)
        # TODO: consider whether to support lead direction inverted, rather than just inverting options value
        # if is_true(meander_opt.lead_direction_inverted):
        #     sideways *= -1

        # Calculate lengths and meander number
        dist = end_pt.position - start_pt.position
        if snap:
            length_direct = abs(norm(np.dot(dist, forward)))  # in the vertical direction
            length_sideways = abs(norm(np.dot(dist, sideways)))  # in the orthogonal direction
        else:
            length_direct = norm(dist)
            length_sideways = 0

        # Breakup into sections
        meander_number = np.floor(length_direct / spacing)
        if meander_number < 1:
            self.logger.info(f'Zero meanders for {self.name}')
            return np.empty((0, 2), float)

        # The start and end points can have 4 directions each. Depending on the direction
        # there might be not enough space for all the meanders, thus here we adjust
        # meander_number w.r.t. what the start and end points "directionality" allows
        if round(np.dot(start_pt.direction, sideways) * np.dot(end_pt.direction, sideways)) > 0 and (meander_number % 2) == 0:
            # even meander_number is no good if roots have same orientation (w.r.t sideway)
            meander_number -= 1
        elif round(np.dot(start_pt.direction, sideways) * np.dot(end_pt.direction, sideways)) < 0 and (
                meander_number % 2) == 1:
            # odd meander_number is no good if roots have opposite orientation (w.r.t sideway)
            meander_number -= 1

        # should the first meander go sideways or counter sideways?
        start_meander_direction = round(np.dot(start_pt.direction, sideways), 10)
        end_meander_direction = round(np.dot(end_pt.direction, sideways), 10)
        if start_meander_direction > 0:  # sideway direction
            first_meander_sideways = True
            # print("1-> ", ((meander_number % 2) == 0))
        elif start_meander_direction < 0:  # opposite to sideway direction
            first_meander_sideways = False
            # print("2-> ", ((meander_number % 2) == 0))
        else:
            if end_meander_direction > 0:  # sideway direction
                first_meander_sideways = ((meander_number % 2) == 1)
                # print("3-> ", ((meander_number % 2) == 0))
            elif end_meander_direction < 0:  # opposite to sideway direction
                first_meander_sideways = ((meander_number % 2) == 0)
                # print("4-> ", ((meander_number % 2) == 0))
            else:
                # either direction is fine, so let's just pick one
                first_meander_sideways = True
                # print("5-> ", ((meander_number % 2) == 0))

        # TODO: this does not seem right. asymmetry has no role unless all meander top/bot points
        #  surpass the line (aligned with 'forward') of either the left or right root points.
        # length to distribute on the meanders (excess w.r.t a straight line between start and end)
        length_excess = (length_meander - length_direct - 2 * abs(asymmetry))
        # how much meander offset from center-line is needed to accommodate the length_excess (perpendicular length)
        length_perp = max(0, length_excess / (meander_number * 2.))

        # USES ROW Vectors
        # const vec. of unit normals
        middle_points = [forward] * int(meander_number + 1)
        # index so to multiply other column - creates a column vector
        scale_bys = spacing * np.arange(int(meander_number + 1))[:, None]
        # multiply each one in a linear chain fashion fwd
        middle_points = scale_bys * middle_points
        '''
        middle_points = array([
            [0. , 0. ],
            [0.2, 0. ],
            [0.4, 0. ],
            [0.6, 0. ],
            [0.8, 0. ],
            [1. , 0. ]])
        '''

        ################################################################
        # Calculation
        # including start and end points - there is no overlap in points
        # root_pts = np.concatenate([middle_points,
        #                            end.position[None, :]],  # convert to row vectors
        #                           axis=0)
        side_shift_vecs = np.array([sideways * length_perp] * len(middle_points))
        asymmetry_vecs = np.array([sideways * asymmetry] * len(middle_points))
        root_pts = middle_points + asymmetry_vecs
        top_pts = root_pts + side_shift_vecs
        bot_pts = root_pts - side_shift_vecs
        # TODO: add here length_sideways to root_pts[-1, :]?

        # print("MDL->", root_pts, "\nTOP->", top_pts, "\nBOT->", bot_pts)
        ################################################################
        # Combine points
        # Meanest part of the meander

        # Add 2 for the lead and end points in the cpw from
        # pts will have to store properly alternated top_pts and bot_pts
        # it will also store right-most root_pts (end)
        # 2 points from top_pts and bot_pts will be dropped for a complete meander
        pts = np.zeros((len(top_pts) + len(bot_pts) + 1 - 2, 2))
        # need to add the last root_pts in, because there could be a left-over non-meandered segment
        pts[-1, :] = root_pts[-1, :]
        idx_side1_meander, odd = self.get_index_for_side1_meander(len(root_pts))
        idx_side2_meander = 2 + idx_side1_meander[:None if odd else -2]
        if first_meander_sideways:
            pts[idx_side1_meander, :] = top_pts[:-1 if odd else None]
            pts[idx_side2_meander, :] = bot_pts[1:None if odd else -1]
        else:
            pts[idx_side1_meander, :] = bot_pts[:-1 if odd else None]
            pts[idx_side2_meander, :] = top_pts[1:None if odd else -1]

        # print("PTS->", pts)

        pts += start_pt.position  # move to start position

        # TODO: the below, changes the CPW total length. Need to account for this earlier
        if snap:
            # the right-most root_pts need to be aligned with the end.position point
            pts[-1, abs(forward[0])] = end_pt.position[abs(forward[0])]
        if abs(asymmetry) > abs(length_perp):
            if start_meander_direction * asymmetry < 0:  # sideway direction
                pts[0, abs(forward[0])] = start_pt.position[abs(forward[0])]
                pts[1, abs(forward[0])] = start_pt.position[abs(forward[0])]
            if end_meander_direction * asymmetry < 0:  # sideway direction
                pts[-2, abs(forward[0])] = end_pt.position[abs(forward[0])]
                pts[-3, abs(forward[0])] = end_pt.position[abs(forward[0])]

        # print("PTS_intermediate->", pts)

        return pts

    @staticmethod
    def get_index_for_side1_meander(num_root_pts: int):
        """
        Get the indices

        Args:
            root_pts (list): List of points

        Returns:
            tuple: Tuple of indices
        """
        num_2pts, odd = divmod(num_root_pts, 2)

        x = np.array(range(num_2pts), dtype=int) * 4
        z = np.zeros(num_2pts * 2, dtype=int)
        z[::2] = x
        z[1::2] = x + 1
        return z, odd
