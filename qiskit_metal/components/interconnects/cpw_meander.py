"""
@author: Marco Facchini, John Blair, Zlatko Minev
"""

from collections import namedtuple
from typing import List, Tuple, Union

from numpy.linalg import norm
from qiskit_metal.draw.utility import vec_unit_planar

import numpy as np
from qiskit_metal import draw, Dict, QComponent
from qiskit_metal import is_true

# from qiskit_metal.toolbox_metal.parsing import is_true
options = Dict(pin_start_name='Q1_a',
               pin_end_name='Q2_b',
               meander=Dict(
                   lead_start='0.1mm',
                   lead_end='0.1mm',
                   asymmetry='0 um')
               )


class Oriented_2D_Array:
    r"""A simple class to define a 2D Oriented_Point,
    with a 2D position and a 2D direction (XY plane).
    All values stored as np.ndarray of parsed floats.

    Attributes:
        positon (np.ndarray of 2 points) -- Position of the Oriented_Point
        direction (np.ndarray of 2 points) -- *Normal vector* of the Oriented_Point, defines which way it points outward.
                                              This is the normal vector to the surface on which the Oriented_Point mates.
                                              Has unit norm.
    """

    # TODO: Maybe move this class out of here, more general.

    def __init__(self, position: np.ndarray, direction: np.ndarray):
        self.positions = np.expand_dims(position, axis=0)
        self.directions = np.expand_dims(vec_unit_planar(direction), axis=0)

    def go_straight(self, length: float):
        """Add a point ot 'lenght' distance in the same direction

        Args:
            length (float) : how much to move by
        """
        self.directions = np.append(self.directions, [self.directions[-1]], axis=0)
        self.positions = np.append(self.positions, [self.positions[-1] + self.directions[-1] * length], axis=0)

    def go_left(self, length: float):
        """Straight line 90deg counter-clock-wise direction w.r.t. Oriented_Point

        Args:
            length (float) : how much to move by
        """
        self.directions = np.append(self.directions, [draw.Vector.rotate(self.directions, np.pi / 2)], axis=0)
        self.positions = np.append(self.positions, [self.positions[-1] + self.directions[-1] * length], axis=0)

    def go_right(self, length: float):
        """Straight line 90deg clock-wise direction w.r.t. Oriented_Point

        Args:
            length (float) : how much to move by
        """
        self.directions = np.append(self.directions, [draw.Vector.rotate(self.directions, -1 * np.pi / 2)], axis=0)
        self.positions = np.append(self.positions, [self.positions[-1] + self.directions[-1] * length], axis=0)

    def align_to(self, concurrent_array):
        """
        In this code, meanders need to face each-other to connect.
        TODO: Make sure the two points align on one of the axes, adding a new point
        TODO: Adjusts the orientation of the meander, adding yet a new point
            * Includes the start but not the given end point
            * If it cannot meander just returns the initial start point

        Arguments:
            concurrent_array {Oriented_2D_Array} -- Other end of the CPW
        """
        print(self.positions[-1])
        print(concurrent_array.positions[-1])

        # determine relative position
        concurrent_position = ""
        oriented_distance = concurrent_array.positions[-1] - self.positions[-1]
        if oriented_distance[1] > 0:
            concurrent_position = "N"
        elif oriented_distance[1] < 0:
            concurrent_position = "S"
        else:
            return  # points already aligned
        if oriented_distance[0] > 0:
            concurrent_position += "E"
        elif oriented_distance[1] < 0:
            concurrent_position += "W"
        else:
            return  # points already aligned

        # TODO implement vertical alignment. Only using horizontal alignment for now
        # if oriented_distance[0] > oriented_distance[1]:
        #     # Vertical alignment
        #     pass
        # else:
        #     # horizontal alignment
        #     pass # code below

        if np.dot(self.directions[-1], concurrent_array.directions[-1]) == -1:
            # points are facing each other or opposing each other
            if (("E" in concurrent_position and self.directions[-1][0] > 0)
                    or ("N" in concurrent_position and self.directions[-1][1] > 0)):
                # facing each other
                pass
            else:
                # opposing each other
                pass
        elif np.dot(self.directions[-1], concurrent_array.directions[-1]) == 1:
            # points are facing the same direction
            if (("E" in concurrent_position and self.directions[-1][0] > 0)
                    or ("N" in concurrent_position and self.directions[-1][1] > 0)):
                # facing each other
                pass
            else:
                # opposing each other
                pass
        else:
            # points are orthogonal to ach other
            pass


class Oriented_Point:
    r"""A simple class to define a 2D Oriented_Point,
    with a 2D position and a 2D direction (XY plane).
    All values stored as np.ndarray of parsed floats.

    Attributes:
        positon (np.ndarray of 2 points) -- Position of the Oriented_Point
        direction (np.ndarray of 2 points) -- *Normal vector* of the Oriented_Point, defines which way it points outward.
                                              This is the normal vector to the surface on which the Oriented_Point mates.
                                              Has unit norm.
    """

    # TODO: Maybe move this class out of here, more general.

    def __init__(self, array: Oriented_2D_Array):
        self.position = array.positions[-1]
        self.direction = array.directions[-1]


