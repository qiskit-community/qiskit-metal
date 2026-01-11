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
"""Anchored path."""

import numpy as np

from collections import OrderedDict
from qiskit_metal import Dict
from qiskit_metal.qlibrary.core import QRoute, QRoutePoint
from qiskit_metal.toolbox_metal import math_and_overrides as mao
from qiskit_metal.toolbox_metal.exceptions import QiskitMetalDesignError
from collections.abc import Mapping
from shapely.ops import unary_union
from shapely.geometry import CAP_STYLE
import geopandas as gpd


def intersecting(a: np.array, b: np.array, c: np.array, d: np.array) -> bool:
    """Returns whether segment ab intersects or overlaps with segment cd, where
    a, b, c, and d are all coordinates.

    .. meta::
        :description: Anchored Path

    Args:
        a (np.array): Coordinate
        b (np.array): Coordinate
        c (np.array): Coordinate
        d (np.array): Coordinate

    Returns:
        bool: True if intersecting, False otherwise
    """

    x0_start, y0_start = a
    x0_end, y0_end = b
    x1_start, y1_start = c
    x1_end, y1_end = d
    if (x0_start == x0_end) and (x1_start == x1_end):
        # 2 vertical lines intersect only if they completely overlap at some point(s)
        if x0_end == x1_start:
            # Same x-intercept -> potential overlap, so check y coordinate
            # Distinct, non-overlapping segments if and only if min y coord of one is above max y coord of the other
            return not ((min(y0_start, y0_end) > max(y1_start, y1_end)) or
                        (min(y1_start, y1_end) > max(y0_start, y0_end)))
        return False  # Parallel lines with different x-intercepts don't overlap
    elif (x0_start == x0_end) or (x1_start == x1_end):
        # One segment is vertical, the other is not
        # Express non-vertical line in the form of y = mx + b and check y value
        if x1_start == x1_end:
            # Exchange names; the analysis below assumes that line 0 is the vertical one
            x0_start, x0_end, x1_start, x1_end = x1_start, x1_end, x0_start, x0_end
            y0_start, y0_end, y1_start, y1_end = y1_start, y1_end, y0_start, y0_end
        m = (y1_end - y1_start) / (x1_end - x1_start)
        b = (x1_end * y1_start - x1_start * y1_end) / (x1_end - x1_start)
        if min(x1_start, x1_end) <= x0_start <= max(x1_start, x1_end):
            if min(y0_start, y0_end) <= m * x0_start + b <= max(
                    y0_start, y0_end):
                return True
        return False
    else:
        # Neither line is vertical; check slopes and y-intercepts
        b0 = (y0_start * x0_end - y0_end * x0_start) / (
            x0_end - x0_start)  # y-intercept of line 0
        b1 = (y1_start * x1_end - y1_end * x1_start) / (
            x1_end - x1_start)  # y-intercept of line 1
        if (x1_end - x1_start) * (y0_end - y0_start) == (x0_end - x0_start) * (
                y1_end - y1_start):
            # Lines have identical slopes
            if b0 == b1:
                # Same y-intercept -> potential overlap, so check x coordinate
                # Distinct, non-overlapping segments if and only if min x coord of one exceeds max x coord of the other
                return not ((min(x0_start, x0_end) > max(x1_start, x1_end)) or
                            (min(x1_start, x1_end) > max(x0_start, x0_end)))
            return False  # Parallel lines with different y-intercepts don't overlap
        else:
            # Lines not parallel so must intersect somewhere -> examine slopes m0 and m1
            m0 = (y0_end - y0_start) / (x0_end - x0_start)  # slope of line 0
            m1 = (y1_end - y1_start) / (x1_end - x1_start)  # slope of line 1
            x_intersect = (b1 - b0) / (m0 - m1
                                      )  # x coordinate of intersection point
            if min(x0_start, x0_end) <= x_intersect <= max(x0_start, x0_end):
                if min(x1_start, x1_end) <= x_intersect <= max(
                        x1_start, x1_end):
                    return True
            return False


