"""
@author: Marco Facchini, John Blair, Zlatko Minev
"""

from typing import List, Tuple, Union

from numpy.linalg import norm
from qiskit_metal.draw.utility import vec_unit_planar

import numpy as np
from qiskit_metal import draw, Dict
from qiskit_metal.components import QComponent
from qiskit_metal.toolbox_metal.parsing import is_true


class Oriented_2D_Array:
    r"""A simple class to define a 2D Oriented_Point,
    with a 2D position and a 2D direction (XY plane).
    All values stored as np.ndarray of parsed floats.
    """

    # TODO: Maybe move this class out of here, more general.

    def __init__(self, position: np.ndarray, direction: np.ndarray):
        """
        Args:
            positon (np.ndarray of 2 points): Center position of the connector
            direction (np.ndarray of 2 points): *Normal vector* of the connector, defines which way it
                points outward.
                This is the normal vector to the surface on which the connector mates.
                Has unit norm.
        """
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
        # THIS METHOD IS NOT USED AT THIS TIME (7/2/20)
        """Straight line 90deg counter-clock-wise direction w.r.t. Oriented_Point

        Args:
            length (float): how much to move by
        """
        self.directions = np.append(self.directions, [draw.Vector.rotate(self.directions, np.pi / 2)], axis=0)
        self.positions = np.append(self.positions, [self.positions[-1] + self.directions[-1] * length], axis=0)

    def go_right(self, length: float):
        """Straight line 90deg clock-wise direction w.r.t. Oriented_Point

        Args:
            length (float): how much to move by

        THIS METHOD IS NOT USED AT THIS TIME (7/2/20)
        """
        self.directions = np.append(self.directions, [draw.Vector.rotate(self.directions, -1 * np.pi / 2)], axis=0)
        self.positions = np.append(self.positions, [self.positions[-1] + self.directions[-1] * length], axis=0)

    @property
    def get_length(self):
        """Sum of all segments length

        Return:
            length (float): full point_array length
        """
        length = 0
        for x in range(len(self.positions) - 1):
            length += abs(norm(self.positions[x] - self.positions[x + 1]))
            return length

    def align_to(self, concurrent_array):
        # THIS METHOD IS NOT USED AT THIS TIME (7/2/20)
        """
        In this code, meanders need to face each-other to connect.

        TODO: Make sure the two points align on one of the axes, adding a new point

        TODO: Adjusts the orientation of the meander, adding yet a new point:
            * Includes the start but not the given end point
            * If it cannot meander just returns the initial start point

        Arguments:
            concurrent_array (Oriented_2D_Array): Other end of the CPW
        """

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
    """

    # TODO: Maybe move this class out of here, more general.

    def __init__(self, array: Oriented_2D_Array):
        """
        Arguments:
            array (Oriented_2D_Array): 2D array
        """
        self.position = array.positions[-1]
        self.direction = array.directions[-1]


class CpwMeanderSimple(QComponent):
    """A meandered basic CPW.

    Inherits QComponent class

    **Behavior and parameters**:
        * #TODO: @john_blair / @marco
        * Explain and comment on what options do?
        * For example, note that lead_direction_inverted can be 'false' or 'true'
    """
    default_options = Dict(
        pin_inputs=Dict(
            start_pin=Dict(
                component='',  # Name of component to start from, which has a pin
                pin=''),  # Name of pin used for pin_start
            end_pin=Dict(
                component='',  # Name of component to end on, which has a pin
                pin='')  # Name of pin used for pin_end
        ),
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
    """Default options"""

    def make(self):
        """
        The make function implements the logic that creates the geoemtry
        (poly, path, etc.) from the qcomponent.options dictionary of parameters,
        and the adds them to the design, using qcomponent.add_qgeometry(...),
        adding in extra needed information, such as layer, subtract, etc.
        """
        # parsed options
        p = self.p
        snap = is_true(p.meander.snap)
        total_length = p.total_length
        lead_start = p.meander.lead_start
        lead_end = p.meander.lead_end

        # Set the CPW pins and add the points/directions to the lead-in/out arrays
        start_points = Oriented_2D_Array(*self.set_pin("start"))
        end_points = Oriented_2D_Array(*self.set_pin("end"))

        # Align the lead-in/out to the input options set from the user
        lead_in = max(lead_start, p.trace_width / 2)  # minimum lead, to be able to jog correctly
        lead_out = max(lead_end, p.trace_width / 2)  # minimum lead, to be able to jog correctly
        start_points.go_straight(lead_in)
        end_points.go_straight(lead_out)

        if snap:
            # TODO: adjust the terminations to be sure the meander connects well on both ends
            # start_points.align_to(end_points)
            pass

        # Meander
        length_meander = total_length - (start_points.get_length + end_points.get_length)
        if snap:
            # handle y distance
            length_meander -= 0  # (end.position - endm.position)[1]

        meandered_pts = self.meander_fixed_length(
            start_points, end_points, length_meander, p.meander)

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

        Arguments:
            start (Oriented_Point): Oriented_Point of the start
            end (Oriented_Point): Oriented_Point of the end
            length (str): Total length of the meander whole CPW segment (defined by user, after you subtract lead lengths
            meander (dict): meander options (parsed)

        Returns:
            np.ndarray: Array of points

        Adjusts the width of the meander:
            * Includes the start but not the given end point
            * If it cannot meander just returns the initial start point
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
            length_direct = abs(norm(np.dot(dist, forward)))  # in the vertical direction
            length_sideways = abs(norm(np.dot(dist, sideways)))  # in the orthogonal direction
        else:
            length_direct = norm(dist)
            length_sideways = 0

        # Breakup into sections
        meander_number = np.floor(length_direct / spacing)
        if meander_number < 1:
            self.logger.info(f'Zero meanders for {self.name}')
            # TODO: test if this should return empty instead
            return start.position

        # The start and end points can have 4 directions each. Depending on the direction
        # there might be not enough space for all the meanders, thus here we adjust
        # meander_number w.r.t. what the start and end points "directionality" allows
        if round(np.dot(start.direction, sideways) * np.dot(end.direction, sideways)) > 0 and (meander_number % 2) == 0:
            # even meander_number is no good if roots have same orientation (w.r.t sideway)
            meander_number -= 1
        elif round(np.dot(start.direction, sideways) * np.dot(end.direction, sideways)) < 0 and (
                meander_number % 2) == 1:
            # odd meander_number is no good if roots have opposite orientation (w.r.t sideway)
            meander_number -= 1

        # should the first meander go sideways or counter sideways?
        start_meander_direction = round(np.dot(start.direction, sideways), 10)
        end_meander_direction = round(np.dot(end.direction, sideways), 10)
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
        length_excess = (length - length_direct - 2 * abs(asymmetry))
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

        pts += start.position  # move to start position

        # TODO: the below, changes the CPW total length. Need to account for this earlier
        if snap:
            # the right-most root_pts need to be aligned with the end.position point
            pts[-1, abs(forward[0])] = end.position[abs(forward[0])]
        if abs(asymmetry) > abs(length_perp):
            if start_meander_direction * asymmetry < 0:  # sideway direction
                pts[0, abs(forward[0])] = start.position[abs(forward[0])]
                pts[1, abs(forward[0])] = start.position[abs(forward[0])]
            if end_meander_direction * asymmetry < 0:  # sideway direction
                pts[-2, abs(forward[0])] = end.position[abs(forward[0])]
                pts[-3, abs(forward[0])] = end.position[abs(forward[0])]

        # print("PTS->", pts)

        self.pts = pts
        self.forward = forward
        self.sideways = sideways

        return pts

    @staticmethod
    def get_index_for_side1_meander(num_root_pts: int):
        """
        Get the indecies

        Args:
            root_pts (list): List of points

        Returns:
            tuple: Tuple of indecies
        """
        num_2pts, odd = divmod(num_root_pts, 2)

        x = np.array(range(num_2pts), dtype=int) * 4
        z = np.zeros(num_2pts * 2, dtype=int)
        z[::2] = x
        z[1::2] = x + 1
        z
        return z, odd

    def set_pin(self, name) -> Tuple:
        """Defines the CPW pins and returns the pin coordinates and normal direction vector

        Args:
            name: string (supported pin names are: start, end)

        Returns:
            tuple: `coordinate`, `direction`.
            The values are numpy arrays with two float points each.
        """
        if name == "start":
            options_pin = self.options.pin_inputs.start_pin
        elif name == "end":
            options_pin = self.options.pin_inputs.end_pin
        else:
            raise Exception("Pin name \"" + name + "\" is not supported for this CPW." +
                            " The only supported pins are: start, end." +
                            " to change that, edit set_pin(self, name)")

        pin = self.design.components[options_pin.component].pins[options_pin.pin]

        # add pins and document the connections in the netlist
        self.add_pin(name, pin.points[::-1], self.options.trace_width)
        self.design.connect_pins(
            self.design.components[options_pin.component].id, options_pin.pin, self.id, name)

        position = pin['middle']
        direction = pin['normal']
        return position, direction

    def get_unit_vectors(self, start: Oriented_Point, end: Oriented_Point, snap: bool = False) -> Tuple[np.ndarray]:
        """Return the unit and target vector in which the CPW should procees as its
        cooridnate sys.

        Arguments:
            start (Oriented_Point): [description]
            end (Oriented_Point): [description]
            snap (bool): True to snap to grid (Default: False)

        Returns:
            array: straight and 90 deg CCW rotated vecs 2D
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
        """Turns the CPW points into design elements, and add them to the design object

        Arguments:
            pts (np.ndarray): Array of points
        """
        p = self.p
        line = draw.LineString(pts)
        self.options._actual_length = str(line.length) + ' ' + self.design.get_units()
        self.add_qgeometry('path',
                           {'trace': line},
                           width=p.trace_width,
                           layer=p.layer)
        self.add_qgeometry('path',
                           {'cut': line},
                           width=p.trace_width + 2 * p.trace_gap,
                           layer=p.layer,
                           subtract=True)
