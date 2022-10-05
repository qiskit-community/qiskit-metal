from dataclasses import dataclass, field
from typing import Union, List, Tuple
import numpy as np
import gmsh
from qiskit_metal.draw.utility import Vec3D


@dataclass
class Vec3DArray:
    """Class to define an array of np.ndarray objects

    Raises:
        TypeError: if layer_z value is not provided for 2D design
        ValueError: if dimensionality of coordinate > 3

    Returns:
        Vec3DArray: Array of np.ndarray objects
    """
    points: List[np.ndarray]
    path_vecs: List[np.ndarray] = field(init=False)

    def __post_init__(self):
        """This is to initialize the `path_vecs` field separately
        as it depends on the `points` field, and needs to be
        calculated after the __init__ for the dataclass is called.

        CAUTION: Please don't change this unless you really need to!
        """
        self.path_vecs = []
        for i in range(0, len(self.points) - 1):
            v1 = self.points[i]
            v2 = self.points[i + 1]
            v12 = Vec3D.normed(Vec3D.sub(v2, v1))
            self.path_vecs.append(v12)

    def append(self, vecs: List[np.ndarray]):
        """Append vector to the array

        Args:
            vecs (List[np.ndarray]): list of vectors to append
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
            v1 = Vec3D.normed(self.path_vecs[i])
            v2 = Vec3D.normed(self.path_vecs[j])
            return np.round(np.pi - np.arccos(Vec3D.dot(v1, v2)), decimals=9)

        v1 = Vec3D.normed(self.points[i])
        v2 = Vec3D.normed(self.points[j])
        return np.round(np.pi - np.arccos(Vec3D.dot(v1, v2)), decimals=9)

    @staticmethod
    def make_vec3DArray(points: List[List[Union[int, float]]],
                        layer_z: float = None):
        """Create a Vec3DArray object from list of points

        Args:
            points (List[List[Union[int, float]]]): list of points
            layer_z (float, optional): z-coordinate of layer in case
                                    of 2D design. Defaults to None.

        Raises:
            TypeError: if layer_z value is not provided for 2D design
            ValueError: if dimensionality of coordinate > 3

        Returns:
            Vec3DArray: return a Vec3DArray object
        """
        vecs = []
        for xyz in points:
            if len(xyz) > 2:
                vecs.append(np.array(xyz))
            elif len(xyz) == 2:
                if layer_z is not None:
                    vecs.append(np.array([xyz[0], xyz[1], layer_z]))
                else:
                    raise TypeError(
                        f"Expected a layer_z value for 2D geometry, found NoneType."
                    )
            else:
                raise ValueError(
                    f"Expected a 2-D or 3-D coordinate, got {len(xyz)}-D instead."
                )

        return Vec3DArray(vecs)


def vecs_to_gmsh_points(vecs: List[np.ndarray], layer_z: float) -> list:
    """Create Gmsh points from np.ndarray objs

    Args:
        vecs (List[np.ndarray]): list of np.ndarray objs
        layer_z (float): z-coordinate of layer

    Returns:
        list: list of Gmsh points
    """
    points = []
    for v in vecs:
        p = gmsh.model.occ.addPoint(v[0], v[1], layer_z)
        points.append(p)

    return points


def line_width_offset_pts(pt_vec: np.ndarray,
                          path_vec: np.ndarray,
                          width: float,
                          layer_z: float,
                          ret_pts: bool = True) -> list:
    """Create offset points for straight line

    Args:
        pt_vec (np.ndarray): vectors of points in line
        path_vec (np.ndarray): vectors along lines
        width (float): width for offset
        layer_z (float): z-coordinate of layer
        ret_pts (bool, optional): Return Gmsh points if True
                        else return np.ndarray. Defaults to True.

    Returns:
        list: list of Gmsh points or vec3D objs
    """
    path_angle = Vec3D.angle_azimuth(path_vec)
    perp_angle = path_angle + np.pi / 2
    cos_t = np.round(np.cos(perp_angle), decimals=9)
    sin_t = np.round(np.sin(perp_angle), decimals=9)
    r = width / 2

    offset_vec = np.array([r * cos_t, r * sin_t, 0])
    v1 = Vec3D.add(pt_vec, offset_vec)
    v2 = Vec3D.sub(pt_vec, offset_vec)

    if ret_pts:
        pts = vecs_to_gmsh_points([v1, v2], layer_z)
        return pts
    else:
        return [v1, v2]


def arc_width_offset_pts(vec1: np.ndarray, vec3: np.ndarray, angle: float,
                         width: float, layer_z: float) -> list:
    """Create offset points for Circle Arcs

    Args:
        vec1 (np.ndarray): incoming vector to arc
        vec3 (np.ndarray): outgoing vector from arc
        angle (float): angle of arc
        width (float): width for offset
        layer_z (float): z-coordinate of layer

    Returns:
        list: list of Gmsh points
    """
    perp_angle = np.pi / 2 - angle  # π - (angle + π/2)
    cos_t = np.round(np.cos(perp_angle), decimals=9)
    sin_t = np.round(np.sin(perp_angle), decimals=9)
    r = width / 2

    offset1 = np.array([0, r, 0])
    v1 = Vec3D.add(vec1, offset1)
    v2 = Vec3D.sub(vec1, offset1)

    sign = 1 if angle == np.pi / 2 else -1
    offset2 = np.array([r * cos_t * sign, r * sin_t * sign, 0])

    v3 = Vec3D.add(vec3, offset2)
    v4 = Vec3D.sub(vec3, offset2)

    pts = vecs_to_gmsh_points([v1, v2, v3, v4], layer_z)
    return pts


def make_arc_vecs(angle: float,
                  fillet: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Create vectors for the circle arc

    Args:
        angle (float): angle of arc
        fillet (float): fillet radius

    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray]: vectors defining the arc control points
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

    v1 = np.array([p1x, p1y, 0])
    v2 = np.array([p2x, p2y, 0])
    v3 = np.array([p3x, p3y, 0])

    return v1, v2, v3


def transform_arc_points(pts: list, translate: np.ndarray,
                         path_vecs: list) -> list:
    """Apply transformation to arc points

    Args:
        pts (list): list of Gmsh points
        translate (np.ndarray): translation vector
        path_vecs (list): vectors of actual position

    Returns:
        list: list of Gmsh points
    """
    dim_tags = [(0, p) for p in pts]
    new_pts = [p for p in pts]

    angle1 = Vec3D.angle_azimuth(path_vecs[0])
    cross_vec = Vec3D.cross(path_vecs[0], path_vecs[1])
    mirror = True if np.sign(Vec3D.normed(cross_vec)[2]) < 0 else False

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
    gmsh.model.occ.translate(dim_tags, translate[0], translate[1], 0)
    return new_pts


def draw_curves(recent_pts: list, curves1: list,
                curves2: list) -> Tuple[list, list, list]:
    """Draw the curves using control points

    Args:
        recent_pts (list): list to keep track of recent points
        curves1 (list): curves on one side of offset
        curves2 (list): curves on other side of offset

    Raises:
        RuntimeError: raised when the number of points in recent_pts
                            is not what is expected by the program.

    Returns:
        Tuple[list, list, list]: returns a tuple of recent_pts, curves1, curves2
    """
    rec_pts = []

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
                       layer_z: float,
                       fillet: float,
                       width: float,
                       bad_fillet_idxs: List[int],
                       straight_line_tol: float = 1e-9) -> list:
    """Helper function for rendering path QGeometry curves

    Args:
        vecs (Vec3DArray): vector array
        layer_z (float): z-coordinate of layer
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
            p1, p2 = line_width_offset_pts(v, vecs.path_vecs[i], width, layer_z)
            recent_pts += [p1, p2]
            curves1 += [gmsh.model.occ.addLine(p1, p2)]
            continue

        if i == len(vecs.points) - 1:
            p1, p2 = line_width_offset_pts(v, vecs.path_vecs[i - 1], width,
                                           layer_z)
            recent_pts += [p1, p2]
            curves1 += [gmsh.model.occ.addLine(p1, p2)]
            continue

        pv1 = vecs.path_vecs[i - 1]
        pv2 = vecs.path_vecs[i]
        angle12 = vecs.get_angle_between(i - 1, i)
        is_filleted = False if i in bad_fillet_idxs else True

        if fillet < 0.0:
            raise ValueError(f"Expected positive fillet radius, got {fillet}.")

        elif fillet > 0.0 and is_filleted:
            if np.allclose(angle12, np.pi, rtol=straight_line_tol):
                p1, p2 = line_width_offset_pts(v, pv2, width, layer_z)
                recent_pts += [p1, p2]

            else:
                v1, v2, v3 = make_arc_vecs(angle12, fillet)
                p1, p2, p4, p5 = arc_width_offset_pts(v1, v3, angle12, width,
                                                      layer_z)
                p3 = vecs_to_gmsh_points([v2], layer_z)[0]

                new_pts = transform_arc_points([p1, p2, p3, p4, p5], v,
                                               [pv1, pv2])
                recent_pts += new_pts

        else:
            half_angle = angle12 / 2
            if np.allclose(angle12, np.pi, rtol=straight_line_tol):
                right_turn = 1
            else:
                right_turn = -np.sign(Vec3D.normed(Vec3D.cross(pv1, pv2))[2])
            turn_pt_vec = vecs.points[i]
            pv1_normed = Vec3D.normed(pv1)
            pv1_scaled = Vec3D.scale(
                pv1_normed, width / (2 * np.cos(np.pi / 2 - half_angle)))
            pv1_trans = Vec3D.translate(pv1_scaled, turn_pt_vec)
            offset_vec1 = Vec3D.rotate(pv1_trans,
                                       turn_pt_vec,
                                       az=True,
                                       radians=right_turn * half_angle)
            offset_vec2 = Vec3D.rotate(pv1_trans,
                                       turn_pt_vec,
                                       az=True,
                                       radians=-right_turn *
                                       (np.pi - half_angle))
            p1 = gmsh.model.occ.addPoint(offset_vec1[0], offset_vec1[1],
                                         layer_z)
            p2 = gmsh.model.occ.addPoint(offset_vec2[0], offset_vec2[1],
                                         layer_z)
            recent_pts += [p1, p2] if right_turn > 0 else [p2, p1]

        recent_pts, curves1, curves2 = draw_curves(recent_pts, curves1, curves2)

    _, curves1, curves2 = draw_curves(recent_pts, curves1, curves2)

    last_curve = curves1.pop(-2)
    curves1.append(last_curve)
    curves = curves1 + curves2[::-1]

    return curves