class RouteAnchors(QRoute):
    """Creates and connects a series of anchors through which the Route passes.

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
        * anchors: OrderedDict -- Intermediate anchors only; doesn't include endpoints
        * advanced: Dict
            * avoid_collision: 'false' -- true/false, defines if the route needs to avoid collisions.  Defaults to 'false'.
    """

    component_metadata = Dict(short_name='cpw')
    """Component metadata"""

    default_options = Dict(
        anchors=OrderedDict(
        ),  # Intermediate anchors only; doesn't include endpoints
        # Example: {1: np.array([x1, y1]), 2: np.array([x2, y2])}
        # startpin -> startpin + leadin -> anchors -> endpin + leadout -> endpin
        advanced=Dict(avoid_collision='false'))
    """Default options"""

    TOOLTIP = """Creates and connects a series of anchors through which the Route passes."""

    from shapely.ops import unary_union
    from matplotlib import pyplot as plt
    import geopandas as gpd

    from shapely.geometry import CAP_STYLE, JOIN_STYLE

    def unobstructed_close_up(self, segment: list, component_name: str) -> bool:
        """Checks whether the given component's perimeter intersects or
        overlaps a given segment.

        Args:
            segment (list): 2 vertices, in the form [np.array([x0, y0]), np.array([x1, y1])]
            component_name (str): Alphanumeric component name

        Returns:
            bool: True is no obstacles
        """
        # transform path to polygons
        paths_converted = []
        paths = self.design.components[component_name].qgeometry_table('path')
        for _, row in paths.iterrows():
            paths_converted.append(row['geometry'].buffer(
                row['width'] / 2, cap_style=CAP_STYLE.flat))
        # merge all the polygons
        polygons = self.design.components[component_name].qgeometry_list('poly')
        boundary = gpd.GeoSeries(unary_union(polygons + paths_converted))
        boundary_coords = list(boundary.geometry.exterior[0].coords)
        if any(
                intersecting(segment[0], segment[1], boundary_coords[i],
                             boundary_coords[i + 1])
                for i in range(len(boundary_coords) - 1)):
            # At least 1 intersection with the actual component contour; do not proceed!
            return False
        # All clear, no intersections
        return True

    def unobstructed(self, segment: list) -> bool:
        """Check that no component's bounding box in self.design intersects or
        overlaps a given segment.

        Args:
            segment (list): 2 vertices, in the form [np.array([x0, y0]), np.array([x1, y1])]

        Returns:
            bool: True is no obstacles
        """

        # assumes rectangular bounding boxes
        for component in self.design.components:
            if component == self.name:
                continue
            xmin, ymin, xmax, ymax = self.design.components[
                component].qgeometry_bounds()
            # p, q, r, s are corner coordinates of each bounding box
            p, q, r, s = [
                np.array([xmin, ymin]),
                np.array([xmin, ymax]),
                np.array([xmax, ymin]),
                np.array([xmax, ymax])
            ]
            if any(
                    intersecting(segment[0], segment[1], k, l)
                    for k, l in [(p, q), (p, r), (r, s), (q, s)]):
                # At least 1 intersection with the component bounding box. Check the actual contour.
                if not self.unobstructed_close_up(segment, component):
                    # At least 1 intersection with the actual component contour; do not proceed!
                    return False
        # All clear, no intersections
        return True

    def connect_simple(self, start_pt: QRoutePoint,
                       end_pt: QRoutePoint) -> np.ndarray:
        """Try connecting start and end with single or 2-segment/S-shaped CPWs
        if possible.

        Args:
            start_pt (QRoutePoint): QRoutePoint of the start
            end_pt (QRoutePoint): QRoutePoint of the end

        Returns:
            List of vertices of a CPW going from start to end

        Raises:
            QiskitMetalDesignError: If the connect_simple() has failed.
        """
        avoid_collision = self.parse_options().advanced.avoid_collision

        start_direction = start_pt.direction
        start = start_pt.position
        end_direction = end_pt.direction
        end = end_pt.position

        # end_direction originates strictly from endpoint + leadout (NOT intermediate stopping anchors)
        self.assign_direction_to_anchor(start_pt, end_pt)
        stop_direction = end_pt.direction

        if (start[0] == end[0]) or (start[1] == end[1]):
            # Matching x or y coordinates -> check if endpoints can be connected with a single segment
            if mao.dot(start_direction, end - start) >= 0:
                # Start direction and end - start for CPW must not be anti-aligned
                if (end_direction is None) or (mao.dot(end - start,
                                                       end_direction) <= 0):
                    # If leadout + end has been reached, the single segment CPW must not be aligned with its direction
                    return np.empty((0, 2), float)
        else:
            # If the endpoints don't share a common x or y value:
            # designate them as 2 corners of an axis aligned rectangle
            # and check if both start and end directions are aligned with
            # the displacement vectors between start/end and
            # either of the 2 remaining corners ("perfect alignment").
            corner1 = np.array([start[0],
                                end[1]])  # x coordinate matches with start
            corner2 = np.array([end[0],
                                start[1]])  # x coordinate matches with end
            if avoid_collision:
                # Check for collisions at the outset to avoid repeat work
                startc1end = bool(
                    self.unobstructed([start, corner1]) and
                    self.unobstructed([corner1, end]))
                startc2end = bool(
                    self.unobstructed([start, corner2]) and
                    self.unobstructed([corner2, end]))
            else:
                startc1end = startc2end = True
            if (mao.dot(start_direction, corner1 - start) > 0) and startc1end:
                # corner1 is "in front of" the start_pt
                if (end_direction is None) or (mao.dot(end_direction,
                                                       corner1 - end) >= 0):
                    # corner1 is also "in front of" the end_pt
                    return np.expand_dims(corner1, axis=0)
            elif (mao.dot(start_direction, corner2 - start) > 0) and startc2end:
                # corner2 is "in front of" the start_pt
                if (end_direction is None) or (mao.dot(end_direction,
                                                       corner2 - end) >= 0):
                    # corner2 is also "in front of" the end_pt
                    return np.expand_dims(corner2, axis=0)
            # In notation below, corners 3 and 4 correspond to
            # the ends of the segment bisecting the longer rectangle formed by start and end
            # while the segment formed by corners 5 and 6 bisect the shorter rectangle
            if stop_direction[
                    0]:  # "Wide" rectangle -> vertical middle segment is more natural
                corner3 = np.array([(start[0] + end[0]) / 2, start[1]])
                corner4 = np.array([(start[0] + end[0]) / 2, end[1]])
                corner5 = np.array([start[0], (start[1] + end[1]) / 2])
                corner6 = np.array([end[0], (start[1] + end[1]) / 2])
            else:  # "Tall" rectangle -> horizontal middle segment is more natural
                corner3 = np.array([start[0], (start[1] + end[1]) / 2])
                corner4 = np.array([end[0], (start[1] + end[1]) / 2])
                corner5 = np.array([(start[0] + end[0]) / 2, start[1]])
                corner6 = np.array([(start[0] + end[0]) / 2, end[1]])
            if avoid_collision:
                startc3c4end = bool(
                    self.unobstructed([start, corner3]) and
                    self.unobstructed([corner3, corner4]) and
                    self.unobstructed([corner4, end]))
                startc5c6end = bool(
                    self.unobstructed([start, corner5]) and
                    self.unobstructed([corner5, corner6]) and
                    self.unobstructed([corner6, end]))
            else:
                startc3c4end = startc5c6end = True
            if (mao.dot(start_direction, stop_direction) < 0) and (mao.dot(
                    start_direction, corner3 - start) > 0) and startc3c4end:
                if (end_direction is None) or (mao.dot(end_direction,
                                                       corner4 - end) > 0):
                    # Perfectly aligned S-shaped CPW
                    return np.vstack((corner3, corner4))
            # Relax constraints and check if imperfect 2-segment or S-segment works,
            # where "imperfect" means 1 or more dot products of directions
            # between successive segments is 0; otherwise return an empty list
            if (mao.dot(start_direction, corner1 - start) >= 0) and startc1end:
                if (end_direction is None) or (mao.dot(end_direction,
                                                       corner1 - end) >= 0):
                    return np.expand_dims(corner1, axis=0)
            if (mao.dot(start_direction, corner2 - start) >= 0) and startc2end:
                if (end_direction is None) or (mao.dot(end_direction,
                                                       corner2 - end) >= 0):
                    return np.expand_dims(corner2, axis=0)
            if (mao.dot(start_direction, corner3 - start)
                    >= 0) and startc3c4end:
                if (end_direction is None) or (mao.dot(end_direction,
                                                       corner4 - end) >= 0):
                    return np.vstack((corner3, corner4))
            if (mao.dot(start_direction, corner5 - start)
                    >= 0) and startc5c6end:
                if (end_direction is None) or (mao.dot(end_direction,
                                                       corner6 - end) >= 0):
                    return np.vstack((corner5, corner6))
        raise QiskitMetalDesignError(
            "connect_simple() has failed. This might be due to one of two reasons. "
            f"1. Either one of the start point {start} or the end point {end} "
            "provided are inside the bounding box of another QComponent. "
            "Please move the point, or setup a \"lead\" to exit the QComponent area. "
            "2. none of the 4 routing possibilities of this algorithm "
            "(^|_, ^^|, __|, _|^) can complete. Please use Pathfinder instead")

    def free_manhattan_length_anchors(self):
        """Computes the free-flight manhattan distance between start_pt and
        end_pt passing through all of the given anchor points.

        Returns:
            float: Total length connecting all points in order
        """
        anchors = self.parse_options().anchors
        reference = [self.head.get_tip().position]
        reference.extend(list(anchors.values()))
        reference.append(self.tail.get_tip().position)

        length = 0
        for i in range(1, len(reference)):
            length += abs(reference[i][0] -
                          reference[i - 1][0]) + abs(reference[i][1] -
                                                     reference[i - 1][1])
        return length

    def trim_pts(self):
        """Crops the sequence of points to concatenate.

        For example, if a segment between two anchors has no points,
        then the segment is eliminated (only anchor points will do).
        Modified directly the self.intermediate_pts, thus nothing is
        returned.
        """
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
            arc_pts = self.connect_simple(self.get_tip(), QRoutePoint(coord))
            if arc_pts is None:
                self.intermediate_pts[arc_num] = [coord]
            else:
                self.intermediate_pts[arc_num] = np.concatenate(
                    [arc_pts, [coord]], axis=0)
        arc_pts = self.connect_simple(self.get_tip(), end_point)
        if arc_pts is not None:
            self.intermediate_pts[len(anchors)] = np.array(arc_pts)

        # concatenate all points, transforming the dictionary into a single numpy array
        self.trim_pts()
        self.intermediate_pts = np.concatenate(list(
            self.intermediate_pts.values()),
                                               axis=0)

        # Make points into elements
        self.make_elements(self.get_points())
