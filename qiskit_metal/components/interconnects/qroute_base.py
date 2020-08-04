"""
@author: Marco Facchini
"""
import numpy as np
from qiskit_metal.draw.utility import vec_unit_planar
from qiskit_metal import draw
from qiskit_metal.components import QComponent
from numpy.linalg import norm
from typing import List, Tuple, Union, Dict


class QRoutePoint:
    r"""A simple class to define a 2D Oriented_Point,
    with a 2D position and a 2D direction (XY plane).
    All values stored as np.ndarray of parsed floats.
    """

    def __init__(self, position: np.array, direction: np.array):
        """
        Arguments:
            position (np.ndarray of 2 points): Center point of the pin
            direction (np.ndarray of 2 points): *Normal vector* of the connector,
                defines which way it points outward.
                This is the normal vector to the surface on which the pin mates.
                Has unit norm.
        """
        self.position = position
        self.direction = direction


class QRoute(QComponent):
    r"""A simple class to define a generic route, using an array of planar points (x,y coordinates)
    and the direction of the pins that start and end the array
    Values stored as np.ndarray of parsed floats or np.array float pair
    """

    def __init__(self, *args, **kwargs):
        """Calls the QComponent __init__() to create a new Metal component
        Before that, it the variables that are needed to support routing
        """
        self.head = QRouteLead()
        self.tail = QRouteLead()

        # keep track of all points so far in the route from both ends
        self.intermediate_pts = None  # will be numpy 2xN

        # supported pin names (constants)
        self.start_pin_name = "start"
        self.end_pin_name = "end"
        super().__init__(*args, **kwargs)

        """Create a new Metal component and adds it's default_options to the design.

        Arguments:
            design (QDesign): The parent design.
            name (str): Name of the component.
            options (dict): User options that will override the defaults. (default: None)
            make (bool): True if the make function should be called at the end of the init.
                Options be used in the make function to create the geometry. (default: True)
            component_template (dict): User can overwrite the template options for the component
                that will be stored in the design, in design.template,
                and used every time a new component is instantiated.
                (default: None)

        Raises:
            ValueError: User supplied design isn't a QDesign

        Note:  Information copied from QDesign class.
            self._design.overwrite_enabled (bool):
            When True - If the string name, used for component, already
            exists in the design, the existing component will be
            deleted from design, and new component will be generated
            with the same name and newly generated component_id,
            and then added to design.

            When False - If the string name, used for component, already
            exists in the design, the existing component will be
            kept in the design, and current component will not be generated,
            nor will be added to the design. The variable design.self.status 
            will still be NotBuilt, as opposed to Initialization Successful.

            Either True or False - If string name, used for component, is NOT
            being used in the design, a component will be generated and
            added to design using the name.
        """

    def make(self):
        """
        Implements QComponent method.

        **Note:**
            * This method should be overwritten by the children make function.

        Raises:
            NotImplementedError: Overwrite this function by subclassing.
        """
        raise NotImplementedError()

    def get_pin(self, pin_data: Dict):
        """Recovers a pin from the dictionary

        Args:
            pin_data: dict {component: string, pin: string}

        Returns:
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
        reference_pin = self.get_pin(options_pin)

        # create the cpw pin and document the connections to the reference_pin in the netlist
        self.add_pin(name, reference_pin.points[::-1], self.p.trace_width)
        self.design.connect_pins(
            self.design.components[options_pin.component].id, options_pin.pin, self.id, name)

        # anchor the correct lead to the pin and return its position and direction
        return lead.seed_from_pin(reference_pin)

    def set_lead(self, name: str) -> QRoutePoint:
        # First define which lead you intend to modify
        if name == self.start_pin_name:
            options_lead = self.p.meander.lead_start
            lead = self.head
        elif name == self.end_pin_name:
            options_lead = self.p.meander.lead_end
            lead = self.tail
        else:
            raise Exception("Pin name \"" + name + "\" is not supported for this CPW." +
                            " The only supported pins are: start, end.")

        # then change the lead by adding a point in the same direction of the seed pin
        lead_length = max(options_lead, self.p.trace_width / 2)  # minimum lead, to be able to jog correctly
        lead.go_straight(lead_length)

        # return the last QRoutePoint of the lead
        return lead.get_tip()

    def get_points(self) -> np.ndarray:
        """Assembles the list of points for the route by concatenating:
        head_pts + intermediate_pts, tail_pts

        Returns:
            np.ndarray: (2x(H+N+T)) all points (x,y) of the CPW
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

    @property
    def length(self):
        """Sum of all segments length, including the head

        Return:
            length (float): full point_array length
        """
        points = self.get_points()
        return sum(norm(points[i + 1] - points[i]) for i in range(len(points) - 1))

    def route_to_align(self, concurrent_array):
        """
        THIS METHOD IS OUTDATED AND THUS NOT FUNCTIONING

        TODO: Develop code to make sure the tip of the leads align on one of the axes
        TODO: Adjusts the orientation of the meander, adding yet a new point:
            * Includes the start but not the given end point
            * If it cannot meander just returns the initial start point
        """
        print(self.points[-1])
        print(concurrent_array.positions[-1])

        # determine relative position
        concurrent_position = ""
        oriented_distance = concurrent_array.positions[-1] - self.points[-1]
        if oriented_distance[1] != 0: # vertical displacement
            concurrent_position += ["N", "S"][oriented_distance[1] < 0]
        if oriented_distance[0] != 0: # horizontal displacement
            concurrent_position += ["E", "W"][oriented_distance[0] < 0]
        else:
            return # points already aligned

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


class QRouteLead:
    """A simple class to define a an array of points with some properties,
    defines 2D positions and some of the 2D directions (XY plane).
    All values stored as np.ndarray of parsed floats.
    """

    def __init__(self):
        """QRouteLead basic content
        """
        # keep track of all points so far in the route from both ends
        self.pts = None  # will be numpy 2xN
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
        self.pts = np.append(self.pts, [self.pts[-1] + self.direction * length], axis=0)

    def go_left(self, length: float):
        """Straight line 90deg counter-clock-wise direction w.r.t. lead tip direction

        Args:
            length (float): how much to move by
        """
        self.direction = draw.Vector.rotate(self.direction, np.pi / 2)
        self.pts = np.append(self.pts, [self.pts[-1] + self.direction * length], axis=0)

    def go_right(self, length: float):
        """Straight line 90deg clock-wise direction w.r.t. lead tip direction

        Args:
            length (float): how much to move by
        """
        self.direction = draw.Vector.rotate(self.direction, -1 * np.pi / 2)
        self.pts = np.append(self.pts, [self.pts[-1] + self.direction * length], axis=0)

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

    def align_to(self, concurrent_array):
        """
        THIS METHOD IS OUTDATED AND THUS NOT FUNCTIONING

        TODO: Develop code to make sure the tip of the leads align on one of the axes
        TODO: Adjusts the orientation of the meander, adding yet a new point:
            * Includes the start but not the given end point
            * If it cannot meander just returns the initial start point
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
