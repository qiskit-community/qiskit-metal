# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


"""
@author: Marco Facchini
@date: 2020/08/06
"""
import numpy as np
from qiskit_metal import draw, Dict
from .base import QComponent
from numpy.linalg import norm
from typing import List, Tuple, Union, AnyStr


class QRoutePoint:
    """A convenience wrapper class to define an point with orientation,
    with a 2D position and a 2D direction (XY plane).
    All values stored as np.ndarray of parsed floats.
    """

    def __init__(self, position: np.array, direction: np.array = None):
        """
        Arguments:
            position (np.ndarray of 2 points): Center point of the pin
            direction (np.ndarray of 2 points): (default: None) *Normal vector*
                This is the normal vector to the surface on which the pin mates.
                Defines which way it points outward. Has unit norm.
        """
        self.position = position
        self.direction = direction


class QRoute(QComponent):
    """
    The super-class `QRoute`

    Inherits `QComponent` class

    Description:
        Super-class implementing routing methods that are valid irrespective of
        the number of pins (>=1). The route is stored in a n array of planar points
        (x,y coordinates) and one direction, which is that of the last point in the array
        Values are stored as np.ndarray of parsed floats or np.array float pair

    Options:

    Pins:
        * start_pin       - component and pin string pair. Define which pin to start from
        * end_pin         - (optional) component and pin string pair. Define which pin to end at

    Leads:
        * start_straight  - lead-in, defined as the straight segment extension from start_pin (default: 0.1um)
        * end_straight    - (optional) lead-out, defined as the straight segment extension from end_pin (default: 0.1um)

    Others:
        * snap            - true/false, defines if snapping on Manhattan routing or any direction (default: 'true')
        * total_length    - target length of the overall route (default: '7mm')
        * chip            - which chip is this component attached to (default: 'main')
        * layer           - which layer this component should be rendered on (default: '1')
        * trace_width     - defines the width of the line (default: 'cpw_width')
        * trace_gap       - (only exists for type="CPW") defines the gap between the route wire
                            and the ground plane (default: 'cpw_gap')

    """

    component_metadata = Dict(
        short_name='route'
        )
    """Component metadata"""

    default_options = Dict(
        pin_inputs=Dict(
            start_pin=Dict(  # QRoute also supports single pin routes
                component='',  # Name of component to start from, which has a pin
                pin=''),  # Name of pin used for pin_start
            end_pin=Dict(
                component='',  # Name of component to end on, which has a pin
                pin='')  # Name of pin used for pin_end
        ),
        fillet='0',
        lead=Dict(
            start_straight='0.1mm',
            end_straight='0.1mm'
        ),
        total_length='7mm',
        chip='main',
        layer='1',
        trace_width='cpw_width'
    )
    """Default options"""

    def __init__(self, design, name=None, options=None, type: str = "CPW", **kwargs):
        """Initializes all Routes

        Calls the QComponent __init__() to create a new Metal component
        Before that, it adds the variables that are needed to support routing

        Arguments:
            type (string): Supports Route (single layer trace) and CPW (adds the gap around it) (default: "CPW")

        Attributes:
            head (QRouteLead()): Stores sequential points to start the route
            tail (QRouteLead()): (optional) Stores sequential points to terminate the route
            intermediate_pts (numpy Nx2): Sequence of points between and other than head and tail (default:None)
            start_pin_name (string): Head pin name (default: "start")
            end_pin_name (string): Tail pin name (default: "end")
        """
        self.head = QRouteLead()
        self.tail = QRouteLead()

        # keep track of all points so far in the route from both ends
        self.intermediate_pts = None  # will be numpy Nx2

        # supported pin names (constants)
        self.start_pin_name = "start"
        self.end_pin_name = "end"

        self.type = type.upper().strip()

        # # add default_options that are QRoute type specific:
        options = self._add_route_specific_options(options)

        # regular QComponent boot, including the run of make()
        super().__init__(design, name, options, **kwargs)

    def _add_route_specific_options(self, options):
        """Enriches the default_options to support different types of route styles

        Args:
            options (dict): User options that will override the defaults

        Return:
            a modified options dictionary
        """
        if self.type == "ROUTE":
            # all the defaults are fine as-is
            None
        elif self.type == "CPW":
            # add the variable to define the space between the route and the ground plane
            cpw_options = Dict(trace_gap='cpw_gap')
            if options:
                if "trace_gap" not in options:
                    # user did not pass the trace_gap, so add it
                    options.update(cpw_options)
            else:
                # user did not pass custom options, so create it to add trace_gap
                options["options"] = cpw_options
        else:
            raise Exception("Unsupported Route type: " + self.type +
                            " The only supported types are CPW and route")

        return options

    def _get_connected_pin(self, pin_data: Dict):
        """Recovers a pin from the dictionary

        Args:
            pin_data: dict {component: string, pin: string}

        Return:
            the actual pin object.
        """
        return self.design.components[pin_data.component].pins[pin_data.pin]

    def set_pin(self, name: str) -> QRoutePoint:
        """Defines the CPW pins and returns the pin coordinates and normal direction vector

        Args:
            name: string (supported pin names are: start, end)

        Return:
            QRoutePoint: last point (for now the single point) in the QRouteLead
        """
        # First define which pin/lead you intend to initialize
        if name == self.start_pin_name:
            options_pin = self.options.pin_inputs.start_pin
            lead = self.head
        elif name == self.end_pin_name:
            options_pin = self.options.pin_inputs.end_pin
            lead = self.tail
        else:
            raise Exception("Pin name \"" + name + "\" is not supported for this CPW." +
                            " The only supported pins are: start, end.")

        # grab the reference component pin
        reference_pin = self._get_connected_pin(options_pin)

        # create the cpw pin and document the connections to the reference_pin in the netlist
        self.add_pin(name, reference_pin.points[::-1], self.p.trace_width)
        self.design.connect_pins(
            self.design.components[options_pin.component].id, options_pin.pin, self.id, name)

        # anchor the correct lead to the pin and return its position and direction
        return lead.seed_from_pin(reference_pin)

    def set_lead(self, name: str) -> QRoutePoint:
        """Defines the lead_extension by adding a point to the self.head/tail

        Args:
            name: string (supported pin names are: start, end)

        Return:
            QRoutePoint: last point in the QRouteLead (self.head/tail)
        """
        # TODO: jira case #300 should remove the need for this line, and only use self.p
        p = self.parse_options()

        # First define which lead you intend to modify
        if name == self.start_pin_name:
            options_lead = p.lead.start_straight
            lead = self.head
        elif name == self.end_pin_name:
            options_lead = p.lead.end_straight
            lead = self.tail
        else:
            raise Exception("Pin name \"" + name + "\" is not supported for this CPW." +
                            " The only supported pins are: start, end.")

        # then change the lead by adding a point in the same direction of the seed pin
        # minimum lead, to be able to jog correctly
        lead_length = max(options_lead, self.p.trace_width / 2.0)
        lead.go_straight(lead_length)

        # return the last QRoutePoint of the lead
        return lead.get_tip()

    def get_tip(self) -> QRoutePoint:
        """Access the last element in the QRouteLead

        Return:
            QRoutePoint: last point in the QRouteLead
            The values are numpy arrays with two float points each.
        """
        if not self.intermediate_pts:
            return self.head.get_tip()
        elif len(self.intermediate_pts) == 1:
            return QRoutePoint(self.intermediate_pts[-1],
                               self.intermediate_pts[-1] - self.head.get_tip().position)
        else:
            return QRoutePoint(self.intermediate_pts[-1],
                               self.intermediate_pts[-1] - self.intermediate_pts[-2])

    def get_points(self) -> np.ndarray:
        """Assembles the list of points for the route by concatenating:
        head_pts + intermediate_pts, tail_pts

        Returns:
            np.ndarray: ((H+N+T)x2) all points (x,y) of the CPW
        """
        # cover case where there is no intermediate points (straight connection between lead ends)
        if self.intermediate_pts is None:
            beginning = self.head.pts
        else:
            beginning = np.concatenate([
                self.head.pts,
                self.intermediate_pts], axis=0)

        # cover case where there is no tail defined (floating end)
        if self.tail is None:
            return beginning
        return np.concatenate([
            beginning,
            self.tail.pts[::-1]], axis=0)

    def get_unit_vectors(self, start: QRoutePoint, end: QRoutePoint, snap: bool = False) -> Tuple:
        """Return the unit and target vector in which the CPW should process as its
        coordinate sys.

        Arguments:
            start (QRoutePoint): [description]
            end (QRoutePoint): [description]
            snap (bool): True to snap to grid (default: False)

        Returns:
            array: straight and 90 deg CCW rotated vecs 2D
            (array([1., 0.]), array([0., 1.]))
        """
        # handle chase when start and end are same?
        v = end.position - start.position
        direction = v / norm(v)
        if snap:
            direction = draw.Vector.snap_unit_vector(direction, flip=False)
        normal = draw.Vector.rotate(direction, np.pi / 2)
        return direction, normal

    @property
    def length(self):
        """Sum of all segments length, including the head

        Return:
            length (float): full point_array length
        """
        points = self.get_points()
        return sum(norm(points[i + 1] - points[i]) for i in range(len(points) - 1))

    def make_elements(self, pts: np.ndarray):
        """Turns the CPW points into design elements, and add them to the design object

        Arguments:
            pts (np.ndarray): Array of points
        """
        p = self.p
        # prepare the routing track
        line = draw.LineString(pts)
        # TODO: show up the actual length, which is now different from the initial length
        self.options._actual_length = str(line.length) + ' ' + self.design.get_units()
        # expand the routing track to form the substrate core of the cpw
        self.add_qgeometry('path',
                           {'trace': line},
                           width=p.trace_width,
                           fillet=p.fillet,
                           layer=p.layer)
        if self.type == "CPW":
            # expand the routing track to form the two gaps in the substrate
            # final gap will be form by this minus the trace above
            self.add_qgeometry('path',
                               {'cut': line},
                               width=p.trace_width + 2 * p.trace_gap,
                               fillet=p.fillet,
                               layer=p.layer,
                               subtract=True)

    # def route_to_align(self, concurrent_array):
    #     """
    #     THIS METHOD IS OUTDATED AND THUS NOT FUNCTIONING
    #
    #     TODO: Develop code to make sure the tip of the leads align on one of the axes
    #     """
    #     print(self.points[-1])
    #     print(concurrent_array.positions[-1])
    #
    #     # determine relative position
    #     concurrent_position = ""
    #     oriented_distance = concurrent_array.positions[-1] - self.points[-1]
    #     if oriented_distance[1] != 0: # vertical displacement
    #         concurrent_position += ["N", "S"][oriented_distance[1] < 0]
    #     if oriented_distance[0] != 0: # horizontal displacement
    #         concurrent_position += ["E", "W"][oriented_distance[0] < 0]
    #     else:
    #         return # points already aligned
    #
    #     # TODO implement vertical alignment. Only using horizontal alignment for now
    #     # if oriented_distance[0] > oriented_distance[1]:
    #     #     # Vertical alignment
    #     #     pass
    #     # else:
    #     #     # horizontal alignment
    #     #     pass # code below
    #
    #     if np.dot(self.head_direction, concurrent_array.directions[-1]) == -1:
    #         # points are facing each other or opposing each other
    #         if (("E" in concurrent_position and self.head_direction[0] > 0)
    #                 or ("N" in concurrent_position and self.head_direction[1] > 0)):
    #             # facing each other
    #             pass
    #         else:
    #             # opposing each other
    #             pass
    #     elif np.dot(self.head_direction, concurrent_array.directions[-1]) == 1:
    #         # points are facing the same direction
    #         if (("E" in concurrent_position and self.head_direction[0] > 0)
    #                 or ("N" in concurrent_position and self.head_direction[1] > 0)):
    #             # facing each other
    #             pass
    #         else:
    #             # opposing each other
    #             pass
    #     else:
    #         # points are orthogonal to ach other
    #         pass


