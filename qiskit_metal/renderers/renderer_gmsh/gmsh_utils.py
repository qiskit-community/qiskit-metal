from dataclasses import dataclass, field
import numpy as np
import gmsh
from qiskit_metal.designs.design_base import QDesign
from typing import Union

@dataclass
class Vec2D:
    x: float
    y: float
    
    def mag(self):
        return np.round(np.sqrt(self.x**2 + self.y**2), decimals=9)
    
    def normalize(self):
        mag = self.mag()
        return Vec2D(x=self.x/mag, y=self.y/mag)
    
    def add(self, other):
        return Vec2D(x=self.x+other.x, y=self.y+other.y)
    
    def dot(self, other):
        return np.round((self.x*other.x) + (self.y*other.y), decimals=9)
    
    def cross_prod_sign(self, other):
        self_norm = self.normalize()
        other_norm = other.normalize()
        return (self_norm.x * other_norm.y - self_norm.y * other_norm.x)
    
    def sub(self, other):
        return Vec2D(x=self.x-other.x, y=self.y-other.y)
    
    def dist(self, other):
        return np.round(
            np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2),
            decimals=9)
    
    def angle(self):
        if self.x == 0:
            return np.round(np.arctan(np.sign(self.y) * np.inf), decimals=9)
        if self.x < 0:
            return np.round(np.arctan(self.y/self.x) + np.pi, decimals=9)
        
        return np.round(np.arctan(self.y/self.x), decimals=9)

@dataclass
class Vec2DArray:
    points: list[Vec2D]
    path_vecs: list[Vec2D] = field(init=False)
    
    def __post_init__(self):
        self.path_vecs = []
        for i in range(0, len(self.points)-1):
            v1 = self.points[i]; v2 = self.points[i+1]
            v12 = v2.sub(v1).normalize()
            self.path_vecs.append(v12)
            
    def append(self, vecs:list[Vec2D]):
        self.points += vecs
        
    def get_angle_between(self, i, j, path_angle:bool=True):
        if path_angle:
            v1 = self.path_vecs[i].normalize()
            v2 = self.path_vecs[j].normalize()
            return np.round(np.pi - np.arccos(v1.dot(v2)), decimals=9)
        
        v1 = self.points[i].normalize()
        v2 = self.points[j].normalize()
        return np.round(np.pi - np.arccos(v1.dot(v2)), decimals=9)


    @staticmethod
    def make_vec2DArray(points:list[Union[int, float]]):
        vecs = []
        for xy in points:
            vecs.append(Vec2D(x=xy[0], y=xy[1]))

        return Vec2DArray(vecs)


def vecs_to_gmsh_points(vecs:list[Vec2D], chip_z:float):
    points = []
    for v in vecs:
        p = gmsh.model.occ.addPoint(v.x, v.y, chip_z)
        points.append(p)

    return points

def line_width_offset_pts(vec:Vec2D, path_vec:Vec2D, width:float, chip_z:float, ret_pts:bool = True):
    path_angle = path_vec.angle()
    perp_angle = path_angle + np.pi/2
    cos_t = np.round(np.cos(perp_angle), decimals=9)
    sin_t = np.round(np.sin(perp_angle), decimals=9)
    r = width/2

    v1 = Vec2D(x=np.round(vec.x + r*cos_t, decimals=9),
               y=np.round(vec.y + r*sin_t, decimals=9))
    v2 = Vec2D(x=np.round(vec.x - r*cos_t, decimals=9),
               y=np.round(vec.y - r*sin_t, decimals=9))

    if ret_pts:
        pts = vecs_to_gmsh_points([v1, v2], chip_z)
        return pts
    else:
        return [v1, v2]

def arc_width_offset_pts(vec1:Vec2D, vec3:Vec2D, angle:float, width:float, chip_z:float):
    perp_angle = np.pi/2 - angle # π - (angle + π/2)
    cos_t = np.round(np.cos(perp_angle), decimals=9)
    sin_t = np.round(np.sin(perp_angle), decimals=9)
    r = width/2

    v1 = Vec2D(x=vec1.x, y=vec1.y+r)
    v2 = Vec2D(x=vec1.x, y=vec1.y-r)

    sign = 1 if angle == np.pi/2 else -1

    v3 = Vec2D(x=np.round(vec3.x + (r*cos_t*sign), decimals=9),
               y=np.round(vec3.y + (r*sin_t*sign), decimals=9))
    v4 = Vec2D(x=np.round(vec3.x - (r*cos_t*sign), decimals=9),
               y=np.round(vec3.y - (r*sin_t*sign), decimals=9))

    pts = vecs_to_gmsh_points([v1, v2, v3, v4], chip_z)
    return pts

