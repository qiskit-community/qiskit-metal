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

import numpy as np
from numpy.linalg import norm
from qiskit_metal import Dict
from qiskit_metal.qlibrary.core import QRoute
from qiskit_metal.toolbox_metal import math_and_overrides as mao


class RouteFramed(QRoute):
    """A non-meandered sample_shapes CPW that is auto-generated between 2 components.
    Designed to avoid self-collisions and collisions with components it is
    attached to.

    This class extends the `QComponent` class.

    .. meta::
        Routed Frame

    Assumptions:
        1. Components are situated along xy axes in 2 dimensions. No rotation is allowed (yet). Their bounding boxes may
           not overlap, though they may be situated at arbitrary x and y provided these conditions are met.
        2. Pins point normal to qubits ("directly outward") and either in the x or y directions. They must not protrude
           from the exact corner of a component. [This last assumption has implications for 2-segment connections.]
        3. Intersection of CPWs with themselves or the qubits they stem from is prohibited. Intersection with other
           components/CPWs has not yet been considered.
        4. Components may not share an edge; a nonzero gap must be present between 2 adjacent qubits.
        5. CPWs must be attached to protruding leads via terminations head-on, not from the sides.
    """

    component_metadata = Dict(short_name='cpw')
    """Component metadata"""

    TOOLTIP = """A non-meandered basic CPW that is auto-generated between 2 components."""

    def make(self):
        """Use user-specified parameters and geometric orientation of
        components to determine whether the CPW connecting the pins on either
        end requires 1, 2, or 3 segments. Preference given to shorter paths and
        paths that flow with the leadin and leadout directions rather than
        turning immediately at 90 deg.

        Keepout region along x and y directions specified for CPWs that
        wrap around outer perimeter of overall bounding box of both
        components.
        """

        self.__pts = []  # list of 2D numpy arrays containing vertex locations

        p = self.p  # parsed options

        w = p.trace_width
        leadstart = p.lead.start_straight
        leadend = p.lead.end_straight
        keepoutx = 0.2
        keepouty = 0.2

        # Set the CPW pins and add the points/directions to the lead-in/out arrays
        self.set_pin("start")
        self.set_pin("end")

        # Align the lead-in/out to the input options set from the user
        meander_start_point = self.set_lead("start")
        meander_end_point = self.set_lead("end")

        n1 = meander_start_point.direction
        n2 = meander_end_point.direction

        m1 = meander_start_point.position
        m2 = meander_end_point.position

        component_start = p.pin_inputs['start_pin']['component']
        component_end = p.pin_inputs['end_pin']['component']

        # Coordinates of bounding box for each individual component
        minx1, miny1, maxx1, maxy1 = self.design.components[
            component_start].qgeometry_bounds()
        minx2, miny2, maxx2, maxy2 = self.design.components[
            component_end].qgeometry_bounds()

        # Coordinates of overall bounding box which includes both components
        minx, miny = min(minx1, minx2), min(miny1, miny2)
        maxx, maxy = max(maxx1, maxx2), max(maxy1, maxy2)

        # Normdot is dot product of normal vectors
        normdot = mao.dot(n1, n2)

        if normdot == -1:
            # Modify CPW endpoints to include mandatory w / 2 leadin plus user defined leadin
            m1ext = m1 + n1 * (w / 2 + leadstart)
            m2ext = m2 + n2 * (w / 2 + leadend)
            # Alignment is between displacement of modified positions (see above) and normal vector
            alignment = mao.dot((m2ext - m1ext) / norm(m2ext - m1ext), n1)
            if alignment == 1:
                # Normal vectors point directly at each other; no obstacles in between
                # Connect with single segment; generalizes to arbitrary angles with no snapping
                self.__pts = self.connect_frame(1)
            elif alignment > 0:
                # Displacement partially aligned with normal vectors
                # Connect with antisymmetric 3-segment CPW
                if n1[1] == 0:
                    # Normal vectors horizontal
                    if minx2 < maxx1:
                        self.__pts = self.connect_frame(3, 0,
                                                        (minx2 + maxx1) / 2)
                    else:
                        self.__pts = self.connect_frame(3, 0,
                                                        (minx1 + maxx2) / 2)
                else:
                    # Normal vectors vertical
                    if miny2 < maxy1:
                        self.__pts = self.connect_frame(3, 1,
                                                        (miny2 + maxy1) / 2)
                    else:
                        self.__pts = self.connect_frame(3, 1,
                                                        (miny1 + maxy2) / 2)
            elif alignment == 0:
                # Displacement orthogonal to normal vectors
                # Connect with 1 segment
                self.__pts = self.connect_frame(1)
            elif alignment < 0:
                # Normal vectors on opposite sides of squares
                if n1[1] == 0:
                    # Normal vectors horizontal
                    if maxy1 < miny2:
                        self.__pts = self.connect_frame(3, 1,
                                                        (maxy1 + miny2) / 2)
                    elif maxy2 < miny1:
                        self.__pts = self.connect_frame(3, 1,
                                                        (maxy2 + miny1) / 2)
                    else:
                        # Gap running only vertically -> must wrap around with shorter of 2 possibilities
                        # pts_top represents 3-segment CPW running along top edge of overall bounding box
                        # pts_bott represents 3-segment CPW running along bottom edge of overall bounding box
                        pts_top = self.connect_frame(3, 1, maxy + keepouty)
                        pts_bott = self.connect_frame(3, 1, miny - keepouty)
                        if self.totlength(pts_top) < self.totlength(pts_bott):
                            self.__pts = pts_top
                        else:
                            self.__pts = pts_bott
                else:
                    # Normal vectors vertical
                    if maxx1 < minx2:
                        self.__pts = self.connect_frame(3, 0,
                                                        (maxx1 + minx2) / 2)
                    elif maxx2 < minx1:
                        self.__pts = self.connect_frame(3, 0,
                                                        (maxx2 + minx1) / 2)
                    else:
                        # Gap running only horizontally -> must wrap around with shorter of 2 possibilities
                        # pts_left represents 3-segment CPW running along left edge of overall bounding box
                        # pts_right represents 3-segment CPW running along right edge of overall bounding box
                        pts_left = self.connect_frame(3, 0, minx - keepoutx)
                        pts_right = self.connect_frame(3, 0, maxx + keepoutx)
                        if self.totlength(pts_left) < self.totlength(pts_right):
                            self.__pts = pts_left
                        else:
                            self.__pts = pts_right
        elif normdot == 0:
            # Normal vectors perpendicular to each other
            if (m1[0] in [minx, maxx]) and (m2[1] in [miny, maxy]):
                # Both pins on perimeter of overall bounding box, but not at corner
                self.__pts = self.connect_frame(2)
            elif (m1[1] in [miny, maxy]) and (m2[0] in [minx, maxx]):
                # Both pins on perimeter of overall bounding box, but not at corner
                self.__pts = self.connect_frame(2)
            elif (m1[0] not in [minx, maxx]) and (m2[0] not in [
                    minx, maxx
            ]) and (m1[1] not in [miny, maxy]) and (m2[1] not in [miny, maxy]):
                # Neither pin lies on perimeter of overall bounding box
                # Always possible to connect with at most 2 segments
                if (m1[0] == m2[0]) or (m1[1] == m2[1]):
                    # Connect directly with 1 segment
                    self.__pts = self.connect_frame(1)
                else:
                    # Connect with 2 segments
                    self.__pts = self.connect_frame(2)
            elif (m1[0] in [minx, maxx]) or (m1[1] in [miny, maxy]):
                # Pin 1 lies on boundary of overall bounding box but pin 2 does not
                if m1[0] in [minx, maxx]:
                    # Pin 1 on left or right boundary, pointing left or right, respectively
                    if n2[1] > 0:
                        # Pin 2 pointing up
                        if miny1 > maxy2:
                            self.__pts = self.connect_frame(2)
                        else:
                            self.__pts = self.connect_frame(
                                3, 1, maxy + keepouty)
                    else:
                        # Pin 2 pointing down
                        if miny2 > maxy1:
                            self.__pts = self.connect_frame(2)
                        else:
                            self.__pts = self.connect_frame(
                                3, 1, miny - keepouty)
                elif m1[1] in [miny, maxy]:
                    # Pin 1 on bottom or top boundary, pointing down or up, respectively
                    if n2[0] < 0:
                        # Pin 2 pointing left
                        if minx2 > maxx1:
                            self.__pts = self.connect_frame(2)
                        else:
                            self.__pts = self.connect_frame(
                                3, 0, minx - keepoutx)
                    else:
                        # Pin 2 pointing right
                        if minx1 > maxx2:
                            self.__pts = self.connect_frame(2)
                        else:
                            self.__pts = self.connect_frame(
                                3, 0, maxx + keepoutx)
            elif (m2[0] in [minx, maxx]) or (m2[1] in [miny, maxy]):
                # Pin 2 lies on boundary of overall bounding box but pin 1 does not
                if m2[0] in [minx, maxx]:
                    # Pin 2 on left or right boundary, pointing left or right, respectively
                    if n1[1] > 0:
                        # Pin 1 pointing up
                        if miny2 > maxy1:
                            self.__pts = self.connect_frame(2)
                        else:
                            self.__pts = self.connect_frame(
                                3, 1, maxy + keepouty)
                    else:
                        # Pin 1 pointing down
                        if miny1 > maxy2:
                            self.__pts = self.connect_frame(2)
                        else:
                            self.__pts = self.connect_frame(
                                3, 1, miny - keepouty)
                elif m2[1] in [miny, maxy]:
                    # Pin 2 on bottom or top boundary, pointing down or up, respectively
                    if n1[0] < 0:
                        # Pin 1 pointing left
                        if minx1 > maxx2:
                            self.__pts = self.connect_frame(2)
                        else:
                            self.__pts = self.connect_frame(
                                3, 0, minx - keepoutx)
                    else:
                        # Pin 1 pointing right
                        if minx2 > maxx1:
                            self.__pts = self.connect_frame(2)
                        else:
                            self.__pts = self.connect_frame(
                                3, 0, maxx + keepoutx)
        else:
            # Normal vectors pointing in same direction
            if ((m1[0] == m2[0]) or
                (m1[1] == m2[1])) and (mao.dot(n1, m2 - m1) == 0):
                # Connect directly with 1 segment
                self.__pts = self.connect_frame(1)
            elif n1[1] == 0:
                # Normal vectors horizontal
                if (m1[1] > maxy2) or (m2[1] > maxy1):
                    # Connect with 2 segments
                    self.__pts = self.connect_frame(2)
                else:
                    # Must wrap around with shorter of the 2 following possibilities:
                    # pts_top represents 3-segment CPW running along top edge of overall bounding box
                    # pts_bott represents 3-segment CPW running along bottom edge of overall bounding box
                    pts_top = self.connect_frame(3, 1, maxy + keepouty)
                    pts_bott = self.connect_frame(3, 1, miny - keepouty)
                    if self.totlength(pts_top) < self.totlength(pts_bott):
                        self.__pts = pts_top
                    else:
                        self.__pts = pts_bott
            else:
                # Normal vectors vertical
                if (m1[0] > maxx2) or (m2[0] > maxx1):
                    # Connect with 2 segments
                    self.__pts = self.connect_frame(2)
                else:
                    # Must wrap around with shorter of the 2 following possibilities:
                    # pts_left represents 3-segment CPW running along left edge of overall bounding box
                    # pts_right represents 3-segment CPW running along right edge of overall bounding box
                    pts_left = self.connect_frame(3, 0, minx - keepoutx)
                    pts_right = self.connect_frame(3, 0, maxx + keepoutx)
                    if self.totlength(pts_left) < self.totlength(pts_right):
                        self.__pts = pts_left
                    else:
                        self.__pts = pts_right

        self.intermediate_pts = self.__pts

        # Make points into elements
        self.make_elements(self.get_points())

    def connect_frame(self, segments: int, constaxis=0, constval=0) -> list:
        """Generate the list of 2D coordinates comprising a CPW between
        startpin and endpin.

        Args:
            startpin (str): Name of startpin
            endpin (str): Name of endpin
            width (float): Width of CPW in mm
            segments (int): Number of segments in the CPW, not including leadin and leadout. Ranges from 1 to 3.
            leadstart (float): Length of first CPW segment originating at startpin
            leadend (float): Length of final CPW segment ending at endpin
            constaxis (int, optional): In the case of 3 segment CPWs, the constant axis of the line that both
                leadin and leadout must connect to. Example: If x = 3, the constant axis (x) is 0.  Defaults to 0.
            constval (int, optional): In the case of 3 segment CPWs, the constant numerical value of the line
                that both leadin and leadout must connect to. Example: If x = 3, the constant value is 3.  Defaults to 0.

        Returns:
            List: [np.array([x0, y0]), np.array([x1, y1]), np.array([x2, y2])] where xi, yi are vertices of CPW.
        """

        start = self.head.get_tip()
        end = self.tail.get_tip()

        if segments == 1:
            # Straight across or up and down; no additional points necessary
            midcoords = []
        elif segments == 2:
            # Choose between 2 diagonally opposing corners so that CPW doesn't trace back on itself
            corner1 = np.array([(start.position)[0], (end.position)[1]])
            corner2 = np.array([(end.position)[0], (start.position)[1]])
            startc1 = mao.dot(corner1 - (start.position), start.direction)
            endc1 = mao.dot(corner1 - (end.position), end.direction)
            startc2 = mao.dot(corner2 - (start.position), start.direction)
            endc2 = mao.dot(corner2 - (end.position), end.direction)
            # If both pins' normal vectors point towards one of the corners, pick that corner
            if (startc1 > 0) and (endc1 > 0):
                midcoords = [corner1]
            elif (startc2 > 0) and (endc2 > 0):
                midcoords = [corner2]
            elif min(startc1, endc1) >= 0:
                midcoords = [corner1]
            else:
                midcoords = [corner2]
        elif segments == 3:
            # Connect start and end to long segment at constaxis
            # 2 additional intermediate points needed to achieve this
            if constaxis == 0:
                # Middle segment lies on the line x = c for some constant c
                midcoord_start = np.array([constval, (start.position)[1]])
                midcoord_end = np.array([constval, (end.position)[1]])
            else:
                # Middle segment lies on the line y = d for some constant d
                midcoord_start = np.array([(start.position)[0], constval])
                midcoord_end = np.array([(end.position)[0], constval])
            midcoords = [midcoord_start, midcoord_end]
        startpts = [start.position]
        endpts = [end.position]
        return startpts + midcoords + endpts

    def totlength(self, pts: list) -> float:
        """Get total length of all line segments in a given CPW."""
        return sum(norm(pts[i] - pts[i - 1]) for i in range(1, len(pts)))