class QRouteLead:
    """A simple class to define a an array of points with some properties,
    defines 2D positions and some of the 2D directions (XY plane).
    All values stored as np.ndarray of parsed floats.
    """

    def __init__(self, *args, **kwargs):
        """QRouteLead is a simple sequence of points

        Used to accurately control one of the QRoute termination points
        Before that, it adds the variables that are needed to support routing

        Attributes:
            pts (numpy Nx2): Sequence of points (default: None)
            direction (numpy 2x1): Normal from the last point of the array (default: None)
        """
        # keep track of all points so far in the route from both ends
        self.pts = None  # will be numpy Nx2
        # keep track of the direction of the tip of the lead (last point)
        self.direction = None  # will be numpy 2x1

    def seed_from_pin(self, pin: Dict) -> QRoutePoint:
        """Initialize the QRouteLead by giving it a starting point and a direction

        Args:
            pin: object describing the "reference_pin" (not cpw_pin) this is attached to.
                this is currently (8/4/2020) a dictionary

        Return:
            QRoutePoint: last point (for now the single point) in the QRouteLead
            The values are numpy arrays with two float points each.
        """
        # TODO: widely repeated code. Transform pin into class and add method
        #  pin.get_locale()->position,direction, to execute below.
        position = pin['middle']
        direction = pin['normal']

        self.direction = direction
        self.pts = np.array([position])

        return QRoutePoint(position, direction)

    def go_straight(self, length: float):
        """Add a point ot 'length' distance in the same direction

        Args:
            length (float) : how much to move by
        """
        self.pts = np.append(
            self.pts, [self.pts[-1] + self.direction * length], axis=0)

    def go_left(self, length: float):
        """Straight line 90deg counter-clock-wise direction w.r.t. lead tip direction

        Args:
            length (float): how much to move by
        """
        self.direction = draw.Vector.rotate(self.direction, np.pi / 2)
        self.pts = np.append(
            self.pts, [self.pts[-1] + self.direction * length], axis=0)

    def go_right(self, length: float):
        """Straight line 90deg clock-wise direction w.r.t. lead tip direction

        Args:
            length (float): how much to move by
        """
        self.direction = draw.Vector.rotate(self.direction, -1 * np.pi / 2)
        self.pts = np.append(
            self.pts, [self.pts[-1] + self.direction * length], axis=0)

    @property
    def length(self):
        """Sum of all segments length, including the head

        Return:
            length (float): full point_array length
        """
        return sum(norm(self.pts[i + 1] - self.pts[i]) for i in range(len(self.pts) - 1))

    def get_tip(self) -> QRoutePoint:
        """Access the last element in the QRouteLead

        Return:
            QRoutePoint: last point in the QRouteLead
            The values are numpy arrays with two float points each.
        """
        return QRoutePoint(self.pts[-1], self.direction)

    # def align_to(self, concurrent_array):
    #     """
    #     THIS METHOD IS OUTDATED AND THUS NOT FUNCTIONING
    #
    #     TODO: Develop code to make sure the tip of the leads align on one of the axes
    #     """
    #
    #     # determine relative position
    #     concurrent_position = ""
    #     oriented_distance = concurrent_array.positions[-1] - self.positions[-1]
    #     if oriented_distance[1] > 0:
    #         concurrent_position = "N"
    #     elif oriented_distance[1] < 0:
    #         concurrent_position = "S"
    #     else:
    #         return  # points already aligned
    #     if oriented_distance[0] > 0:
    #         concurrent_position += "E"
    #     elif oriented_distance[1] < 0:
    #         concurrent_position += "W"
    #     else:
    #         return  # points already aligned
    #
    #     # TODO implement vertical alignment. Only using horizontal alignment for now
    #     # if oriented_distance[0] > oriented_distance[1]:
    #     #     # Vertical alignment
    #     #     pass
    #     # else:
    #     #     # horizontal alignment
    #     #     pass # code below
    #
    #     if np.dot(self.directions[-1], concurrent_array.directions[-1]) == -1:
    #         # points are facing each other or opposing each other
    #         if (("E" in concurrent_position and self.directions[-1][0] > 0)
    #                 or ("N" in concurrent_position and self.directions[-1][1] > 0)):
    #             # facing each other
    #             pass
    #         else:
    #             # opposing each other
    #             pass
    #     elif np.dot(self.directions[-1], concurrent_array.directions[-1]) == 1:
    #         # points are facing the same direction
    #         if (("E" in concurrent_position and self.directions[-1][0] > 0)
    #                 or ("N" in concurrent_position and self.directions[-1][1] > 0)):
    #             # facing each other
    #             pass
    #         else:
    #             # opposing each other
    #             pass
    #     else:
    #         # points are orthogonal to ach other
    #         pass
