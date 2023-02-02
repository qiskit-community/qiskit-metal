import gmsh
import sys

# script showing how a mesh can be modified (here setting all z coordinates of
# nodes to 0) by getting the mesh, performing a modification, and storing the
# modified mesh in the same model.

# (The approach followed here is overkill to # just change node coordinates of
# course - if you merely want to change coordinates see `flatten2.py' instead.)

if len(sys.argv) < 2:
    print("Usage: " + sys.argv[0] + " file.msh")
    exit(0)

gmsh.initialize()
gmsh.open(sys.argv[1])

nodeTags = {}
nodeCoords = {}
elementTypes = {}
elementTags = {}
elementNodeTags = {}

entities = gmsh.model.getEntities()

# get the nodes and elements
for e in entities:
    nodeTags[e], nodeCoords[e], _ = gmsh.model.mesh.getNodes(e[0], e[1])
    elementTypes[e], elementTags[e], elementNodeTags[e] = gmsh.model.mesh.getElements(e[0], e[1])

# delete the mesh
gmsh.model.mesh.clear()

# store new mesh
for e in entities:
    for i in range(2, len(nodeCoords[e]), 3):
        nodeCoords[e][i] = 0
    gmsh.model.mesh.addNodes(e[0], e[1], nodeTags[e], nodeCoords[e])
    gmsh.model.mesh.addElements(e[0], e[1], elementTypes[e], elementTags[e],
                                elementNodeTags[e])

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

#gmsh.write('flat.msh')

gmsh.finalize()
