import numpy as np
from qiskit_metal.draw.utility import vec_unit_planar
from qiskit_metal import draw, QComponent
from numpy.linalg import norm
from typing import List, Tuple, Union


class Qroute:
    r"""A simple class to define a generic route, using an array of planar points (x,y coordinates)
    and the direction of the pins that start and end the array
    Values stored as np.ndarray of parsed floats or np.array float pair
    """

    def __init__(self, pin_start, pin_end=None):
        """
        Arguments:
            pin_start (pin object): reference to the connecting pin
            pin_end (pin object): reference to the connecting pin

        
        """
        self.points = np.expand_dims(pin_start.position, axis=0)
        self.pin_start = pin_start
        self.pin_end = pin_end
        
        # head_direction (2x1 np.ndarray - 1 vector): *Normal vector* defining which way the head
        # is pointing.  This is the normal vector to the surface of the head line-end.
        self.head_direction = vec_unit_planar(pin_start.direction)

    def get_start(self) -> Tuple:
        """Return the start point and normal direction vector

        Returns:
            Tuple: Initializes the Qroute start point and and returns `position` and `direction`.
            The values are numpy arrays with two float points each.
        """
        pin = self.design.connectors[self.options.pin_start_name]
        position = pin['middle']
        direction = pin['normal']
        return position, direction

    def go_straight(self, length: float):
        """Add a point ot 'length' distance in the same direction

        Args:
            length (float) : how much to move by
        """
        self.points = np.append(self.points, [self.points[-1] + self.head_direction * length], axis=0)

    def go_left(self, length: float):
        # THIS METHOD IS NOT USED AT THIS TIME (7/2/20). PLAN TO USE
        """Straight line 90deg counter-clock-wise direction w.r.t. Oriented_Point

        Args:
            length (float): how much to move by
        """
        self.head_direction = draw.Vector.rotate(self.head_direction, np.pi / 2)
        self.points = np.append(self.points, [self.points[-1] + self.head_direction * length], axis=0)

    def go_right(self, length: float):
        # THIS METHOD IS NOT USED AT THIS TIME (7/2/20). PLAN TO USE
        """Straight line 90deg clock-wise direction w.r.t. Oriented_Point

        Args:
            length (float): how much to move by
        """
        self.head_direction = draw.Vector.rotate(self.head_direction, -1 * np.pi / 2)
        self.points = np.append(self.points, [self.points[-1] + self.head_direction * length], axis=0)

    @property
    def length(self):
        """Sum of all segments length, including the head

        Return:
            length (float): full point_array length
        """
        length = 0
        for x in range(len(self.points)-1):
            length += abs(norm(self.points[x] - self.points[x+1]))
        if self.pin_end is None:
            return length
        else:
            return length + abs(norm(self.points[x] - self.pin_end.position))

    def route_to_align(self, concurrent_array):
        # THIS METHOD IS NOT USED AT THIS TIME (7/2/20). RE_EVALUATE BASED ON NEED.
        """
        In this code, meanders are aligned to face each-other. So they are easier to connect.


        TODO: Make sure the two points align on one of the axes, by adding a new point

        TODO: Adjusts the orientation of the meander, adding yet a new point:
            * Includes the start but not the given end point
            * If it cannot meander just returns the initial start point

        Arguments:
            concurrent_array {Oriented_2D_Array}: Other end of the CPW
        """
        print(self.points[-1])
        print(concurrent_array.positions[-1])

        # determine relative position
        concurrent_position = ""
        oriented_distance = concurrent_array.positions[-1] - self.points[-1]
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

        if np.dot(self.head_direction, concurrent_array.directions[-1]) == -1:
            # points are facing each other or opposing each other
            if (("E" in concurrent_position and self.head_direction[0] > 0)
                    or ("N" in concurrent_position and self.head_direction[1] > 0)):
                # facing each other
                pass
            else:
                # opposing each other
                pass
        elif np.dot(self.head_direction, concurrent_array.directions[-1]) == 1:
            # points are facing the same direction
            if (("E" in concurrent_position and self.head_direction[0] > 0)
                    or ("N" in concurrent_position and self.head_direction[1] > 0)):
                # facing each other
                pass
            else:
                # opposing each other
                pass
        else:
            # points are orthogonal to ach other
            pass