def make_arc_pts(angle:float, fillet:float):
    sector_angle = np.pi - angle
    intercept = np.abs(fillet * np.tan(sector_angle/2))
    cos_t = np.round(np.cos(sector_angle), decimals=9)
    sin_t = np.round(np.sin(sector_angle), decimals=9)

    p1x = np.round(-intercept, decimals=9)
    p1y = 0
    p2x = np.round(p1x, decimals=9)
    p2y = np.round(p1y + fillet, decimals=9)
    p3x = np.round(intercept * cos_t, decimals=9)
    p3y = np.round(intercept * sin_t, decimals=9)

    v1 = Vec2D(x=p1x, y=p1y)
    v2 = Vec2D(x=p2x, y=p2y)
    v3 = Vec2D(x=p3x, y=p3y)

    return v1, v2, v3

def transform_arc_points(pts:list, translate:Vec2D, path_vecs:list, chip_z:float):
    dim_tags = [(0, p) for p in pts]
    new_pts = [p for p in pts]

    angle1 = path_vecs[0].angle()
    mirror = True if path_vecs[0].cross_prod_sign(path_vecs[1]) < 0 else False

    if mirror:
        # Flip right turn start/end points
        p1 = new_pts.pop(0)
        p4 = new_pts.pop(2)
        new_pts.insert(1, p1)
        new_pts.append(p4)
        gmsh.model.occ.mirror(dim_tags, a=0, b=1, c=0, d=0)

    print(dim_tags, angle1)
    gmsh.model.occ.rotate(dim_tags, x=0, y=0, z=0, ax=0, ay=0, az=1, angle=angle1)
    gmsh.model.occ.translate(dim_tags, translate.x, translate.y, chip_z)
    return new_pts

def draw_curves(recent_pts:list, lines:list, arcs:list):
    rec_pts = []
    lns = []
    acs = []

    # TODO: think of a better error message
    if len(recent_pts) not in [4, 7]:
        raise RuntimeError("Unexpected geometry {len(recent_pts) not in [4,7]}. Check your geometry and retry.")

    l1 = gmsh.model.occ.addLine(recent_pts[0], recent_pts[2])
    l2 = gmsh.model.occ.addLine(recent_pts[1], recent_pts[3])
    lns += [l1, l2]

    if len(recent_pts) == 7:
        a1 = gmsh.model.occ.addCircleArc(recent_pts[2], recent_pts[4], recent_pts[5])
        a2 = gmsh.model.occ.addCircleArc(recent_pts[3], recent_pts[4], recent_pts[6])
        acs += [a1, a2]

    rec_pts = recent_pts[-2:]
    lns += lines
    acs += arcs

    return rec_pts, lns, acs

def render_path_curves(vecs: Vec2DArray, chip_z:float, fillet:float, width:float, straight_line_tol=1e-9):
    recent_pts = [] # To store recent Gmsh points
    lines = [] # To store Gmsh Lines
    arcs = [] # to store Gmsh CircleArcs

    for i,v in enumerate(vecs.points):
        if i == 0:
            p1, p2 = line_width_offset_pts(v, vecs.path_vecs[i], width, chip_z)
            recent_pts += [p1, p2]
            lines += [gmsh.model.occ.addLine(p1, p2)]
            continue

        if i == len(vecs.points)-1:
            p1, p2 = line_width_offset_pts(v, vecs.path_vecs[i-1], width, chip_z)
            recent_pts += [p1, p2]
            lines += [gmsh.model.occ.addLine(p1, p2)]
            continue

        pv1 = vecs.path_vecs[i-1]; pv2 = vecs.path_vecs[i]
        angle12 = vecs.get_angle_between(i-1, i)
        if np.allclose(angle12, np.pi, rtol=straight_line_tol):
            p1, p2 = line_width_offset_pts(v, pv2, width, chip_z)
            recent_pts += [p1, p2]

        else:
            v1, v2, v3 = make_arc_pts(angle12, fillet)
            p1, p2, p4, p5 = arc_width_offset_pts(v1, v3, angle12, width, chip_z)
            p3 = vecs_to_gmsh_points([v2], chip_z)

            new_pts = transform_arc_points([p1, p2, p3, p4, p5], v, [pv1, pv2], chip_z)
            recent_pts += new_pts

        recent_pts, lines, arcs = draw_curves(recent_pts, lines, arcs)

    _, lines, arcs = draw_curves(recent_pts, lines, arcs)

    return lines, arcs