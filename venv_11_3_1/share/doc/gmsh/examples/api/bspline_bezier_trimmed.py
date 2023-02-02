import gmsh
import sys

gmsh.initialize(sys.argv)

gmsh.model.occ.addPoint(0.1,0,0.75)
gmsh.model.occ.addPoint(1,0,0.65)
gmsh.model.occ.addPoint(2,0,0.5)
gmsh.model.occ.addPoint(3,0,0.2)
gmsh.model.occ.addPoint(4,0,0)

gmsh.model.occ.addPoint(0.1,1,0.1)
gmsh.model.occ.addPoint(1,1,0)
gmsh.model.occ.addPoint(2,1,0)
gmsh.model.occ.addPoint(3,1,0)
gmsh.model.occ.addPoint(4,1,0)

gmsh.model.occ.addPoint(0,2,0.2)
gmsh.model.occ.addPoint(1,2,0)
gmsh.model.occ.addPoint(2,2,0.1)
gmsh.model.occ.addPoint(3,2,0)
gmsh.model.occ.addPoint(4,2,0)

gmsh.model.occ.addPoint(0,3,0.1)
gmsh.model.occ.addPoint(1,3,0)
gmsh.model.occ.addPoint(2,3,0)
gmsh.model.occ.addPoint(3,3,0)
gmsh.model.occ.addPoint(4,3,0)

c=gmsh.model.occ.addCircle(0.5,0.5,0, 0.4)
w=gmsh.model.occ.addWire([c])

c2=gmsh.model.occ.addCircle(0.5,0.5,0, 0.2)
w2=gmsh.model.occ.addWire([c2])

# with use3d=True, project the 3D curves on the patch; with use3d=False, use the
# x,y coordinates of the curves as the parametric coordinates of the patch
use3d = True
use3d = False

gmsh.model.occ.addBSplineSurface(range(1,21), 5, wireTags=[w,w2], wire3D=use3d)

#gmsh.model.occ.addBezierSurface(range(1,21), 5, wireTags=[w], wire3D=use3d)

gmsh.model.occ.synchronize()

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
