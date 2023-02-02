# This script takes an STL triangulation and creates a brep with a plane surface
# for each triangle

import gmsh
import sys
import os
import numpy as np

if len(sys.argv) < 2:
    print('usage: {} file.stl'.format(sys.argv[0]))
    exit(0)

gmsh.initialize()

# load the STL mesh and retrieve the element, node and edge data
gmsh.open(sys.argv[1])
typ = 2 # 3-node triangles
elementTags, elementNodes = gmsh.model.mesh.getElementsByType(typ)
nodeTags, nodeCoord, _ = gmsh.model.mesh.getNodesByElementType(typ)
edgeNodes = gmsh.model.mesh.getElementEdgeNodes(typ)

# create a new model to store the BREP
gmsh.model.add('my brep')

# create a geometrical point for each mesh node
nodes = dict(zip(nodeTags, np.reshape(nodeCoord, (len(nodeTags), 3))))
for n in nodes.items():
    gmsh.model.occ.addPoint(n[1][0], n[1][1], n[1][2], tag=n[0])

# create a geometrical plane surface for each (triangular) element
allsurfaces = []
allcurves = {}
elements = dict(zip(elementTags, np.reshape(edgeNodes, (len(elementTags), 3, 2))))

print("... creating {} surfaces".format(len(elements)))
for e in elements.items():
    curves = []
    for edge in e[1]:
        ed = tuple(np.sort(edge))
        if ed not in allcurves:
            t = gmsh.model.occ.addLine(edge[0], edge[1])
            allcurves[ed] = t
        else:
            t = allcurves[ed]
        curves.append(t)
    cl = gmsh.model.occ.addCurveLoop(curves)
    allsurfaces.append(gmsh.model.occ.addPlaneSurface([cl]))

gmsh.model.occ.synchronize()

# if the surfaces form a closed shell, create a volume
if len(allsurfaces) > 0:
    bnd = gmsh.model.getBoundary(gmsh.model.getEntities(2))
    if len(bnd) == 0:
        print("... creating volume")
        sl = gmsh.model.occ.addSurfaceLoop(allsurfaces)
        gmsh.model.occ.addVolume([sl])

print("... done!")

gmsh.write(os.path.splitext(sys.argv[1])[0] + ".brep")

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
