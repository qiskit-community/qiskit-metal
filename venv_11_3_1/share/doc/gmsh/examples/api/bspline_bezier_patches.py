import gmsh
import sys

gmsh.initialize()

gmsh.model.occ.addPoint(0.1,0,-0.1)
gmsh.model.occ.addPoint(1,0,0)
gmsh.model.occ.addPoint(2,0,0)
gmsh.model.occ.addPoint(3,0,0)
gmsh.model.occ.addPoint(4,0,0)
gmsh.model.occ.addPoint(0.1,1,0.1)
gmsh.model.occ.addPoint(1,1,0)
gmsh.model.occ.addPoint(2,1,0)
gmsh.model.occ.addPoint(3,1,0)
gmsh.model.occ.addPoint(4,1,0)
gmsh.model.occ.addPoint(0,2,0.2)
gmsh.model.occ.addPoint(1,2,0)
gmsh.model.occ.addPoint(2,2,1.5)
gmsh.model.occ.addPoint(3,2,0)
gmsh.model.occ.addPoint(4,2,0)
gmsh.model.occ.addPoint(0,3,0.1)
gmsh.model.occ.addPoint(1,3,0)
gmsh.model.occ.addPoint(2,3,0)
gmsh.model.occ.addPoint(3,3,0)
gmsh.model.occ.addPoint(4,3,0)

gmsh.model.occ.addPoint(0.1,0,-0.1)
gmsh.model.occ.addPoint(-1,0,0)
gmsh.model.occ.addPoint(-2,0,0)
gmsh.model.occ.addPoint(-3,0,0)
gmsh.model.occ.addPoint(-4,0,0)
gmsh.model.occ.addPoint(0.1,1,0.1)
gmsh.model.occ.addPoint(-1,1,0)
gmsh.model.occ.addPoint(-2,1,0)
gmsh.model.occ.addPoint(-3,1,0)
gmsh.model.occ.addPoint(-4,1,0)
gmsh.model.occ.addPoint(0,2,0.2)
gmsh.model.occ.addPoint(-1,2,0)
gmsh.model.occ.addPoint(-2,2,1.5)
gmsh.model.occ.addPoint(-3,2,0)
gmsh.model.occ.addPoint(-4,2,0)
gmsh.model.occ.addPoint(0,3,0.1)
gmsh.model.occ.addPoint(-1,3,0)
gmsh.model.occ.addPoint(-2,3,0)
gmsh.model.occ.addPoint(-3,3,0)
gmsh.model.occ.addPoint(-4,3,0)

bezier = False
bezier = True

if bezier:
    gmsh.model.occ.addBezierSurface(range(1,21), 5)
    gmsh.model.occ.addBezierSurface(range(21,41), 5)
else:
    gmsh.model.occ.addBSplineSurface(range(1,21), 5)
    gmsh.model.occ.addBSplineSurface(range(21,41), 5)


# 3 methods to glue the 2 patches
method = 1

if method == 1:
    # healShapes performs surface sewing, which does the job; it will also
    # reorient the left patch so that its normal points along +z
    gmsh.model.occ.healShapes()

elif method == 2:
    # we can also fragment; here we also include points so that the original
    # corner points will be used as corners of the patches
    gmsh.model.occ.fragment(gmsh.model.occ.getEntities(0),
                            gmsh.model.occ.getEntities(2))

elif method == 3:
    # this is the same as fragment, but just on the 2 surfaces
    gmsh.model.occ.removeAllDuplicates()

gmsh.model.occ.synchronize()

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
