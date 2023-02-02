import gmsh
import sys

# small example showing how the api can be used to compute the neighbours (by a
# face) of all tets in the mesh

gmsh.initialize(sys.argv)

gmsh.model.add("my test model")
gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
gmsh.model.occ.synchronize()
gmsh.model.mesh.generate(3)

print("--- getting tets and face nodes")
tets, _ = gmsh.model.mesh.getElementsByType(4)
fnodes = gmsh.model.mesh.getElementFaceNodes(4, 3)

print("--- computing face x tet incidence")
faces = []
fxt = {}
for i in range(0, len(fnodes), 3):
    f = tuple(sorted(fnodes[i:i + 3]))
    faces.append(f)
    t = tets[i // 12]
    if not f in fxt:
        fxt[f] = [t]
    else:
        fxt[f].append(t)

print("--- computing neighbors by face")
txt = {}
for i in range(0, len(faces)):
    f = faces[i]
    t = tets[i // 4]
    if not t in txt:
        txt[t] = set()
    for tt in fxt[f]:
        if tt != t:
            txt[t].add(tt)

print("--- done: neighbors by face =", txt)

gmsh.finalize()
