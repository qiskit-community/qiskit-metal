# Contributed by Roberto Agromayor

import gmsh
import sys
import numpy as np

gmsh.initialize()

# Set a target mesh size
lc = 2e-2

# Define the south B-Spline curve
a = 0.25
P1  = gmsh.model.occ.addPoint(0.00, 0.00, 0.00, lc)
P2  = gmsh.model.occ.addPoint(0.33, 0.00 + a, 0.00 + a, lc)
P3  = gmsh.model.occ.addPoint(0.66, 0.00 - a, 0.00 + a, lc)
P4  = gmsh.model.occ.addPoint(1.00, 0.00, 0.00, lc)
C1 = gmsh.model.occ.addBSpline([P1, P2, P3, P4], degree=3)

# Define the north B-Spline curve
P5  = gmsh.model.occ.addPoint(0.00, 1.00, 0.00, lc)
P6  = gmsh.model.occ.addPoint(0.33, 1.00 - a, 0.00 - a, lc)
P7  = gmsh.model.occ.addPoint(0.66, 1.00 + a, 0.00 - a, lc)
P8  = gmsh.model.occ.addPoint(1.00, 1.00, 0.00, lc)
C2 = gmsh.model.occ.addBSpline([P5, P6, P7, P8], degree=3)

# Define the east B-Spline curve
P9 = gmsh.model.occ.addPoint(0.00-a, 0.50, 0.00 + a, lc)
C3 = gmsh.model.occ.addBSpline([P1,P9, P5], degree=2)

# Define the west B-Spline curve
P10 = gmsh.model.occ.addPoint(1.00+a, 0.50, 0.00 - a, lc)
C4 = gmsh.model.occ.addBSpline([P4, P10, P8], degree=3)

# Create a BSpline surface filling the 4 curves:
W1 = gmsh.model.occ.addWire([C1, C3, C2, C4])

# gmsh.model.occ.addBSplineFilling(W1, type="Stretch")
gmsh.model.occ.addBSplineFilling(W1, type="Curved")
# gmsh.model.occ.addBSplineFilling(W1, type="Coons") # fails...

# Synchronize the CAD model
gmsh.model.occ.synchronize()

# Show the model
if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

# Exit gmsh API
gmsh.finalize()
