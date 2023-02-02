import gmsh
import sys
import math
import numpy as np

gmsh.initialize(sys.argv)
gmsh.model.add("NACA 0012")

# incidence angle
incidence = -math.pi / 18.;

# create the boundary layer by extrusion, or as a mesh constraint?
by_extrusion = False

# rounded trailing edge?
rounded = True

# base mesh sizes
fact = 1;
lc1 = 0.01 * fact
lc2 = 0.3 * fact

# generate curved mesh?
order2 = False

# xy coordinates of top part of NACA 0012 profile
naca = [0.9987518, 0.0014399, 0.9976658, 0.0015870, 0.9947532, 0.0019938,
        0.9906850, 0.0025595, 0.9854709, 0.0032804, 0.9791229, 0.0041519,
        0.9716559, 0.0051685, 0.9630873, 0.0063238, 0.9534372, 0.0076108,
        0.9427280, 0.0090217, 0.9309849, 0.0105485, 0.9182351, 0.0121823,
        0.9045085, 0.0139143, 0.8898372, 0.0157351, 0.8742554, 0.0176353,
        0.8577995, 0.0196051, 0.8405079, 0.0216347, 0.8224211, 0.0237142,
        0.8035813, 0.0258337, 0.7840324, 0.0279828, 0.7638202, 0.0301515,
        0.7429917, 0.0323294, 0.7215958, 0.0345058, 0.6996823, 0.0366700,
        0.6773025, 0.0388109, 0.6545085, 0.0409174, 0.6313537, 0.0429778,
        0.6078921, 0.0449802, 0.5841786, 0.0469124, 0.5602683, 0.0487619,
        0.5362174, 0.0505161, 0.5120819, 0.0521620, 0.4879181, 0.0536866,
        0.4637826, 0.0550769, 0.4397317, 0.0563200, 0.4158215, 0.0574033,
        0.3921079, 0.0583145, 0.3686463, 0.0590419, 0.3454915, 0.0595747,
        0.3226976, 0.0599028, 0.3003177, 0.0600172, 0.2784042, 0.0599102,
        0.2570083, 0.0595755, 0.2361799, 0.0590081, 0.2159676, 0.0582048,
        0.1964187, 0.0571640, 0.1775789, 0.0558856, 0.1594921, 0.0543715,
        0.1422005, 0.0526251, 0.1257446, 0.0506513, 0.1101628, 0.0484567,
        0.0954915, 0.0460489, 0.0817649, 0.0434371, 0.0690152, 0.0406310,
        0.0572720, 0.0376414, 0.0465628, 0.0344792, 0.0369127, 0.0311559,
        0.0283441, 0.0276827, 0.0208771, 0.0240706, 0.0145291, 0.0203300,
        0.0093149, 0.0164706, 0.0052468, 0.0125011, 0.0023342, 0.0084289,
        0.0005839, 0.0042603, 0.0000000, 0.0000000]

