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
from qiskit_metal import draw, Dict
from .base import QComponent
from numpy.linalg import norm
from typing import List, Tuple, Union, AnyStr
from collections.abc import Mapping
from qiskit_metal.toolbox_metal import math_and_overrides as mao
import math
import re


class QRoutePoint:
    """A convenience wrapper class to define an point with orientation, with a
    2D position and a 2D direction (XY plane).

    All values stored as np.ndarray of parsed floats.
    """

    def __init__(self, position: np.array, direction: np.array = None):
        """
        Args:
            position (np.ndarray of 2 points): Center point of the pin.
            direction (np.ndarray of 2 points): *Normal vector*
                This is the normal vector to the surface on which the pin mates.
                Defines which way it points outward. Has unit norm.  Defaults to None.
        """
        self.position = position
        if isinstance(position, list):
            if len(position[-1]) == 2:
                self.position = position[-1]
        self.direction = direction

    def __str__(self):
        return "position: " + str(self.position) + " : direction:" + str(
            self.direction) + "."


class QRoute(QComponent):
    """Super-class implementing routing methods that are valid irrespective of
    the number of pins (>=1). The route is stored in a n array of planar points
    (x,y coordinates) and one direction, which is that of the last point in the
    array. Values are stored as np.ndarray of parsed floats or np.array float
    pair.

    Inherits `QComponent` class

    Default Options:
        * pin_inputs: Dict
            * start_pin: Dict -- Component and pin string pair. Define which pin to start from
                * component: '' -- Name of component to start from, which has a pin
                * pin: '' -- Name of pin used for pin_start
            * end_pin=Dict -- Component and pin string pair. Define which pin to start from
                * component: '' -- Name of component to end on, which has a pin
                * pin: '' -- Name of pin used for pin_end
        * lead: Dict
            * start_straight: '0mm' -- Lead-in, defined as the straight segment extension from start_pin.  Defaults to 0.1um.
            * end_straight: '0mm' -- Lead-out, defined as the straight segment extension from end_pin.  Defaults to 0.1um.
            * start_jogged_extension: '' -- Lead-in, jogged extension of lead-in. Described as list of tuples
            * end_jogged_extension: '' -- Lead-out, jogged extension of lead-out. Described as list of tuples
        * fillet: '0'
        * total_length: '7mm'
        * trace_width: 'cpw_width' -- Defines the width of the line.  Defaults to 'cpw_width'.

    How to specify \*_jogged_extensions for the QRouteLeads:
        \*_jogged_extensions have to be specified in an OrderedDict with incremental keys.
        the value of each key specifies the direction of the jog and the extension past the jog.
        For example:

        .. code-block:: python
            :linenos:

            jogs = OrderedDict()
            jogs[0] = ["R", '200um']
            jogs[1] = ["R", '200um']
            jogs[2] = ["L", '200um']
            jogs[3] = ["L", '500um']
            jogs[4] = ["R", '200um']
            jogs_other = ....
            
            options = {'lead': {
                'start_straight': '0.3mm',
                'end_straight': '0.3mm',
                'start_jogged_extension': jogs,
                'end_jogged_extension': jogs_other
            }}

        The jog direction can be specified in several ways. Feel free to pick the one more
        convenient for your coding style:

        >> "L", "L#", "R", "R#", #, "#", "A,#", "left", "left#", "right", "right#"

        where # is any signed or unsigned integer or floating point value.
        For example the following will all lead to the same turn:

        >> "L", "L90", "R-90", 90, "90", "A,90", "left", "left90", "right-90"
    """

    component_metadata = Dict(short_name='route', _qgeometry_table_path='True')
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
        lead=Dict(start_straight='0mm',
                  end_straight='0mm',
                  start_jogged_extension='',
                  end_jogged_extension=''),
        total_length='7mm',
        trace_width='cpw_width')
    """Default options"""

    TOOLTIP = """QRoute"""

    def __init__(self,
                 design,
                 name: str = None,
                 options: Dict = None,
                 type: str = "CPW",
                 **kwargs):
        """Initializes all Routes.

        Calls the QComponent __init__() to create a new Metal component.
        Before that, it adds the variables that are needed to support routing.

        Args:
            design (QDesign): The parent design.
            name (str): Name of the component. Auto-named if possible.
            options (dict): User options that will override the defaults.  Defaults to None.
            type (string): Supports Route (single layer trace) and CPW (adds the gap around it).
                Defaults to "CPW".
        """
        # Class key Attributes:
        #     * head (QRouteLead()): Stores sequential points to start the route.
        #     * tail (QRouteLead()): (optional) Stores sequential points to terminate the route.
        #     * intermediate_pts: (list or numpy Nx2 or dict) Sequence of points between and other
        #         than head and tail.  Defaults to None. Type could be either list or numpy Nx2,
        #         or dict/OrderedDict nesting lists or numpy Nx2.
        #     * start_pin_name (string): Head pin name.  Defaults to "start".
        #     * end_pin_name (string): Tail pin name.  Defaults to "end".

        self.head = QRouteLead()
        self.tail = QRouteLead()

        # keep track of all points so far in the route from both ends
        self.intermediate_pts = np.empty((0, 2), float)  # will be numpy Nx2

        # supported pin names (constants)
        self.start_pin_name = "start"
        self.end_pin_name = "end"

        self.type = type.upper().strip()

        # # add default_options that are QRoute type specific:
        options = self._add_route_specific_options(options)

        # regular QComponent boot, including the run of make()
        super().__init__(design, name, options, **kwargs)

    def _add_route_specific_options(self, options):
        """Enriches the default_options to support different types of route
        styles.

        Args:
            options (dict): User options that will override the defaults

        Return:
            A modified options dictionary

        Raises:
            Exception: Unsupported route type
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
        """Recovers a pin from the dictionary.

        Args:
            pin_data: dict {component: string, pin: string}

        Return:
            The actual pin object.
        """
        return self.design.components[pin_data.component].pins[pin_data.pin]

    def set_pin(self, name: str) -> QRoutePoint:
        """Defines the CPW pins and returns the pin coordinates and normal
        direction vector.

        Args:
            name: String (supported pin names are: start, end)

        Return:
            QRoutePoint: Last point (for now the single point) in the QRouteLead

        Raises:
            Exception: Ping name is not supported
        """
        # First define which pin/lead you intend to initialize
        if name == self.start_pin_name:
            options_pin = self.options.pin_inputs.start_pin
            lead = self.head
        elif name == self.end_pin_name:
            options_pin = self.options.pin_inputs.end_pin
            lead = self.tail
        else:
            raise Exception("Pin name \"" + name +
                            "\" is not supported for this CPW." +
                            " The only supported pins are: start, end.")

        # grab the reference component pin
        reference_pin = self._get_connected_pin(options_pin)

        # create the cpw pin and document the connections to the reference_pin in the netlist
        self.add_pin(name, reference_pin.points[::-1], self.p.trace_width)
        self.design.connect_pins(
            self.design.components[options_pin.component].id, options_pin.pin,
            self.id, name)

        # anchor the correct lead to the pin and return its position and direction
        return lead.seed_from_pin(reference_pin)

    def set_lead(self, name: str) -> QRoutePoint:
        """Defines the lead_extension by adding a point to the self.head/tail.

        Args:
            name: String (supported pin names are: start, end)

        Return:
            QRoutePoint: Last point in the QRouteLead (self.head/tail)

        Raises:
            Exception: Ping name is not supported
        """
        p = self.parse_options()

        # First define which lead you intend to modify
        if name == self.start_pin_name:
            options_lead = p.lead.start_straight
            lead = self.head
            jogged_lead = self.p.lead.start_jogged_extension
        elif name == self.end_pin_name:
            options_lead = p.lead.end_straight
            lead = self.tail
            jogged_lead = self.p.lead.end_jogged_extension
        else:
            raise Exception("Pin name \"" + name +
                            "\" is not supported for this CPW." +
                            " The only supported pins are: start, end.")

        # then change the lead by adding a point in the same direction of the seed pin
        # minimum lead, to be able to jog correctly
        lead_length = max(options_lead, self.p.trace_width / 2.0)
        lead.go_straight(lead_length)
        # then add all the jogged lead information
        if jogged_lead:
            self.set_lead_extension(name)  # consider merging with set_lead

        # return the last QRoutePoint of the lead
        return lead.get_tip()

    def set_lead_extension(self, name: str) -> QRoutePoint:
        """Defines the jogged lead_extension by adding a series of turns to the
        self.head/tail.

        Args:
            name: String (supported pin names are: start, end)

        Return:
            QRoutePoint: Last point in the QRouteLead (self.head/tail)

        Raises:
            Exception: Ping name is not supported
            Exception: Dictionary error
        """
        p = self.parse_options()
        # First define which lead you intend to modify
        if name == self.start_pin_name:
            options_lead = p.lead.start_jogged_extension
            lead = self.head
        elif name == self.end_pin_name:
            options_lead = p.lead.end_jogged_extension
            lead = self.tail
        else:
            raise Exception("Pin name \"" + name +
                            "\" is not supported for this CPW." +
                            " The only supported pins are: start, end.")

        # then change the lead by adding points
        for turn, length in options_lead.values():
            if isinstance(turn, (float, int)):
                # turn is a number indicating the angle
                lead.go_angle(length, turn)
            elif re.search(r'^[-+]?(\d+\.\d+|\d+)$', turn):
                # turn is a string of a number indicating the angle
                lead.go_angle(length, float(turn))
            elif turn in ("left", "L"):
                # implicit turn -90 degrees
                lead.go_left(length)
            elif turn in ("right", "R"):
                # implicit turn 90 degrees
                lead.go_right(length)
            elif turn in ("straight", "D", "S"):
                # implicit 0 degrees movement
                lead.go_straight(length)
            elif re.search(r'^(left|L)[-+]?(\d+\.\d+|\d+)$', turn):
                # left turn by the specified int/float degrees. can be signed
                angle = re.sub(r'^(left|L)', "", turn)
                lead.go_angle(length, float(angle))
            elif re.search(r'^(right|R)[-+]?(\d+\.\d+|\d+)$', turn):
                # right turn by the specified int/float degrees. can be signed
                angle = re.sub(r'^(right|R)', "", turn)
                lead.go_angle(length, -1 * float(angle))
            elif ('A' or 'angle') in turn:
                # turn by the specified int/float degrees. Positive numbers turn left.
                turn, angle = turn.split(',')
                lead.go_angle(length, float(angle))
            else:
                raise Exception(
                    f"\nThe input string {turn} is not supported. Please specify the jog turn "
                    "using one of the supported formats:\n\"L\", \"L#\", \"R\", \"R#\", #, "
                    "\"#\", \"A,#\", \"left\", \"left#\", \"right\", \"right#\""
                    "\nwhere # is any signed or unsigned integer or floating point value.\n"
                    "For example the following will all lead to the same turn:\n"
                    "\"L\", \"L90\", \"R-90\", 90, "
                    "\"90\", \"A,90\", \"left\", \"left90\", \"right-90\"")

        # return the last QRoutePoint of the lead
        return lead.get_tip()

    def _get_lead2pts_array(self, arr) -> Tuple:
        """Return the last "diff pts" of the array. If the array is one
        dimensional or has only identical points, return -1 for tip_pt_minus_1.

        Return:
            Tuple: Of two np.ndarray. the arrays could be -1 instead, if point not found
        """
        pt = pt_minus_1 = None
        if len(arr) == 1:
            pt = arr[0]
        elif len(arr) > 1:
            if not isinstance(arr, np.ndarray) and len(arr) == 2 and len(
                    arr[0]) == 1:
                # array 2,1
                pt = arr
            else:
                # array N,2
                pt = arr[-1]
                prev_id = -2
                pt_minus_1 = arr[prev_id]
                while (pt_minus_1 == pt).all() and prev_id > -len(arr):
                    prev_id -= 1
                    pt_minus_1 = arr[prev_id]
                if (pt_minus_1 == pt).all():
                    pt_minus_1 = None
        return pt, pt_minus_1

    def get_tip(self) -> QRoutePoint:
        """Access the last element in the QRouteLead.

        Return:
            QRoutePoint: Last point in the QRouteLead
            The values are numpy arrays with two float points each.
        """
        if self.intermediate_pts is None:
            # no points in between, so just grab the last point from the lead-in
            return self.head.get_tip()
        tip_pt = tip_pt_minus_1 = None
        if isinstance(self.intermediate_pts, list) or isinstance(
                self.intermediate_pts, np.ndarray):
            tip_pt, tip_pt_minus_1 = self._get_lead2pts_array(
                self.intermediate_pts)
        elif isinstance(self.intermediate_pts, Mapping):
            # then it is either a dict or a OrderedDict
            # this method relies on the keys to be numerical integer. Will use the last points
            # assumes that the "value" associated with each key is some "not empty" list/array
            sorted_keys = sorted(self.intermediate_pts.keys(), reverse=True)
            for key in sorted_keys:
                pt0, pt_minus1 = self._get_lead2pts_array(
                    self.intermediate_pts[key])
                if pt0 is None:
                    continue
                if tip_pt_minus_1 is None:
                    tip_pt_minus_1 = pt0
                if tip_pt is None:
                    tip_pt, tip_pt_minus_1 = tip_pt_minus_1, tip_pt
                    tip_pt_minus_1 = pt_minus1
        else:
            print("unsupported type for self.intermediate_pts",
                  type(self.intermediate_pts))
            return
        if tip_pt is None:
            # no point in the intermediate array
            return self.head.get_tip()
        if tip_pt_minus_1 is None:
            # no "previous" point in the intermediate array
            tip_pt_minus_1 = self.head.get_tip().position

        return QRoutePoint(tip_pt, tip_pt - tip_pt_minus_1)

    def del_colinear_points(self, inarray):
        """Delete colinear points from the given array.

        Args:
            inarray (list): List of points

        Returns:
            list: List of points without colinear points
        """
        if len(inarray) <= 1:
            return
        else:
            outarray = list()  #outarray = np.empty(shape=[0, 2])
            pts = [None, None, inarray[0]]
            for idxnext in range(1, len(inarray)):
                pts = pts[1:] + [inarray[idxnext]]
                # delete identical points
                if np.allclose(*pts[1:]):
                    pts = [None] + pts[0:2]
                    continue
                # compare points once you have 3 unique points in pts
                if pts[0] is not None:
                    # if all(mao.round(i[1]) == mao.round(pts[0][1]) for i in pts) \
                    #         or all(mao.round(i[0]) == mao.round(pts[0][0]) for i in pts):
                    if mao.aligned_pts(pts):
                        pts = [None] + [pts[0]] + [pts[2]]
                # save a point once you successfully establish the three are not aligned,
                #  and before it gets dropped in the next loop cycle
                if pts[0] is not None:
                    outarray.append(pts[0])
            # save the remainder non-aligned points
            if pts[1] is not None:
                outarray.extend(pts[1:])
            else:
                outarray.append(pts[2])
            return np.array(outarray)

    def get_points(self) -> np.ndarray:
        """Assembles the list of points for the route by concatenating:
        head_pts + intermediate_pts, tail_pts.

        Returns:
            np.ndarray: ((H+N+T)x2) all points (x,y) of the CPW
        """
        # cover case where there is no intermediate points (straight connection between lead ends)
        if self.intermediate_pts is None:
            beginning = self.head.pts
        else:
            beginning = np.concatenate([self.head.pts, self.intermediate_pts],
                                       axis=0)

        # cover case where there is no tail defined (floating end)
        if self.tail is None:
            polished = beginning
        else:
            polished = np.concatenate([beginning, self.tail.pts[::-1]], axis=0)

        polished = self.del_colinear_points(polished)

        return polished

    def get_unit_vectors(self,
                         start: QRoutePoint,
                         end: QRoutePoint,
                         snap: bool = False) -> Tuple:
        """Return the unit and target vector in which the CPW should process as
        its coordinate sys.

        Args:
            start (QRoutePoint): Reference start point (direction from here)
            end (QRoutePoint): Reference end point (direction to here)
            snap (bool): True to snap to grid.  Defaults to False.

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
    def length(self) -> float:
        """Sum of all segments length, including the head.

        Return:
            length (float): Full point_array length
        """
        # get the final points (get_point also eliminate co-linear and short edges)
        points = self.get_points()

        # get the length without the corner rounding radius adjustment
        length_estimate = sum(
            norm(points[i + 1] - points[i]) for i in range(len(points) - 1))
        # compensate for corner rounding
        length_estimate -= self.length_excess_corner_rounding(points)

        return length_estimate

    def length_excess_corner_rounding(self, points) -> float:
        """Computes how much length to deduce for compensating the fillet
        settings.

        Args:
            points (list or array): List of vertices that will be receiving the corner rounding radius

        Return:
            length_excess (float): Corner rounding radius excess multiplied by the number of points
        """
        # deduct the corner rounding (WARNING: assumes fixed fillet for all corners)
        length_arch = 0.5 * self.p.fillet * math.pi
        length_corner = 2 * self.p.fillet
        length_excess = length_corner - length_arch
        # the start and and point are the pins, so no corner rounding
        return (len(points) - 2) * length_excess

    def assign_direction_to_anchor(self, ref_pt: QRoutePoint,
                                   anchor_pt: QRoutePoint):
        """Method to assign a direction to a point. Currently assigned as the
        max(x,y projection) of the direct path between the reference point and
        the anchor. Method directly modifies the anchor_pt.direction, thus
        there is no return value.

        Args:
            ref_pt (QRoutePoint): Reference point
            anchor_pt (QRoutePoint): Anchor point. if it already has a direction, the method will not overwrite it
        """
        if anchor_pt.direction is not None:
            # anchor_pt already has a direction (not an anchor?), so do nothing
            return
        # Current rule: stop_direction aligned with longer edge of the rectangle connecting ref_pt and anchor_pt
        ref = ref_pt.position
        anchor = anchor_pt.position
        # Absolute value of displacement between ref and anchor in x direction
        offsetx = abs(anchor[0] - ref[0])
        # Absolute value of displacement between ref and anchor in y direction
        offsety = abs(anchor[1] - ref[1])
        if offsetx >= offsety:  # "Wide" rectangle -> anchor_arrow points along x
            assigned_direction = np.array([ref[0] - anchor[0], 0])
        else:  # "Tall" rectangle -> anchor_arrow points along y
            assigned_direction = np.array([0, ref[1] - anchor[1]])
        anchor_pt.direction = assigned_direction / norm(assigned_direction)

    def make_elements(self, pts: np.ndarray):
        """Turns the CPW points into design elements, and add them to the
        design object.

        Args:
            pts (np.ndarray): Array of points
        """

        # prepare the routing track
        line = draw.LineString(pts)

        # compute actual final length
        p = self.p
        self.options._actual_length = str(
            line.length - self.length_excess_corner_rounding(line.coords)
        ) + ' ' + self.design.get_units()

        # expand the routing track to form the substrate core of the cpw
        self.add_qgeometry('path', {'trace': line},
                           width=p.trace_width,
                           fillet=p.fillet,
                           layer=p.layer)
        if self.type == "CPW":
            # expand the routing track to form the two gaps in the substrate
            # final gap will be form by this minus the trace above
            self.add_qgeometry('path', {'cut': line},
                               width=p.trace_width + 2 * p.trace_gap,
                               fillet=p.fillet,
                               layer=p.layer,
                               subtract=True)


