import gmsh
import math
import os
import sys

gmsh.initialize(sys.argv)

path = os.path.dirname(os.path.abspath(__file__))

# load an STL surface
gmsh.merge(os.path.join(path, 'terrain_stl_data.stl'))

# classify the surface mesh according to given angle, and create discrete model
# entities (surfaces, curves and points) accordingly; curveAngle forces bounding
# curves to be split on sharp corners
gmsh.model.mesh.classifySurfaces(math.pi, curveAngle=math.pi / 3)

# create a geometry for the discrete curves and surfaces
gmsh.model.mesh.createGeometry()

# retrieve the surface, its boundary curves and corner points
s = gmsh.model.getEntities(2)
c = gmsh.model.getBoundary(s)

if (len(c) != 4):
    gmsh.logger.write('Should have 4 boundary curves!', level='error')

z = -1000

p = []
xyz = []
for e in c:
    pt = gmsh.model.getBoundary([e], combined=False)
    p.extend([pt[0][1]])
    xyz.extend(gmsh.model.getValue(0, pt[0][1], []))

# create other CAD entities to form one volume below the terrain surface; beware
# that only built-in CAD entities can be hybrid, i.e. have discrete entities on
# their boundary: OpenCASCADE does not support this feature
p1 = gmsh.model.geo.addPoint(xyz[0], xyz[1], z)
p2 = gmsh.model.geo.addPoint(xyz[3], xyz[4], z)
p3 = gmsh.model.geo.addPoint(xyz[6], xyz[7], z)
p4 = gmsh.model.geo.addPoint(xyz[9], xyz[10], z)

c1 = gmsh.model.geo.addLine(p1, p2)
c2 = gmsh.model.geo.addLine(p2, p3)
c3 = gmsh.model.geo.addLine(p3, p4)
c4 = gmsh.model.geo.addLine(p4, p1)

c10 = gmsh.model.geo.addLine(p1, p[0])
c11 = gmsh.model.geo.addLine(p2, p[1])
c12 = gmsh.model.geo.addLine(p3, p[2])
c13 = gmsh.model.geo.addLine(p4, p[3])

ll1 = gmsh.model.geo.addCurveLoop([c1, c2, c3, c4])
s1 = gmsh.model.geo.addPlaneSurface([ll1])

ll3 = gmsh.model.geo.addCurveLoop([c1, c11, -c[0][1], -c10])
s3 = gmsh.model.geo.addPlaneSurface([ll3])
ll4 = gmsh.model.geo.addCurveLoop([c2, c12, -c[1][1], -c11])
s4 = gmsh.model.geo.addPlaneSurface([ll4])
ll5 = gmsh.model.geo.addCurveLoop([c3, c13, -c[2][1], -c12])
s5 = gmsh.model.geo.addPlaneSurface([ll5])
ll6 = gmsh.model.geo.addCurveLoop([c4, c10, -c[3][1], -c13])
s6 = gmsh.model.geo.addPlaneSurface([ll6])
sl1 = gmsh.model.geo.addSurfaceLoop([s1, s3, s4, s5, s6, s[0][1]])
v1 = gmsh.model.geo.addVolume([sl1])

gmsh.model.geo.synchronize()

# set this to True to build a fully hex mesh
#transfinite = True
transfinite = False

if transfinite:
    NN = 30
    for c in gmsh.model.getEntities(1):
        gmsh.model.mesh.setTransfiniteCurve(c[1], NN)
    for s in gmsh.model.getEntities(2):
        gmsh.model.mesh.setTransfiniteSurface(s[1])
        gmsh.model.mesh.setRecombine(s[0], s[1])
        gmsh.model.mesh.setSmoothing(s[0], s[1], 100)
    gmsh.model.mesh.setTransfiniteVolume(v1)
else:
    gmsh.option.setNumber('Mesh.MeshSizeMin', 100)
    gmsh.option.setNumber('Mesh.MeshSizeMax', 100)

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
