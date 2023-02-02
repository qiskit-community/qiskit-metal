import gmsh
import sys
import math
import numpy as np

gmsh.initialize(sys.argv)
gmsh.model.add("Tube boundary layer")

# meshing constraints
gmsh.option.setNumber("Mesh.MeshSizeMax", 0.1)
order2 = False

# fuse 2 cylinders and only keep outside shell
c1 = gmsh.model.occ.addCylinder(0,0,0, 5,0,0, 0.5)
c2 = gmsh.model.occ.addCylinder(2,0,-2, 0,0,2, 0.3)
s = gmsh.model.occ.fuse([(3, c1)], [(3, c2)])
gmsh.model.occ.remove(gmsh.model.occ.getEntities(3))
gmsh.model.occ.remove([(2,2), (2,3), (2,5)]) # fixme: automate this
gmsh.model.occ.synchronize()

# create boundary layer extrusion, and make extrusion only return "top" surfaces
# and volumes, not lateral surfaces
gmsh.option.setNumber('Geometry.ExtrudeReturnLateralEntities', 0)
n = np.linspace(1, 1, 5)
d = np.logspace(-3, -1, 5)
e = gmsh.model.geo.extrudeBoundaryLayer(gmsh.model.getEntities(2),
                                        n, -d, True)

# get "top" surfaces created by extrusion
top_ent = [s for s in e if s[0] == 2]
top_surf = [s[1] for s in top_ent]

# get boundary of top surfaces, i.e. boundaries of holes
gmsh.model.geo.synchronize()
bnd_ent = gmsh.model.getBoundary(top_ent)
bnd_curv = [c[1] for c in bnd_ent]

# create plane surfaces filling the holes
loops = gmsh.model.geo.addCurveLoops(bnd_curv)
for l in loops:
    top_surf.append(gmsh.model.geo.addPlaneSurface([l]))

# create the inner volume
gmsh.model.geo.addVolume([gmsh.model.geo.addSurfaceLoop(top_surf)])
gmsh.model.geo.synchronize()

# generate the mesh
gmsh.model.mesh.generate(3)

# 2nd order + fast curving of the boundary layer
if order2:
    gmsh.model.mesh.setOrder(2)
    gmsh.model.mesh.optimize('HighOrderFastCurving')

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