class QRouteLead:
    """A simple class to define a an array of points with some properties,
    defines 2D positions and some of the 2D directions (XY plane).

    All values stored as np.ndarray of parsed floats.
    """

    def __init__(self, *args, **kwargs):
        """QRouteLead is a simple sequence of points.

        Used to accurately control one of the QRoute termination points
        Before that, it adds the variables that are needed to support routing.

        Attributes:
            pts (numpy Nx2): Sequence of points.  Defaults to None.
            direction (numpy 2x1): Normal from the last point of the array.  Defaults to None.
        """
        # keep track of all points so far in the route from both ends
        self.pts = None  # will be numpy Nx2
        # keep track of the direction of the tip of the lead (last point)
        self.direction = None  # will be numpy 2x1

    def seed_from_pin(self, pin: Dict) -> QRoutePoint:
        """Initialize the QRouteLead by giving it a starting point and a
        direction.

        Args:
            pin: object describing the "reference_pin" (not cpw_pin) this is attached to.
                this is currently (8/4/2020) a dictionary

        Return:
            QRoutePoint: Last point (for now the single point) in the QRouteLead
            The values are numpy arrays with two float points each.
        """
        position = pin['middle']
        direction = pin['normal']

        self.direction = direction
        self.pts = np.array([position])

        return QRoutePoint(position, direction)

    def go_straight(self, length: float):
        """Add a point ot 'length' distance in the same direction.

        Args:
            length (float) : How much to move by
        """
        self.pts = np.append(self.pts, [self.pts[-1] + self.direction * length],
                             axis=0)

    def go_left(self, length: float):
        """Straight line 90deg counter-clock-wise direction w.r.t. lead tip
        direction.

        Args:
            length (float): How much to move by
        """
        self.direction = draw.Vector.rotate(self.direction, np.pi / 2)
        self.pts = np.append(self.pts, [self.pts[-1] + self.direction * length],
                             axis=0)

    def go_right(self, length: float):
        """Straight line 90deg clock-wise direction w.r.t. lead tip direction.

        Args:
            length (float): How much to move by
        """
        self.direction = draw.Vector.rotate(self.direction, -1 * np.pi / 2)
        self.pts = np.append(self.pts, [self.pts[-1] + self.direction * length],
                             axis=0)

    def go_right45(self, length: float):
        """Straight line at 45 angle clockwise w.r.t lead tip direction.

        Args:
            length(float): How much to move by
        """
        self.direction = draw.Vector.rotate(self.direction, -1 * np.pi / 4)
        self.pts = np.append(self.pts, [self.pts[-1] + self.direction * length],
                             axis=0)

    def go_left45(self, length: float):
        """Straight line at 45 angle counter-clockwise w.r.t lead tip direction.

        Args:
            length(float): How much to move by
        """
        self.direction = draw.Vector.rotate(self.direction, np.pi / 4)
        self.pts = np.append(self.pts, [self.pts[-1] + self.direction * length],
                             axis=0)

    def go_angle(self, length: float, angle: float):
        """ Straight line at any angle w.r.t lead tip direction.

        Args:
            length(float): How much to move by
            angle(float): rotation angle w.r.t lead tip direction
        """
        self.direction = draw.Vector.rotate(self.direction, np.pi / 180 * angle)
        self.pts = np.append(self.pts, [self.pts[-1] + self.direction * length],
                             axis=0)

    @property
    def length(self):
        """Sum of all segments length, including the head.

        Return:
            length (float): Full point_array length
        """
        return sum(
            norm(self.pts[i + 1] - self.pts[i])
            for i in range(len(self.pts) - 1))

    def get_tip(self) -> QRoutePoint:
        """Access the last element in the QRouteLead.

        Return:
            QRoutePoint: Last point in the QRouteLead
            The values are numpy arrays with two float points each.
        """
        if self.pts.ndim == 1:
            return QRoutePoint(self.pts, self.direction)
        return QRoutePoint(self.pts[-1], self.direction)
