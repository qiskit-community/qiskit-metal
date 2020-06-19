"""
@author: Marco Facchini, John Blair, Zlatko Minev
"""

from collections import namedtuple
from typing import List, Tuple, Union

import numpy as np
from numpy.linalg import norm
from ...toolbox_python.utility_functions import log_error_easy

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


class Connector:  # Shouldn't this class be in the connector folder?
    r"""A simple class to define a connector as a 2D point
    with a 2D direction in the XY plane.
    All values stored as np.ndarray of parsed floats.

    Attributes:
        positon (np.ndarray of 2 points) -- Center position of the connector
        direction (np.ndarray of 2 points) -- *Normal vector* of the connector, defines which way it points outward.
                                              This is the normal vector to the surface on which the connector mates.
                                              Has unit norm.
    """
    # TODO: Maybe move this class out of here, more general.

    def __init__(self, position: np.ndarray, direction: np.ndarray):
        self.position = position
        self.direction = direction / norm(direction)

    def get_leadin(self, length: float) -> 'Connector':
        """A leadin in a straight line from a connector point,
        using with normal direction

        Args:
            length (float) : how much to lead in by
        """
        return Connector(self.position + self.direction*length, self.direction)

    def get_coordinate_vectors(self) -> Tuple[np.ndarray]:
        """Returns vectors that define the normal and tanget

        Returns:
            Tuple[np.ndarray] -- contains the parallel direction and the tangent. e.g.
                                tangent (np.ndarray of 2 points) -- unit vector parallel to
                                the connector face and a 90 deg CCW rotation from the direction units vector
        """
        return self.direction, draw.Vector.rotate(self.direction, np.pi/2)


class CpwMeanderSimple(QComponent):
    """A meandered basic CPW.

    **Behavior and parameters**
        #TODO: @john_blair / @marco
        Explain and comment on what options do?
        For example, note that lead_direction_inverted can be 'false' or 'true'
    """
    default_options = Dict(
        #start_name='',
        #end_name='',
        pin_start_name='',  # Name of pin used for pin_start
        pin_end_name='',  # Name of pin used for pin_end
        component_start_name='',  # If not connected, zero, otherwise component_id
        component_end_name='',  # If not connected, zero, otherwise component_id
        #pin_start=0,  # If not connected, zero, otherwise holds the net_id.
        #pin_end=0,  # If not connected, zero, otherwise holds the net_id.
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
        # TODO: Later, consider performance of instantiating all these Connector classes
        #TODO: Have the cpw make it's own pins at the start/end as well (see fake_cpw.py for guide)

        # parsed options
        p = self.p
        meander = self.parse_value(self.options.meander)  # type: Dict
        snap = is_true(meander.snap)
        total_length = p.total_length
        lead_start = meander.lead_start
        lead_end = meander.lead_end

        # Connector start and end
        start = self.get_start()
        end = self.get_end()

        # Lead in to meander
        startm = start.get_leadin(lead_start)
        endm = end.get_leadin(lead_end)
        self.startm = startm

        # Meander
        length_meander = total_length - (meander.lead_end + meander.lead_start)
        if snap:
            # handle y distance
            length_meander -= 0  # (end.position - endm.position)[1]

        meandered_pts = self.meander_fixed_length(
            startm, endm, length_meander, meander)

        # TODO: if lead_start is zero or end is , then dont add them
        self.x = [start.position, meandered_pts, end.position, startm]
        self.y = [
            start.position[None, :],
            meandered_pts,
            end.position[None, :]]
        points = np.concatenate([
            start.position[None, :],
            meandered_pts,
            endm.position[None, :],
            end.position[None, :]], axis=0)

        # Make points into elements
        self.make_elements(points)

    def meander_fixed_length(self, start: Connector, end: Connector,
                             length: float,
                             meander: dict) -> np.ndarray:
        """
        Meanders using a fixed length and fixed spacing.
        Adjusts the width of the meander
            * Includes the start but not the given end point
            * If it cannot meander just returns the initial start point

        Arguments:
            start {Connector} -- Connector of the start
            end {Connector} -- [description]
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

        # Coordinate system
        forward, sideways = self.get_unit_vectors(start, end, snap)
        if is_true(meander.lead_direction_inverted):
            sideways *= -1

        # Calculate lengths and menader number
        dist = start.position - end.position
        if snap:
            # TODO: Not general, depends on the outside (to fix)
            length_direct = abs(norm(np.dot(dist, forward)))
            # in the vertical direction
            length_excess = abs(norm(np.dot(dist, sideways)))
            # print(length_excess)
        else:
            length_direct = norm(dist)
            length_y = 0

        # Brekaup into sections
        meander_number = np.ceil(length_direct/spacing) - 1
        if meander_number < 1:
            self.logger.info(f'Zero meanders for {self.name}')
            return start.position

        # length of segmnet between two root points
        length_segment = (length - length_excess -
                          # the last little bit
                          (length_direct - meander_number*spacing)
                          - 2*asymmetry
                          ) / meander_number
        length_perp = (length_segment - spacing) / 2.  # perpendicular length

        # TODO: BUG fix when assymetry is large and negative
        if asymmetry < 0:
            if abs(asymmetry) > length_perp:
                print('Trouble')
                length_segment -= (abs(asymmetry) - length_perp)/2
                length_perp = (length_segment - spacing) / \
                    2.  # perpendicular length

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
        # qubit connector.
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

    def get_start(self) -> Connector:
        """Return the start point and normal direction vector

        Returns:
            A dictionary with keys `point` and `direction`.
            The values are numpy arrays with two float points each.
        """
        start_pin = self.design.components[self.options.component_start_name].pins[self.options.pin_start_name]
        
        if start_pin.net_id:
            print(
                f'Given pin {self.options.component_start_name} {self.options.pin_start_name} already in use. Component not created.')
            logger.warning(self.logger, post_text=f'\nERROR in building component "{self.name}"!'
                           'Inelligeable pin passed to function.\n')
            return


        return Connector(position=start_pin['middle'],
                         direction=start_pin['normal'])

    def get_end(self) -> Connector:
        """Return the start point and normal direction vector

        Returns:
            A dictionary with keys `point` and `direction`.
            The values are numpy arrays with two float points each.
        """
        end_pin = self.design.components[self.options.component_end_name].pins[self.options.pin_end_name]
        
        if end_pin.net_id:
            print(
                f'Given pin {self.options.component_end_name} {self.options.pin_end_name} already in use. Component not created.')
            logger.warning(self.logger, post_text=f'\nERROR in building component "{self.name}"!'
                           'Inelligeable pin passed to function.\n')
            return


        return Connector(position=end_pin['middle'],
                         direction=end_pin['normal'])

    def get_unit_vectors(self, start: Connector, end: Connector, snap: bool = False) -> Tuple[np.ndarray]:
        """Return the unit and tnaget vector in which the CPW should procees as its
        cooridnate sys.

        Arguments:
            start {Connector} -- [description]
            end {Connector} -- [description]

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
        self.options._actual_length = str(
            line.length) + ' ' + self.design.get_units()
        self.add_elements('path',
                          {'trace': line},
                          width=width,
                          layer=layer)
        self.add_elements('path',
                          {'cut': line},
                          width=width + p.trace_gap,
                          layer=layer,
                          subtract=True)
