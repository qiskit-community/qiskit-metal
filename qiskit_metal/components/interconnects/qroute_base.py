"""
@author: Marco Facchini
"""
import numpy as np
from qiskit_metal.draw.utility import vec_unit_planar
from qiskit_metal import draw
from qiskit_metal.components import QComponent
from numpy.linalg import norm
from typing import List, Tuple, Union, Dict


class QRoute(QComponent):
    r"""A simple class to define a generic route, using an array of planar points (x,y coordinates)
    and the direction of the pins that start and end the array
    Values stored as np.ndarray of parsed floats or np.array float pair
    """

    def __init__(self, *args, **kwargs):
        """Calls the QComponent __init__() to create a new Metal component
        Then adds to that the variables to support routing
        """
        # keep track of the most recent point direction
        self.head_direction = None  # will be numpy 2x1
        self.tail_direction = None  # will be numpy 2x1
        # keep track of all points so far in the route from both ends
        self.head_pts = None  # will be numpy 2xN
        self.tail_pts = None  # will be numpy 2xN
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

    def set_pin(self, name: str) -> Tuple:
        """Defines the CPW pins and returns the pin coordinates and normal direction vector

        Args:
            name: string (supported pin names are: start, end)

        Returns:
            tuple: `coordinate`, `direction`.
            The values are numpy arrays with two float points each.
        """
        if name == self.start_pin_name:
            options_pin = self.options.pin_inputs.start_pin
        elif name == self.end_pin_name:
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

        if name == "start":
            self.head_direction = direction
            self.head_pts = [position]
        if name == "end":
            self.tail_direction = direction
            self.tail_pts = [position]
        return position, direction

    def get_points(self, intermediate_pts=None) -> np.ndarray:
        """Assembles the list of points for the route by concatenating:
        head_pts + intermediate_pts, tail_pts

        Args:
            intermediate_pts: np.ndarray (2xN) array of point coordinates

        Returns:
            np.ndarray: (2x(H+N+T))
        """
        if intermediate_pts:
            return np.concatenate([
                self.head_pts,
                intermediate_pts,
                self.tail_pts[::-1]], axis=0)
        return np.concatenate([
            self.head_pts,
            self.tail_pts[::-1]], axis=0)

    def go_straight(self, length: float, head=True):
        """Add a point ot 'length' distance in the same direction

        Args:
            length (float) : how much to move by
            head (boolean) : default True. If set to False, it will move the tail
        """
        if head:
            self.head_pts = np.append(self.head_pts, [self.head_pts[-1] + self.head_direction * length], axis=0)
        else:
            self.tail_pts = np.append(self.tail_pts, [self.tail_pts[-1] + self.tail_direction * length], axis=0)

    def go_left(self, length: float, head=True):
        """Straight line 90deg counter-clock-wise direction w.r.t. Oriented_Point

        Args:
            length (float): how much to move by
            head (boolean) : default True. If set to False, it will move the tail

        THIS METHOD IS NOT USED AT THIS TIME (7/2/20). PLAN TO USE
        """
        if head:
            self.head_direction = draw.Vector.rotate(self.head_direction, np.pi / 2)
            self.head_pts = np.append(self.head_pts, [self.head_pts[-1] + self.head_direction * length], axis=0)
        else:
            self.tail_direction = draw.Vector.rotate(self.tail_direction, np.pi / 2)
            self.tail_pts = np.append(self.tail_pts, [self.tail_pts[-1] + self.tail_direction * length], axis=0)


    def go_right(self, length: float, head=True):
        """Straight line 90deg clock-wise direction w.r.t. Oriented_Point

        Args:
            length (float): how much to move by
            head (boolean) : default True. If set to False, it will move the tail

        THIS METHOD IS NOT USED AT THIS TIME (7/2/20). PLAN TO USE
        """
        if head:
            self.head_direction = draw.Vector.rotate(self.head_direction, -1 * np.pi / 2)
            self.head_pts = np.append(self.head_pts, [self.head_pts[-1] + self.head_direction * length], axis=0)
        else:
            self.tail_direction = draw.Vector.rotate(self.tail_direction, -1 * np.pi / 2)
            self.tail_pts = np.append(self.tail_pts, [self.tail_pts[-1] + self.tail_direction * length], axis=0)

    @property
    def length(self):
        """Sum of all segments length, including the head

        Return:
            length (float): full point_array length
        """
        length = sum(norm(self.points[i + 1] - self.points[i]) for i in range(len(self.points) - 1))
        if self.pin_end:
            return length + norm(self.points[-1] - self.pin_end.position)
        return length

    def route_to_align(self, concurrent_array):
        """
        In this code, meanders are aligned to face each-other. So they are easier to connect.


        TODO: Make sure the two points align on one of the axes, by adding a new point

        TODO: Adjusts the orientation of the meander, adding yet a new point:
            * Includes the start but not the given end point
            * If it cannot meander just returns the initial start point

        Arguments:
            concurrent_array (Oriented_2D_Array): Other end of the CPW

        THIS METHOD IS NOT USED AT THIS TIME (7/2/20). PLAN TO USE
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
            concurrent_array (QRouteLead): Other end of the CPW
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


class QRoutePoint:
    r"""A simple class to define a 2D Oriented_Point,
    with a 2D position and a 2D direction (XY plane).
    All values stored as np.ndarray of parsed floats.
    """

    # TODO: Maybe move this class out of here, more general.

    def __init__(self, array: QRouteLead):
        """
        Arguments:
            array (QRouteLead): 2D array
        """
        self.position = array.positions[-1]
        self.direction = array.directions[-1]
