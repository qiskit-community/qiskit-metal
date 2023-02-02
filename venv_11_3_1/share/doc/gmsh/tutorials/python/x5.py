# -----------------------------------------------------------------------------
#
#  Gmsh Python extended tutorial 5
#
#  Additional geometrical data: parametrizations, normals, curvatures
#
# -----------------------------------------------------------------------------

import gmsh
import sys
import math

gmsh.initialize(sys.argv)

# The API provides access to geometrical data in a CAD kernel agnostic manner.

# Let's create a simple CAD model by fusing a sphere and a cube, then mesh the
# surfaces:
gmsh.model.add("x5")
s = gmsh.model.occ.addSphere(0, 0, 0, 1)
b = gmsh.model.occ.addBox(0.5, 0, 0, 1.3, 2, 3)
gmsh.model.occ.fuse([(3, s)], [(3, b)])
gmsh.model.occ.synchronize()
gmsh.model.mesh.generate(2)

# We can for example retrieve the exact normals and the curvature at all the
# mesh nodes (i.e. not normals and curvatures computed from the mesh, but
# directly evaluated on the geometry), by querying the CAD kernels at the
# corresponding parametric coordinates.
normals = []
curvatures = []

# For each surface in the model:
for e in gmsh.model.getEntities(2):
    # Retrieve the surface tag
    s = e[1]

    # Get the mesh nodes on the surface, including those on the boundary
    # (contrary to internal nodes, which store their parametric coordinates,
    # boundary nodes will be reparametrized on the surface in order to compute
    # their parametric coordinates, the result being different when
    # reparametrized on another adjacent surface)
    tags, coord, param = gmsh.model.mesh.getNodes(2, s, True)

    # Get the surface normals on all the points on the surface corresponding to
    # the parametric coordinates of the nodes
    norm = gmsh.model.getNormal(s, param)

    # In the same way, get the curvature
    curv = gmsh.model.getCurvature(2, s, param)

    # Store the normals and the curvatures so that we can display them as
    # list-based post-processing views
    for i in range(0, len(coord), 3):
        normals.append(coord[i])
        normals.append(coord[i + 1])
        normals.append(coord[i + 2])
        normals.append(norm[i])
        normals.append(norm[i + 1])
        normals.append(norm[i + 2])
        curvatures.append(coord[i])
        curvatures.append(coord[i + 1])
        curvatures.append(coord[i + 2])
        curvatures.append(curv[i // 3])

# Create a list-based vector view on points to display the normals, and a scalar
# view on points to display the curvatures
vn = gmsh.view.add("normals")
gmsh.view.addListData(vn, "VP", len(normals) // 6, normals)
vc = gmsh.view.add("curvatures")
gmsh.view.addListData(vc, "SP", len(curvatures) // 4, curvatures)

# We can also retrieve the parametrization bounds of model entities, e.g. of
# curve 5, and evaluate the parametrization for several parameter values:
bounds = gmsh.model.getParametrizationBounds(1, 5)
N = 20
t = [bounds[0][0] + i * (bounds[1][0] - bounds[0][0]) / N for i in range(N)]
xyz1 = gmsh.model.getValue(1, 5, t)

# We can also reparametrize curve 5 on surface 1, and evaluate the points in the
# parametric plane of the surface:
uv = gmsh.model.reparametrizeOnSurface(1, 5, t, 1)
xyz2 = gmsh.model.getValue(2, 1, uv)

# Hopefully we get the same x, y, z coordinates!
if max([abs(a - b) for (a, b) in zip(xyz1, xyz2)]) < 1e-12:
    gmsh.logger.write('Evaluation on curve and surface match!')
else:
    gmsh.logger.write('Evaluation on curve and surface do not match!', 'error')

# Launch the GUI to see the results:
if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
