from dataclasses import dataclass, field
from typing import Union
import numpy as np
import gmsh


@dataclass
class Vec3D:
    """Class to define a 3D vector and perform operations on them.

    Returns:
        Vec3D: A 3-dimensional vector object
    """
    vec: np.ndarray

    @property
    def x(self):
        return self.vec[0]

    @property
    def y(self):
        return self.vec[1]

    @property
    def z(self):
        return self.vec[2]

    def mag(self) -> float:
        """Magnitude of the vector

        Returns:
            float: magnitude of the vector calculated by Frobenius norm
        """
        return np.round(np.linalg.norm(self.vec), decimals=9)

    def normalize(self):
        """Normalize a vector

        Returns:
            Vec3D: normalized vector
        """
        return Vec3D(self.vec / self.mag())

    def add(self, other):
        """Adds two vectors

        Args:
            other (Vec3D): the other vector

        Returns:
            Vec3D: resultant vector
        """
        return Vec3D(self.vec + other.vec)

    def dot(self, other) -> float:
        """Dot product of two vectors

        Args:
            other (Vec3D): the other vector

        Returns:
            float: result from dot product
        """
        return np.round(self.vec.dot(other.vec), decimals=9)

    def cross(self, other):
        """Cross product of two vectors

        Args:
            other (Vec3D): the other vector

        Returns:
            Vec3D: resultant vector
        """
        self_norm = self.normalize().vec
        other_norm = other.normalize().vec
        return Vec3D(np.cross(self_norm, other_norm))

    def sub(self, other):
        """Difference between two vectors

        Args:
            other (Vec3D): the other vector

        Returns:
            Vec3D: resultant vector
        """
        return Vec3D(self.vec - other.vec)

    def scale(self, value: Union[int, float]):
        """Multiply the vector with a scalar

        Args:
            value (Union[int, float]): scalar value

        Returns:
            Vec3D: resultant vector
        """
        return Vec3D(self.vec * value)

    def dist(self, other) -> float:
        """Calculate Euler distance between two vectors

        Args:
            other (Vec3D): the other vector

        Returns:
            float: Euler distance
        """
        return np.round(np.sqrt(np.sum((self.vec - other.vec)**2)), decimals=9)

    def translate(self, translate_vec, ret_new_obj: bool = False):
        """Translate a vector

        Args:
            translate_vec (Vec3D): translation values as a vector
            ret_new_obj (bool, optional): Return a new vec3D object or
                                    modify the same. Defaults to False.

        Returns:
            Union[Vec3D, None]: return a new Vec3D object or None
                                depending on "ret_new_obj"
        """
        if not ret_new_obj:
            self.vec += translate_vec.vec
        else:
            return self.add(translate_vec)

    def rotate(self,
               cvec,
               ax: bool = False,
               ay: bool = False,
               az: bool = False,
               angle: float = 0.0,
               ret_new_obj: bool = False):
        """Rotate a vector

        Args:
            cvec (Vec3D): center of rotation as a vector
            ax (bool, optional): Rotate around x-axis. Defaults to False.
            ay (bool, optional): Rotate around y-axis. Defaults to False.
            az (bool, optional): Rotate around z-axis. Defaults to False.
            angle (float, optional): Angle of rotation. Defaults to 0.0.
            ret_new_obj (bool, optional): return a new Vec3D object or
                                    modify the same. Defaults to False.

        Returns:
            Union[Vec3D, None]: return a new Vec3D object or None
                                depending on "ret_new_obj"
        """

        if ax:
            rot_x = np.array([[1, 0, 0], [0, np.cos(angle), -np.sin(angle)],
                              [0, np.sin(angle),
                               np.cos(angle)]])
            translate_vec = np.array([0, cvec.y, cvec.z])
            new_vec = rot_x.dot((self.vec - translate_vec)) + translate_vec

        if ay:
            rot_y = np.array([[np.cos(angle), 0,
                               np.sin(angle)], [0, 1, 0],
                              [-np.sin(angle), 0,
                               np.cos(angle)]])
            translate_vec = np.array([cvec.x, 0, cvec.z])
            new_vec = rot_y.dot((self.vec - translate_vec)) + translate_vec

        if az:
            rot_z = np.array([[np.cos(angle), -np.sin(angle), 0],
                              [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
            translate_vec = np.array([cvec.x, cvec.y, 0])
            new_vec = rot_z.dot((self.vec - translate_vec)) + translate_vec

        if not ret_new_obj:
            self.vec = new_vec
        else:
            return Vec3D(new_vec)

    def angle_elevation(self) -> float:
        """Returns the elevation angle of vector

        Returns:
            float: elevation angle in radians
        """
        unit_z = Vec3D(np.array([0, 0, 1]))
        unit_self = self.normalize()
        return np.arccos(unit_self.dot(unit_z))

    def angle_azimuth(self) -> float:
        """Returns the azimuthal angle of vector

        Returns:
            float: azimuthal angle of vector
        """
        if self.x == 0:
            return np.round(np.arctan(np.sign(self.y) * np.inf), decimals=9)
        if self.x < 0:
            return np.round(np.arctan(self.y / self.x) + np.pi, decimals=9)

        return np.round(np.arctan(self.y / self.x), decimals=9)


@dataclass
class Vec3DArray:
    """Class to define an array of Vec3D objects

    Raises:
        TypeError: if chip_z value is not provided for 2D design
        ValueError: if dimensionality of coordinate > 3

    Returns:
        Vec3DArray: Array of Vec3D objects
    """
    points: list[Vec3D]
    path_vecs: list[Vec3D] = field(init=False)

    def __post_init__(self):
        self.path_vecs = []
        for i in range(0, len(self.points) - 1):
            v1 = self.points[i]
            v2 = self.points[i + 1]
            v12 = v2.sub(v1).normalize()
            self.path_vecs.append(v12)

    def append(self, vecs: list[Vec3D]):
        """Append vector to the array

        Args:
            vecs (list[Vec3D]): list of vectors to append
        """
        self.points += vecs

    def get_angle_between(self,
                          i: int,
                          j: int,
                          ret_path_angle: bool = True) -> float:
        """Return acute angle between two vectors depending on "ret_path_angle"

        Args:
            i (int): i^th index from path_vecs or points list
            j (int): j^th index from path_vecs or points list
            ret_path_angle (bool, optional): Return angl between path_vecs
                    if True and between points if False. Defaults to True.

        Returns:
            float: angle between the corresponding vectors
        """
        if ret_path_angle:
            v1 = self.path_vecs[i].normalize()
            v2 = self.path_vecs[j].normalize()
            return np.round(np.pi - np.arccos(v1.dot(v2)), decimals=9)

        v1 = self.points[i].normalize()
        v2 = self.points[j].normalize()
        return np.round(np.pi - np.arccos(v1.dot(v2)), decimals=9)

    @staticmethod
    def make_vec3DArray(points: list[list[Union[int, float]]],
                        chip_z: float = None):
        """Create a Vec3DArray object from list of points

        Args:
            points (list[list[Union[int, float]]]): list of points
            chip_z (float, optional): z-coordinate of chip in case
                                    of 2D design. Defaults to None.

        Raises:
            TypeError: if chip_z value is not provided for 2D design
            ValueError: if dimensionality of coordinate > 3

        Returns:
            Vec3DArray: return a Vec3DArray object
        """
        vecs = []
        for xyz in points:
            if len(xyz) > 2:
                vecs.append(Vec3D(np.array(xyz)))
            elif len(xyz) == 2:
                if chip_z is not None:
                    vecs.append(Vec3D(np.array([xyz[0], xyz[1], chip_z])))
                else:
                    raise TypeError(
                        f"Expected a chip_z value for 2D geometry, found NoneType."
                    )
            else:
                raise ValueError(
                    f"Expected a 2-D or 3-D coordinate, got {len(xyz)}-D instead."
                )

        return Vec3DArray(vecs)


def vecs_to_gmsh_points(vecs: list[Vec3D], chip_z: float) -> list:
    """Create Gmsh points from Vec3D objs

    Args:
        vecs (list[Vec3D]): list of Vec3D objs
        chip_z (float): z-coordinate of chip

    Returns:
        list: list of Gmsh points
    """
    points = []
    for v in vecs:
        p = gmsh.model.occ.addPoint(v.x, v.y, chip_z)
        points.append(p)

    return points


def line_width_offset_pts(pt_vec: Vec3D,
                          path_vec: Vec3D,
                          width: float,
                          chip_z: float,
                          ret_pts: bool = True) -> list:
    """Create offset points for straight line

    Args:
        pt_vec (Vec3D): vectors of points in line
        path_vec (Vec3D): vectors along lines
        width (float): width for offset
        chip_z (float): z-coordinate of chip
        ret_pts (bool, optional): Return Gmsh points if True
                        else return Vec3D. Defaults to True.

    Returns:
        list: list of Gmsh points or vec3D objs
    """
    # TODO: change this to use Vec3D translate and rotate
    path_angle = path_vec.angle_azimuth()
    perp_angle = path_angle + np.pi / 2
    cos_t = np.round(np.cos(perp_angle), decimals=9)
    sin_t = np.round(np.sin(perp_angle), decimals=9)
    r = width / 2

    offset_vec = Vec3D(np.array([r * cos_t, r * sin_t, 0]))
    v1 = pt_vec.add(offset_vec)
    v2 = pt_vec.sub(offset_vec)

    if ret_pts:
        pts = vecs_to_gmsh_points([v1, v2], chip_z)
        return pts
    else:
        return [v1, v2]


def arc_width_offset_pts(vec1: Vec3D, vec3: Vec3D, angle: float, width: float,
                         chip_z: float) -> list:
    """Create offset points for Circle Arcs

    Args:
        vec1 (Vec3D): incoming vector to arc
        vec3 (Vec3D): outgoing vector from arc
        angle (float): angle of arc
        width (float): width for offset
        chip_z (float): z-coordinate of chip

    Returns:
        list: list of Gmsh points
    """
    # TODO: change this to use Vec3D translate and rotate
    perp_angle = np.pi / 2 - angle  # π - (angle + π/2)
    cos_t = np.round(np.cos(perp_angle), decimals=9)
    sin_t = np.round(np.sin(perp_angle), decimals=9)
    r = width / 2

    offset1 = Vec3D(np.array([0, r, 0]))
    v1 = vec1.add(offset1)
    v2 = vec1.sub(offset1)

    sign = 1 if angle == np.pi / 2 else -1
    offset2 = Vec3D(np.array([r * cos_t * sign, r * sin_t * sign, 0]))

    v3 = vec3.add(offset2)
    v4 = vec3.sub(offset2)

    pts = vecs_to_gmsh_points([v1, v2, v3, v4], chip_z)
    return pts


def make_arc_vecs(angle: float, fillet: float) -> tuple[Vec3D, Vec3D, Vec3D]:
    """Create vectors for the circle arc

    Args:
        angle (float): angle of arc
        fillet (float): fillet radius

    Returns:
        tuple[Vec3D, Vec3D, Vec3D]: vectors defining the arc control points
    """
    sector_angle = np.pi - angle
    intercept = np.abs(fillet * np.tan(sector_angle / 2))
    cos_t = np.round(np.cos(sector_angle), decimals=9)
    sin_t = np.round(np.sin(sector_angle), decimals=9)

    p1x = np.round(-intercept, decimals=9)
    p1y = 0
    p2x = np.round(p1x, decimals=9)
    p2y = np.round(p1y + fillet, decimals=9)
    p3x = np.round(intercept * cos_t, decimals=9)
    p3y = np.round(intercept * sin_t, decimals=9)

    v1 = Vec3D(np.array([p1x, p1y, 0]))
    v2 = Vec3D(np.array([p2x, p2y, 0]))
    v3 = Vec3D(np.array([p3x, p3y, 0]))

    return v1, v2, v3


def transform_arc_points(pts: list, translate: Vec3D, path_vecs: list,
                         chip_z: float) -> list:
    """Apply transformation to arc points

    Args:
        pts (list): list of Gmsh points
        translate (Vec3D): translation vector
        path_vecs (list): vectors of actual position
        chip_z (float): z-coordinate of chip

    Returns:
        list: list of Gmsh points
    """
    dim_tags = [(0, p) for p in pts]
    new_pts = [p for p in pts]

    angle1 = path_vecs[0].angle_azimuth()
    mirror = True if np.sign(path_vecs[0].cross(path_vecs[1]).z) < 0 else False

    if mirror:
        # Flip right turn start/end points
        p1 = new_pts.pop(0)
        p4 = new_pts.pop(2)
        new_pts.insert(1, p1)
        new_pts.append(p4)
        gmsh.model.occ.mirror(dim_tags, a=0, b=1, c=0, d=0)

    gmsh.model.occ.rotate(dim_tags,
                          x=0,
                          y=0,
                          z=0,
                          ax=0,
                          ay=0,
                          az=1,
                          angle=angle1)
    gmsh.model.occ.translate(dim_tags, translate.x, translate.y, chip_z)
    return new_pts


def draw_curves(recent_pts: list, curves1: list,
                curves2: list) -> tuple[list, list, list]:
    """Draw the curves using control points

    Args:
        recent_pts (list): list to keep track of recent points
        curves1 (list): curves on one side of offset
        curves2 (list): curves on other side of offset

    Raises:
        RuntimeError: raised when the number of points in recent_pts
                            is not what is expected by the program.

    Returns:
        tuple[list, list, list]: returns a tuple of recent_pts, curves1, curves2
    """
    rec_pts = []

    # TODO: think of a better error message
    if len(recent_pts) not in [4, 7]:
        raise RuntimeError(
            "Unexpected geometry {len(recent_pts) not in [4,7]}. Check your geometry and retry."
        )

    l1 = gmsh.model.occ.addLine(recent_pts[0], recent_pts[2])
    l2 = gmsh.model.occ.addLine(recent_pts[1], recent_pts[3])
    curves1 += [l1]
    curves2 += [l2]

    if len(recent_pts) == 7:
        a1 = gmsh.model.occ.addCircleArc(recent_pts[2], recent_pts[4],
                                         recent_pts[5])
        a2 = gmsh.model.occ.addCircleArc(recent_pts[3], recent_pts[4],
                                         recent_pts[6])
        curves1 += [a1]
        curves2 += [a2]

    rec_pts = recent_pts[-2:]

    return rec_pts, curves1, curves2


def render_path_curves(vecs: Vec3DArray,
                       chip_z: float,
                       fillet: float,
                       width: float,
                       straight_line_tol: float = 1e-9) -> list:
    """Helper function for rendering path QGeometry curves

    Args:
        vecs (Vec3DArray): vector array
        chip_z (float): z-coordinate of chip
        fillet (float): fillet radius
        width (float): width for offset
        straight_line_tol (float, optional): Tolerance for straight line
                                        through a point. Defaults to 1e-9.

    Raises:
        ValueError: raises when fillet radius < 0.0

    Returns:
        list: list of Gmsh curves
    """
    recent_pts = []  # To store recent Gmsh points
    curves1, curves2 = [], []  # To store lines and arcs for each visual side

    for i, v in enumerate(vecs.points):
        if i == 0:
            p1, p2 = line_width_offset_pts(v, vecs.path_vecs[i], width, chip_z)
            recent_pts += [p1, p2] if fillet != 0.0 else [p2, p1]
            curves1 += [gmsh.model.occ.addLine(p1, p2)]
            continue

        if i == len(vecs.points) - 1:
            p1, p2 = line_width_offset_pts(v, vecs.path_vecs[i - 1], width,
                                           chip_z)
            recent_pts += [p1, p2] if fillet != 0.0 else [p2, p1]
            curves1 += [gmsh.model.occ.addLine(p1, p2)]
            continue

        pv1 = vecs.path_vecs[i - 1]
        pv2 = vecs.path_vecs[i]
        angle12 = vecs.get_angle_between(i - 1, i)

        pt_vec_prev = vecs.points[i - 1]
        pt_vec_next = vecs.points[i + 1]
        is_filleted = True if (v.dist(pt_vec_prev) > 2 * fillet and
                               v.dist(pt_vec_next) > 2 * fillet) else False
        # TODO: fix the swapping in recent_pts for filleted to non-filleted edges

        if fillet < 0.0:
            raise ValueError(f"Expected positive fillet radius, got {fillet}.")

        elif fillet > 0.0 and is_filleted:
            if np.allclose(angle12, np.pi, rtol=straight_line_tol):
                p1, p2 = line_width_offset_pts(v, pv2, width, chip_z)
                recent_pts += [p1, p2]

            else:
                v1, v2, v3 = make_arc_vecs(angle12, fillet)
                p1, p2, p4, p5 = arc_width_offset_pts(v1, v3, angle12, width,
                                                      chip_z)
                p3 = vecs_to_gmsh_points([v2], chip_z)[0]

                new_pts = transform_arc_points([p1, p2, p3, p4, p5], v,
                                               [pv1, pv2], chip_z)
                recent_pts += new_pts

        else:
            half_angle = angle12 / 2
            right_turn = -np.sign(pv1.cross(pv2).z)
            turn_pt_vec = vecs.points[i]
            pv1_scaled = pv1.normalize().scale(
                width / (2 * np.cos(np.pi / 2 - half_angle)))
            pv1_scaled.translate(turn_pt_vec)
            offset_vec1 = pv1_scaled.rotate(turn_pt_vec,
                                            az=True,
                                            angle=right_turn * half_angle,
                                            ret_new_obj=True)
            offset_vec2 = pv1_scaled.rotate(turn_pt_vec,
                                            az=True,
                                            angle=-right_turn *
                                            (np.pi - half_angle),
                                            ret_new_obj=True)
            p1 = gmsh.model.occ.addPoint(offset_vec1.x, offset_vec1.y, chip_z)
            p2 = gmsh.model.occ.addPoint(offset_vec2.x, offset_vec2.y, chip_z)
            recent_pts += [p2, p1] if right_turn > 0 else [p1, p2]

        recent_pts, curves1, curves2 = draw_curves(recent_pts, curves1, curves2)

    _, curves1, curves2 = draw_curves(recent_pts, curves1, curves2)

    last_curve = curves1.pop(-2)
    curves1.append(last_curve)
    curves = curves1 + curves2[::-1]

    return curves