class CpwMeanderSimple(QComponent):
    """A meandered basic CPW.

    **Behavior and parameters**
        #TODO: @john_blair / @marco
        Explain and comment on what options do?
        For example, note that lead_direction_inverted can be 'false' or 'true'
    """
    default_options = Dict(
        pin_start_name='',
        pin_end_name='',
        total_length='7mm',
        chip='main',
        layer='1',
        trace_width='cpw_width',
        trace_gap='cpw_gap',

        meander=Dict(
            spacing='200um',
            lead_start='0.1mm',
            lead_end='0.1mm',
            lead_direction_inverted='false',
            snap='true',
            asymmetry='0 um',
        )
    )

    def make(self):
        # TODO: Later, consider performance of instantiating all these Oriented_Point classes

        # parsed options
        # p = self.parse_value(self.options)  # type: Dict
        p = self.p
        snap = is_true(p.meander.snap)
        total_length = p.total_length
        lead_start = p.meander.lead_start
        lead_end = p.meander.lead_end

        # Oriented_Point start and end
        start_points = Oriented_2D_Array(*self.get_start())
        end_points = Oriented_2D_Array(*self.get_end())

        # Lead in to meander
        lead_in = max(lead_start, p.trace_width / 2)
        lead_out = max(lead_end, p.trace_width / 2)
        start_points.go_straight(lead_in)
        end_points.go_straight(lead_out)
        if snap:
            # TODO: adjust the terminations to be sure the meander connects well on both ends
            # start_points.align_to(end_points)
            pass

        # Meander
        length_meander = total_length - (lead_in + lead_out)
        if snap:
            # handle y distance
            length_meander -= 0  # (end.position - endm.position)[1]

        meandered_pts = self.meander_fixed_length(
            start_points, end_points, length_meander, p.meander)

        # TODO: if lead_start is zero or end is , then dont add them
        # points = np.concatenate([
        #     start_pts,
        #     meandered_pts,
        #     end_pts], axis=0)

        points = np.concatenate([
            start_points.positions,
            meandered_pts,
            end_points.positions[::-1]], axis=0)

        # Make points into elements
        self.make_elements(points)

    def meander_fixed_length(self, start_array: Oriented_2D_Array, end_array: Oriented_2D_Array,
                             length: float, meander_opt: dict) -> np.ndarray:
        """
        Meanders using a fixed length and fixed spacing.
        Adjusts the width of the meander
            * Includes the start but not the given end point
            * If it cannot meander just returns the initial start point

        Arguments:
            start {Oriented_Point} -- Oriented_Point of the start
            end {Oriented_Point} -- [description]
            length {str} --  Total length of the meander whole CPW segment (defined by user, after you subtract lead lengths
            meander {dict} -- meander options (parsed)

        Returns:
            np.ndarray -- [description]
        """

        """ To prototype, you can use code here:
            ax = plt.gca()
            ax.cla()
            draw.mpl.render([
                draw.LineString(root_pts),
                draw.LineString(bot_pts),
                draw.LineString(top_pts),
            ], kw=dict(lw=0, alpha=0.5, marker='o'), ax=ax)

            draw.mpl.render([
                draw.LineString(pts)
            ], kw=dict(lw=2, alpha=0.5, marker='x'), ax=ax)
        """

        ################################################################
        # Setup

        # Parameters
        spacing = meander_opt.spacing  # Horizontal spacing between meanders
        asymmetry = meander_opt.asymmetry
        snap = is_true(meander_opt.snap)  # snap to xy grid
        # TODO: snap add 45 deg snap by changing snap function using angles

        # TODO: remove adapter below, incorporate new class in the data
        start = Oriented_Point(start_array)
        end = Oriented_Point(end_array)

        # Coordinate system (example: x to the right => sideways up)
        forward, sideways = self.get_unit_vectors(start, end, snap)
        if is_true(meander_opt.lead_direction_inverted):
            sideways *= -1

        # Calculate lengths and meander number
        dist = end.position - start.position
        if snap:
            # TODO: Not general, depends on the outside (to fix)
            length_direct = abs(norm(np.dot(dist, forward)))
            length_excess = abs(norm(np.dot(dist, sideways)))  # in the vertical direction
        else:
            length_direct = norm(dist)
            length_excess = 0

        # Breakup into sections
        meander_number = np.floor(length_direct / spacing)
        if meander_number < 1:
            self.logger.info(f'Zero meanders for {self.name}')
            # TODO: test if this should return empty instead
            return start.position

        # Adjust meander_number w.r.t. what the roots "directionality" allows
        if round(np.dot(start.direction, sideways) * np.dot(end.direction, sideways)) > 0 and (meander_number % 2) == 0:
            # even meander_number is no good if roots have same orientation (w.r.t sideway)
            meander_number -= 1
        elif round(np.dot(start.direction, sideways) * np.dot(end.direction, sideways)) < 0 and (
                meander_number % 2) == 1:
            # odd meander_number is no good if roots have opposite orientation (w.r.t sideway)
            meander_number -= 1

        # should the first meander go sideways or counter sideways?
        if round(np.dot(start.direction, sideways), 10) > 0:
            first_meander_sideways = True  # sideway direction
        elif round(np.dot(start.direction, sideways), 10) < 0:
            first_meander_sideways = False  # opposite to sideway direction
        else:
            if round(np.dot(end.direction, sideways), 10) > 0:
                first_meander_sideways = ((meander_number % 2) == 1)  # sideway direction
            elif round(np.dot(end.direction, sideways), 10) < 0:
                first_meander_sideways = ((meander_number % 2) == 0)  # opposite to sideway direction
            else:
                # either direction is fine, so let's just pick one
                first_meander_sideways = True

        # TODO: does this go with below TODO?
        # length of segment between two root points
        length_segment = (length - length_excess -
                          (length_direct - meander_number * spacing)  # the last little bit
                          - 2 * asymmetry
                          ) / meander_number
        length_perp = (length_segment - spacing) / 2.  # perpendicular length

        # TODO: BUG fix when assymmetry is large and negative
        if asymmetry < 0:
            if abs(asymmetry) > length_perp:
                print('Trouble')
                length_segment -= (abs(asymmetry) - length_perp) / 2
                length_perp = (length_segment - spacing) / 2.  # perpendicular length

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
        root_pts = middle_points
        side_shift_vecs = np.array([sideways * length_perp] * len(root_pts))
        asymmetry_vecs = np.array([sideways * asymmetry] * len(root_pts))
        top_pts = root_pts + side_shift_vecs + asymmetry_vecs
        bot_pts = root_pts - side_shift_vecs + asymmetry_vecs

        ################################################################
        # Combine points
        # Meanest part of the meander

        # Add 2 for the lead and end points in the cpw from
        # pts will have to store properly alternated top_pts and bot_pts
        # it will also store left-most and right-most root_pts (start-end) after adjustment
        # 2 points from top_pts and bot_pts will be dropped for a complete meander
        pts = np.zeros((len(top_pts) + len(bot_pts) + 2 - 2, 2))
        pts[0, :] = root_pts[0, :]
        pts[-1, :] = root_pts[-1, :]
        idx_side1_meander, odd = self.get_index_for_side1_meander(len(root_pts))
        idx_side2_meander = 2 + idx_side1_meander[:None if odd else -2]
        if first_meander_sideways:
            pts[idx_side1_meander, :] = top_pts[:-1 if odd else None]
            pts[idx_side2_meander, :] = bot_pts[1:None if odd else -1]
        else:
            pts[idx_side1_meander, :] = bot_pts[:-1 if odd else None]
            pts[idx_side2_meander, :] = top_pts[1:None if odd else -1]

        pts += start.position  # move to start position

        if snap:
            # the right-most root_pts need to be aligned with the end.position point
            pts[-1, abs(forward[0])] = end.position[abs(forward[0])]

        self.pts = pts
        self.forward = forward
        self.sideways = sideways

        return pts

    @staticmethod
    def get_index_for_side1_meander(num_root_pts: int):
        num_2pts, odd = divmod(num_root_pts, 2)

        x = np.array(range(num_2pts), dtype=int) * 4
        z = np.zeros(num_2pts * 2, dtype=int)
        z[::2] = x
        z[1::2] = x + 1
        z += 1
        return z, odd

    def get_start(self) -> List:
        """Return the start point and normal direction vector

        Returns:
            A dictionary with keys `point` and `direction`.
            The values are numpy arrays with two float points each.
        """
        pin = self.design.connectors[self.options.pin_start_name]
        position = pin['middle']
        direction = pin['normal']
        return position, direction

    def get_end(self) -> List:
        """Return the start point and normal direction vector

        Returns:
            A dictionary with keys `point` and `direction`.
            The values are numpy arrays with two float points each.
        """
        pin = self.design.connectors[self.options.pin_end_name]
        position = pin['middle']
        direction = pin['normal']
        return position, direction

    def get_unit_vectors(self, start: Oriented_Point, end: Oriented_Point, snap: bool = False) -> Tuple[np.ndarray]:
        """Return the unit and target vector in which the CPW should procees as its
        cooridnate sys.

        Arguments:
            start {Oriented_Point} -- [description]
            end {Oriented_Point} -- [description]

        Returns:
            straight and 90 deg CCW rotated vecs 2D
            (array([1., 0.]), array([0., 1.]))
        """
        # handle chase when star tnad end are same?
        v = end.position - start.position
        direction = v / norm(v)
        if snap:
            direction = draw.Vector.snap_unit_vector(direction, flip=False)
        normal = draw.Vector.rotate(direction, np.pi / 2)
        return direction, normal

    def make_elements(self, pts: np.ndarray):
        """Turns points into elements"""
        p = self.p
        line = draw.LineString(pts)
        layer = p.layer
        width = p.trace_width
        self.options._actual_length = str(line.length) + ' ' + self.design.get_units()
        self.add_elements('path',
                          {'trace': line},
                          width=width,
                          layer=layer)
        self.add_elements('path',
                          {'cut': line},
                          width=width + p.trace_gap,
                          layer=layer,
                          subtract=True)