# create profile from points
pts = []
l = len(naca)
for i in range(0, l // 2):
    pts.append(gmsh.model.occ.addPoint(naca[2 * i], naca[2 * i + 1], 0, lc1))
for i in range(l // 2 - 2, -1, -1):
    pts.append(gmsh.model.occ.addPoint(naca[2 * i], -naca[2 * i + 1], 0, lc1))
pts.reverse()
curv = []
curv.append(gmsh.model.occ.addSpline(pts))

if rounded:
    # circle as trailing edge
    c = gmsh.model.occ.addPoint(0.9985510, 0.0000000, 0, lc1)
    curv.append(gmsh.model.occ.addCircleArc(pts[-1], c, pts[0]))
else:
    pt = gmsh.model.occ.addPoint(1.0095, 0.0000000, 0, lc1)
    curv.append(gmsh.model.occ.addLine(pts[-1], pt))
    curv.append(gmsh.model.occ.addLine(pt, pts[0]))

# rotate the profile
gmsh.model.occ.rotate([(1, c) for c in curv], 0.25, 0, 0, 0, 0, 1, incidence)

cl = gmsh.model.occ.addCurveLoop(curv)

if by_extrusion:
    gmsh.model.occ.synchronize()
    # a boundary layer can be created through extrusion using the built-in CAD
    # kernel: this creates topological entities that will be filled with a
    # discrete geometry (a mesh extruded along the boundary normals) during mesh
    # generation
    N = 10 # number of layers
    r = 2 # ratio
    d = [-1.7e-5] # thickness of first layer
    for i in range(1, N): d.append(d[-1] - (-d[0]) * r**i)
    print(d)
    extbl = gmsh.model.geo.extrudeBoundaryLayer(gmsh.model.getEntities(1),
                                                [1] * N, d, True)

    # create curve loop with "top" curves of the boundary layer
    cl2 = gmsh.model.geo.addCurveLoop([c[1] for c in extbl[::2]])

    # connect it with the exterior surface
    p1 = gmsh.model.geo.addPoint(-1, -1, 0, lc2)
    p2 = gmsh.model.geo.addPoint(2, -1, 0, lc2)
    p3 = gmsh.model.geo.addPoint(2, 1, 0, lc2)
    p4 = gmsh.model.geo.addPoint(-1, 1, 0, lc2)
    l1 = gmsh.model.geo.addLine(p1, p2)
    l2 = gmsh.model.geo.addLine(p2, p3)
    l3 = gmsh.model.geo.addLine(p3, p4)
    l4 = gmsh.model.geo.addLine(p4, p1)
    cl3 = gmsh.model.geo.addCurveLoop([l1, l2, l3, l4])
    s2 = gmsh.model.geo.addPlaneSurface([cl3, cl2])
    gmsh.model.geo.synchronize()

else:
    # in 2D, boundary layers can also be specified as a meshing constraint,
    # through the BoundaryLayer field; this is quite a bit more general, as it
    # handles intersections between several boundary layers, fans, etc.
    p1 = gmsh.model.occ.addPoint(-1, -1, 0, lc2)
    p2 = gmsh.model.occ.addPoint(2, -1, 0, lc2)
    p3 = gmsh.model.occ.addPoint(2, 1, 0, lc2)
    p4 = gmsh.model.occ.addPoint(-1, 1, 0, lc2)
    l1 = gmsh.model.occ.addLine(p1, p2)
    l2 = gmsh.model.occ.addLine(p2, p3)
    l3 = gmsh.model.occ.addLine(p3, p4)
    l4 = gmsh.model.occ.addLine(p4, p1)
    cl2 = gmsh.model.occ.addCurveLoop([l1, l2, l3, l4])
    s = gmsh.model.occ.addPlaneSurface([cl2, cl])
    gmsh.model.occ.synchronize()

    f = gmsh.model.mesh.field.add('BoundaryLayer')
    gmsh.model.mesh.field.setNumbers(f, 'CurvesList', curv)
    gmsh.model.mesh.field.setNumber(f, 'Size', 1.7e-5)
    gmsh.model.mesh.field.setNumber(f, 'Ratio', 2)
    gmsh.model.mesh.field.setNumber(f, 'Quads', 1)
    gmsh.model.mesh.field.setNumber(f, 'Thickness', 0.01)
    if not rounded:
        # create a fan at the trailing edge
        gmsh.option.setNumber('Mesh.BoundaryLayerFanElements', 7)
        gmsh.model.mesh.field.setNumbers(f, 'FanPointsList', [pt])

    gmsh.model.mesh.field.setAsBoundaryLayer(f)

# generate the mesh
gmsh.model.mesh.generate(2)

# 2nd order + fast curving of the boundary layer + optimization
if order2:
    gmsh.model.mesh.setOrder(2)
    gmsh.model.mesh.optimize('HighOrderFastCurving')
    gmsh.model.mesh.optimize('HighOrder')

gmsh.write('naca_boundary_layer_2d.msh')

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
