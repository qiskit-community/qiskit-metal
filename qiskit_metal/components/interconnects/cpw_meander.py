"""
@author: Marco Facchini, John Blair, Zlatko Minev
"""

from collections import namedtuple
from typing import List, Tuple, Union

import numpy as np
from numpy.linalg import norm

import numpy as np
from qiskit_metal import draw, Dict, QComponent
from qiskit_metal import is_true

#from qiskit_metal.toolbox_metal.parsing import is_true
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
        self.directions = np.expand_dims((direction / norm(direction)), axis=0)

    def go_straigh(self, length: float):
        """Add a point ot 'lenght' distance in the same direction

        Args:
            length (float) : how much to move by
        """
        np.append(self.directions, [self.directions[-1]], axis=0)
        np.append(self.positions, [self.positions[-1] + self.directions[-1]*length], axis=0)

    def go_left(self, length: float):
        """Straight line 90deg counter-clock-wise direction w.r.t. Oriented_Point

        Args:
            length (float) : how much to move by
        """
        np.append(self.directions, [draw.Vector.rotate(self.direction, np.pi/2)], axis=0)
        np.append(self.positions, [self.positions[-1] + self.directions[-1]*length], axis=0)

    def go_right(self, length: float):
        """Straight line 90deg clock-wise direction w.r.t. Oriented_Point

        Args:
            length (float) : how much to move by
        """
        np.append(self.directions, [draw.Vector.rotate(self.direction, -1*np.pi/2)], axis=0)
        np.append(self.positions, [self.positions[-1] + self.directions[-1]*length], axis=0)

    def align_start_end(self, concurrent_array):
        """
        In this code, meanders need to face each-other to connect.
        Adjusts the orientation of the meander, adding yet a new point
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


    def __init__(self, array:Oriented_2D_Array):
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
        #p = self.parse_value(self.options)  # type: Dict
        p = self.p
        snap = is_true(p.meander.snap)
        total_length = p.total_length
        lead_start = p.meander.lead_start
        lead_end = p.meander.lead_end

        # Oriented_Point start and end
        start_points = Oriented_2D_Array(*self.get_start())
        end_points = Oriented_2D_Array(*self.get_end())

        # Lead in to meander
        start_points.go_straigh(lead_start)
        end_points.go_straigh(lead_end)
        #self.align_start_end(start_points, end_points)

        # Meander
        length_meander = total_length - (p.meander.lead_end + p.meander.lead_start)
        if snap:
            # handle y distance
            length_meander -= 0#(end.position - endm.position)[1]

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
            end_points.positions], axis=0)

#        points = np.concatenate([
#            start_points.positions[None, :],
#            meandered_pts,
#            end_points.positions[None, :]], axis=0)

        # Make points into elements
        self.make_elements(points)

    def meander_fixed_length(self, start_array: Oriented_2D_Array, end_array: Oriented_2D_Array,
                             length: float,
                             meander: dict) -> np.ndarray:
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
        spacing = meander.spacing  # Horizontal spacing between meanders
        asymmetry = meander.asymmetry
        snap = is_true(meander.snap)  # snap to xy grid
        # TODO: snap add 45 deg snap by chaning snap function using angles

        # TODO: remove adapter below, incorporate new class in the data
        start = Oriented_Point(start_array)
        end = Oriented_Point(end_array)

        # Coordinate system (example: x to the right => sideways up)
        forward, sideways = self.get_unit_vectors(start, end, snap)
        if is_true(meander.lead_direction_inverted):
            sideways *= -1

        # Calculate lengths and meander number
        dist = end.position - start.position
        if snap:
            # TODO: Not general, depends on the outside (to fix)
            length_direct = abs(norm(np.dot(dist,forward)))
            length_excess = abs(norm(np.dot(dist,sideways))) # in the vertical direction
        else:
            length_direct = norm(dist)
            length_excess = 0

        # Breakup into sections
        meander_number = np.ceil(length_direct/spacing) - 1
        if meander_number < 1:
            self.logger.info(f'Zero meanders for {self.name}')
            return start.position

        # length of segmnet between two root points
        length_segment = (length - length_excess -
                          (length_direct - meander_number*spacing) # the last little bit
                          - 2*asymmetry
                          ) / meander_number
        length_perp = (length_segment - spacing) / 2.  # perpendicular length

        # TODO: BUG fix when assymetry is large and negative
        if asymmetry < 0:
            if abs(asymmetry) > length_perp:
                print('Trouble')
                length_segment -= (abs(asymmetry) - length_perp)/2
                length_perp = (length_segment - spacing) / 2.  # perpendicular length

        # USES ROW Vectors
        # const vec. of unit normals
        middle_points = [forward]*int(meander_number+1)
        # index so to multipl other column - creates a comuln vector
        scale_bys = spacing*np.arange(int(meander_number+1))[:, None]
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
        root_pts = np.concatenate([middle_points,
                                   end.position[None, :]],  # convert to row vectors
                                  axis=0)
        side_shift_vecs = np.array([sideways*length_perp]*len(root_pts))
        asymmetry_vecs = np.array([sideways*asymmetry]*len(root_pts))
        top_pts = root_pts + side_shift_vecs + asymmetry_vecs
        bot_pts = root_pts - side_shift_vecs + asymmetry_vecs

        ################################################################
        # Combine points
        # Meanest part of the meander

        # Add 2 for the  for the lead and end points in the cpw from
        # root inluced in the top and bot count
        pts = np.zeros((len(top_pts)+len(bot_pts)-2, 2))
        idx, odd = self.get_indecies(root_pts)

        pts[0, :] = root_pts[0]
        # handle even odd, end can end on down or top
        ii = 1 + idx[: -2 if odd else -1]
        pts[ii, :] = top_pts[:len(ii)]
        ii = 2+ii[:-1]
        pts[ii, :] = bot_pts[1:1+len(ii)]
        pts[-1, :] = root_pts[-2]

        pts += start.position  # move to start position

        # add the snap point end - for example if the meander moves left to right
        # but the qubit is higher up in y, then we dont want an angled connection, but
        # need to add one more findal point to the meander, located below the leading in
        # qubit pin.
        if snap:
            meander_end = np.dot(end.position, forward)*forward +\
                np.dot(pts[-1], sideways)*sideways
            pts = np.vstack([pts, meander_end])

        self.pts = pts
        self.forward = forward
        self.sideways = sideways
        self.end = end.position
        return pts

    @staticmethod
    def get_indecies(root_pts: list):
        num_2pts, odd = divmod(len(root_pts), 2)
        if odd:
            num_2pts += 1

        #print(f'root_pts = {len(root_pts)}  num_2pts = {num_2pts}, odd={odd}')
        x = np.array(range(num_2pts), dtype=int)*4
        z = np.zeros(num_2pts*2, dtype=int)
        z[::2] = x
        z[1::2] = x+1
        return z, odd

    def get_start(self) -> List:
        """Return the start point and normal direction vector

        Returns:
            A dictionary with keys `point` and `direction`.
            The values are numpy arrays with two float points each.
        """
        pin = self.design.connectors[self.options.pin_start_name]
        position=pin['middle']
        direction=pin['normal']
        return position, direction

    def get_end(self) -> List:
        """Return the start point and normal direction vector

        Returns:
            A dictionary with keys `point` and `direction`.
            The values are numpy arrays with two float points each.
        """
        pin = self.design.connectors[self.options.pin_end_name]
        position=pin['middle']
        direction=pin['normal']
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
        direction = v/norm(v)
        if snap:
            direction = draw.Vector.snap_unit_vector(direction, flip=False)
        normal = draw.Vector.rotate(direction, np.pi/2)
        return direction, normal

    def make_elements(self, pts: np.ndarray):
        """Turns points into elements"""
        p = self.p
        line = draw.LineString(pts)
        layer = p.layer
        width = p.trace_width
        self.options._actual_length = str(line.length) + ' ' +self.design.get_units()
        self.add_elements('path',
                          {'trace': line},
                          width=width,
                          layer=layer)
        self.add_elements('path',
                          {'cut': line},
                          width=width + p.trace_gap,
                          layer=layer,
                          subtract=True)
