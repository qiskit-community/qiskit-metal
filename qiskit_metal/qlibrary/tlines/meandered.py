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

from typing import List, Tuple, Union

from numpy.linalg import norm

import numpy as np
from qiskit_metal import Dict
from qiskit_metal.toolbox_metal.parsing import is_true
from qiskit_metal.qlibrary.core import QRoute, QRoutePoint
from qiskit_metal.toolbox_metal import math_and_overrides as mao
from qiskit_metal.toolbox_metal.exceptions import QiskitMetalDesignError


class RouteMeander(QRoute):
    """Implements a simple CPW, with a single meander.  The base `CPW
    meandered` class.

    Inherits `QRoute` class

    .. meta::
        Route Meander

    QRoute Default Options:
        * pin_inputs: Dict
            * start_pin: Dict -- Component and pin string pair. Define which pin to start from
                * component: '' -- Name of component to start from, which has a pin
                * pin: '' -- Name of pin used for pin_start
            * end_pin=Dict -- Component and pin string pair. Define which pin to start from
                * component: '' -- Name of component to end on, which has a pin
                * pin: '' -- Name of pin used for pin_end
        * fillet: '0'
        * lead: Dict
            * start_straight: '0mm' -- Lead-in, defined as the straight segment extension from start_pin.  Defaults to 0.1um.
            * end_straight: '0mm' -- Lead-out, defined as the straight segment extension from end_pin.  Defaults to 0.1um.
            * start_jogged_extension: '' -- Lead-in, jogged extension of lead-in. Described as list of tuples
            * end_jogged_extension: '' -- Lead-out, jogged extension of lead-out. Described as list of tuples
        * total_length: '7mm'
        * trace_width: 'cpw_width' -- Defines the width of the line.  Defaults to 'cpw_width'.

    Default Options:
        * meander: Dict
            * spacing: '200um' -- Minimum spacing between adjacent meander curves.  Defaults to 200um.
            * asymmetry='0um' -- offset between the center-line of the meander and the center-line that stretches from the tip of lead-in to the x (or y) coordinate of the tip of the lead-out.  Defaults to '0um'.
        * snap: 'true'
        * prevent_short_edges: 'true'
    """

    component_metadata = Dict(short_name='cpw')
    """Component metadata"""

    default_options = Dict(meander=Dict(spacing='200um', asymmetry='0um'),
                           snap='true',
                           prevent_short_edges='true')
    """Default options"""

    TOOLTIP = """Implements a simple CPW, with a single meander."""

    def make(self):
        """The make function implements the logic that creates the geometry
        (poly, path, etc.) from the qcomponent.options dictionary of
        parameters, and the adds them to the design, using
        qcomponent.add_qgeometry(...), adding in extra needed information, such
        as layer, subtract, etc."""
        # parsed options
        snap = is_true(self.p.snap)

        # Set the CPW pins and add the points/directions to the lead-in/out arrays
        self.set_pin("start")
        self.set_pin("end")

        # Align the lead-in/out to the input options set from the user
        meander_start_point = self.set_lead("start")
        meander_end_point = self.set_lead("end")

        # approximate length needed for the meander
        self._length_segment = self.p.total_length - (self.head.length +
                                                      self.tail.length)

        arc_pts = self.connect_meandered(meander_start_point, meander_end_point)

        self.intermediate_pts = arc_pts

        self.intermediate_pts = self.adjust_length(
            self.p.total_length - self.length, arc_pts, meander_start_point,
            meander_end_point)

        # Make points into elements
        self.make_elements(self.get_points())

    def connect_meandered(self, start_pt: QRoutePoint,
                          end_pt: QRoutePoint) -> np.ndarray:
        """Meanders using a fixed length and fixed spacing.

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
        prevent_short_edges = is_true(self.p.prevent_short_edges)

        # take care of anchors (do not have set directions)
        anchor_lead = 0
        if end_pt.direction is None:
            # end_direction originates strictly from endpoint + leadout (NOT intermediate stopping anchors)
            self.assign_direction_to_anchor(start_pt, end_pt)
            anchor_lead = spacing

        # Meander length
        length_meander = self._length_segment
        if self.p.snap:
            # handle y distance
            length_meander -= 0  # (end.position - endm.position)[1]

        # Coordinate system (example: x to the right => sideways up)
        forward, sideways = self.get_unit_vectors(start_pt, end_pt, snap)

        # Calculate lengths and meander number
        dist = end_pt.position - start_pt.position
        if snap:
            length_direct = abs(norm(mao.dot(
                dist, forward)))  # in the vertical direction
            length_sideways = abs(norm(mao.dot(
                dist, sideways)))  # in the orthogonal direction
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
        if mao.round(
                mao.dot(start_pt.direction, sideways) *
                mao.dot(end_pt.direction, sideways)) > 0 and (meander_number %
                                                              2) == 0:
            # even meander_number is no good if roots have same orientation (w.r.t sideway)
            meander_number -= 1
        elif mao.round(
                mao.dot(start_pt.direction, sideways) *
                mao.dot(end_pt.direction, sideways)) < 0 and (meander_number %
                                                              2) == 1:
            # odd meander_number is no good if roots have opposite orientation (w.r.t sideway)
            meander_number -= 1

        # should the first meander go sideways or counter sideways?
        start_meander_direction = mao.dot(start_pt.direction, sideways)
        end_meander_direction = mao.dot(end_pt.direction, sideways)
        if start_meander_direction > 0:  # sideway direction
            first_meander_sideways = True
        elif start_meander_direction < 0:  # opposite to sideway direction
            first_meander_sideways = False
        else:
            if end_meander_direction > 0:  # sideway direction
                first_meander_sideways = ((meander_number % 2) == 1)
            elif end_meander_direction < 0:  # opposite to sideway direction
                first_meander_sideways = ((meander_number % 2) == 0)
            else:
                # either direction is fine, so let's just pick one
                first_meander_sideways = True

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
        side_shift_vecs = np.array([sideways * length_perp] *
                                   len(middle_points))
        asymmetry_vecs = np.array([sideways * asymmetry] * len(middle_points))
        root_pts = middle_points + asymmetry_vecs
        top_pts = root_pts + side_shift_vecs
        bot_pts = root_pts - side_shift_vecs

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

        pts += start_pt.position  # move to start position

        if snap:
            if ((mao.dot(start_pt.direction, end_pt.direction) < 0) and
                (mao.dot(forward, start_pt.direction) <= 0)):
                # pins are pointing opposite directions and diverging
                # the last root_pts need to be sideways aligned with the end.position point
                # and forward aligned with the previous meander point
                pts[-1, abs(forward[0])] = pts[-2, abs(forward[0])]
                pts[-1,
                    abs(forward[0]) - 1] = end_pt.position[abs(forward[0]) - 1]
            else:
                # the last root_pts need to be forward aligned with the end.position point
                pts[-1, abs(forward[0])] = end_pt.position[abs(forward[0])]
                # and if the last root_pts ends outside the CPW amplitude on the side where the last meander is
                # then the last meander needs to be locked on it as well
                if (self.issideways(pts[-1], pts[-3], pts[-2])
                        and self.issideways(pts[-2], root_pts[0]+start_pt.position, root_pts[-1]+start_pt.position))\
                        or (not self.issideways(pts[-1], pts[-3], pts[-2])
                            and not self.issideways(pts[-2], root_pts[0]+start_pt.position,
                                                    root_pts[-1]+start_pt.position)):
                    pts[-2, abs(forward[0])] = end_pt.position[abs(forward[0])]
                    pts[-3, abs(forward[0])] = end_pt.position[abs(forward[0])]
        if abs(asymmetry) > abs(length_perp):
            if not ((mao.dot(start_pt.direction, end_pt.direction) < 0) and
                    (mao.dot(forward, start_pt.direction) <= 0)):
                # pins are "not" pointing opposite directions and diverging
                if start_meander_direction * asymmetry < 0:  # sideway direction
                    pts[0, abs(forward[0])] = start_pt.position[abs(forward[0])]
                    pts[1, abs(forward[0])] = start_pt.position[abs(forward[0])]
                if end_meander_direction * asymmetry < 0:  # opposite sideway direction
                    pts[-2, abs(forward[0])] = end_pt.position[abs(forward[0])]
                    pts[-3, abs(forward[0])] = end_pt.position[abs(forward[0])]

        # Adjust the meander to eliminate the terminating jog (dogleg)
        if prevent_short_edges:
            x2fillet = 2 * self.p.fillet
            # adjust the tail first
            # the meander algorithm adds a final point in line with the tail, to cope with left-over
            # this extra point needs to be moved or not, depending on the tail tip direction
            if abs(mao.dot(end_pt.direction, sideways)) > 0:
                skippoint = 0
            else:
                skippoint = 1
            if 0 < abs(mao.round(end_pt.position[0] - pts[-1, 0])) < x2fillet:
                pts[-1 - skippoint,
                    0 - skippoint] = end_pt.position[0 - skippoint]
                pts[-2 - skippoint,
                    0 - skippoint] = end_pt.position[0 - skippoint]
            if 0 < abs(mao.round(end_pt.position[1] - pts[-1, 1])) < x2fillet:
                pts[-1 - skippoint,
                    1 - skippoint] = end_pt.position[1 - skippoint]
                pts[-2 - skippoint,
                    1 - skippoint] = end_pt.position[1 - skippoint]
            # repeat for the start. here we do not have the extra point
            if 0 < abs(mao.round(start_pt.position[0] - pts[0, 0])) < x2fillet:
                pts[0, 0] = start_pt.position[0]
                pts[1, 0] = start_pt.position[0]
            if 0 < abs(mao.round(start_pt.position[1] - pts[0, 1])) < x2fillet:
                pts[0, 1] = start_pt.position[1]
                pts[1, 1] = start_pt.position[1]

        return pts

    def adjust_length(self, delta_length, pts, start_pt: QRoutePoint,
                      end_pt: QRoutePoint) -> np.ndarray:
        """Edits meander points to redistribute the length slacks accrued with
        the various local adjustments It should be run after
        self.pts_intermediate is completely defined Inputs are however specific
        to the one meander segment Assumption is that pts is always a sequence
        of paired points, each corresponds to one meander 180deg curve The pts
        is typically an odd count since the last point is typically used to
        anchor the left-over length, therefore this code supports both odd and
        even cases, separately. For even it assumes all points are in paired.

        Args:
            delta_length (delta_length): slack/excess length to distribute on the pts
            pts (np.array): intermediate points of meander. pairs, except last point (2,2,...,2,1)
            start_pt (QRoutePoint): QRoutePoint of the start
            end_pt (QRoutePoint): QRoutePoint of the end

        Returns:
            np.ndarray: Array of points
        """
        # the adjustment length has to be computed in the main or in other method
        # considering entire route (Could include the corner fillet)

        if len(pts) <= 3:
            # not a meander
            return pts

        # is it an even or odd count of points?
        term_point = len(pts) % 2

        # recompute direction
        snap = is_true(self.p.snap)  # snap to xy grid
        forward, sideways = self.get_unit_vectors(start_pt, end_pt, snap)
        # recompute meander_sideways
        if mao.cross(pts[1] - pts[0], pts[2] - pts[1]) < 0:
            first_meander_sideways = True
        else:
            first_meander_sideways = False
        if mao.cross(pts[-2 - term_point] - pts[-1 - term_point],
                     pts[-3 - term_point] - pts[-2 - term_point]) < 0:
            last_meander_sideways = False
        else:
            last_meander_sideways = True

        # which points need to receive the shift?
        # 1. initialize the shift vector to 1 (1 = will receive shift)
        adjustment_vector = np.ones(len(pts))
        # 2. switch shift direction depending on sideways or not
        if first_meander_sideways:
            adjustment_vector[2::4] *= -1
            adjustment_vector[3::4] *= -1
        else:
            adjustment_vector[::4] *= -1
            adjustment_vector[1::4] *= -1

        # 3. suppress shift for points that can cause short edges
        # calculate thresholds for suppression of short edges (short edge = not long enough for set fillet)
        fillet_shift = sideways * self.p.fillet
        start_pt_adjusted_up = start_pt.position + fillet_shift
        start_pt_adjusted_down = start_pt.position - fillet_shift
        end_pt_adjusted_up = end_pt.position + fillet_shift
        end_pt_adjusted_down = end_pt.position - fillet_shift

        # if start_pt.position is below axes + shift - 2xfillet &  first_meander_sideways
        if first_meander_sideways and not self.issideways(
                start_pt_adjusted_up, pts[0], pts[1]):
            pass
        # if start_pt.position is above axes - shift + 2xfillet &  not first_meander_sideways
        elif not first_meander_sideways and self.issideways(
                start_pt_adjusted_down, pts[0], pts[1]):
            pass
        else:
            # else block first mender
            adjustment_vector[:2] = [0, 0]
        # if end_pt.position is below axes + shift - 2xfillet &  last_meander_sideways
        if last_meander_sideways and not self.issideways(
                end_pt_adjusted_up, pts[-2 - term_point], pts[-1 - term_point]):
            pass
        # if end_pt.position is above axes - shift + 2xfillet &  not last_meander_sideways
        elif not last_meander_sideways and self.issideways(
                end_pt_adjusted_down, pts[-2 - term_point],
                pts[-1 - term_point]):
            pass
        else:
            # else block last mender
            adjustment_vector[-2 - term_point:-term_point] = [0, 0]

        not_a_meander = 0
        if term_point:
            # means that pts count is a odd number
            # thus needs to disable shift on the termination point...
            adjustment_vector[-1] = 0
            # ...unless the last point is anchored to the last meander curve
            if start_pt.direction is not None and end_pt.direction is not None:
                if ((mao.dot(start_pt.direction, end_pt.direction) < 0) and
                    (mao.dot(forward, start_pt.direction) <= 0)):
                    # pins are pointing opposite directions and diverging, thus keep consistency
                    adjustment_vector[-1] = adjustment_vector[-2]
                    if adjustment_vector[-1]:
                        # the point in between needs to be shifted, but it will not contribute to length change
                        # therefore the total length distribution (next step) should ignore it.
                        not_a_meander = 1

        # Finally, divide the slack amongst all points...
        sideways_adjustment = sideways * (
            delta_length /
            (np.count_nonzero(adjustment_vector) - not_a_meander))
        pts = pts + sideways_adjustment[
            np.newaxis, :] * adjustment_vector[:, np.newaxis]

        return pts

    @staticmethod
    def get_index_for_side1_meander(num_root_pts: int):
        """Get the indices.

        Args:
            num_root_pts (list): List of points

        Returns:
            tuple: Tuple of indices
        """
        num_2pts, odd = divmod(num_root_pts, 2)

        x = np.array(range(num_2pts), dtype=int) * 4
        z = np.zeros(num_2pts * 2, dtype=int)
        z[::2] = x
        z[1::2] = x + 1
        return z, odd

    def issideways(self, point, seg_point_a, seg_point_b):
        return mao.cross(point - seg_point_a, seg_point_b - seg_point_a) < 0
