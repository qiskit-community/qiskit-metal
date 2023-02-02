import gmsh
import math
import sys

gmsh.initialize(sys.argv)

gmsh.model.add("terrain")

# create the terrain surface from N x N input data points (here simulated using
# a simple function):
N = 100
ps = []

# create a bspline surface
for i in range(N + 1):
    for j in range(N + 1):
        ps.append(gmsh.model.occ.addPoint(float(i) / N, float(j) / N,
                                          0.05 * math.sin(10 * float(i + j) / N)))
s = gmsh.model.occ.addBSplineSurface(ps, numPointsU=N+1)

# create a box
v = gmsh.model.occ.addBox(0, 0, -0.5, 1, 1, 1)

# fragment the box with the bspline surface
gmsh.model.occ.fragment([(2, s)], [(3, v)])
gmsh.model.occ.synchronize()

# define a parameter to select the mesh type interactively
gmsh.onelab.set("""[
  {
    "type":"number",
    "name":"Parameters/Full-hex mesh?",
    "values":[0],
    "choices":[0, 1]
  }
]""")

def setMeshConstraint():
    if gmsh.onelab.getNumber('Parameters/Full-hex mesh?')[0] == 1:
        NN = 30
        for c in gmsh.model.getEntities(1):
            gmsh.model.mesh.setTransfiniteCurve(c[1], NN)
            for s in gmsh.model.getEntities(2):
                gmsh.model.mesh.setTransfiniteSurface(s[1])
                gmsh.model.mesh.setRecombine(s[0], s[1])
                gmsh.model.mesh.setSmoothing(s[0], s[1], 100)
        gmsh.model.mesh.setTransfiniteVolume(1)
        gmsh.model.mesh.setTransfiniteVolume(2)
    else:
        gmsh.model.mesh.removeConstraints()
        gmsh.option.setNumber('Mesh.MeshSizeMin', 0.05)
        gmsh.option.setNumber('Mesh.MeshSizeMax', 0.05)

def checkForEvent():
    action = gmsh.onelab.getString("ONELAB/Action")
    if len(action) and action[0] == "check":
        gmsh.onelab.setString("ONELAB/Action", [""])
        setMeshConstraint()
    return 1

setMeshConstraint()

if "-nopopup" not in sys.argv:
    gmsh.fltk.initialize()
    while gmsh.fltk.isAvailable() and checkForEvent():
        gmsh.fltk.wait()

gmsh.finalize()
