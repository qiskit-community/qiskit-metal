import gmsh
import sys

gmsh.initialize()
gmsh.option.setNumber('Mesh.MeshSizeMin', 0.02)
gmsh.option.setNumber('Mesh.MeshSizeMax', 0.02)
gmsh.model.occ.addPoint(-0.8, 0.1, -0.2, 1)
gmsh.model.occ.addPoint(-0.5, 0.1, -0.2, 2)
gmsh.model.occ.addPoint(-0.6, 0, -0.1, 3)
gmsh.model.occ.addPoint(-0.7, -0, -0.1, 4)
gmsh.model.occ.addPoint(-0.7, 0.2, -0.2, 5)
gmsh.model.occ.addPoint(-0.6, 0.1, -0.1, 6)
gmsh.model.occ.addSpline([1, 5, 2], 1)
gmsh.model.occ.addSpline([2, 6, 3], 2)
gmsh.model.occ.addSpline([3, 4, 1], 3)
gmsh.model.occ.addCurveLoop([1, 2, 3], 1)

# Bspline surface bounded by curve loop 1, constructed by optimization
gmsh.model.occ.addSurfaceFilling(1, 1)

# BSpline filling (try "Stretch" or "Curved")
gmsh.model.occ.addBSplineFilling(1, 2, 'Curved')

# Bezier filling - can be used if all bounding curves are Bezier curves
# gmsh.model.occ.addBezierFilling(1, 3)

# Same as 1, but passing through points 7 and 8
gmsh.model.occ.addPoint(-0.7, 0.1, -0.2, 7)
gmsh.model.occ.addPoint(-0.67, 0.1, -0.2, 8)
gmsh.model.occ.addSurfaceFilling(1, 4, [7, 8])

gmsh.model.occ.synchronize()

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
