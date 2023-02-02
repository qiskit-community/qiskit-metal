import gmsh
import sys

gmsh.initialize(sys.argv)

tri1 = [0., 1., 1., 0., 0., 1., 0., 0., 0.]
tri2 = [0., 1., 0., 0., 1., 1., 0., 0., 0.]

for step in range(0, 10):
    tri1.append(10.)
    tri1.append(10.)
    tri1.append(12. + step)
    tri2.append(10.)
    tri2.append(12. + step)
    tri2.append(13. + step)

t = gmsh.view.add("some data")
gmsh.view.addListData(t, "ST", 1, tri1)

t2 = gmsh.view.add("some other data")
gmsh.view.addListData(t2, "ST", 1, tri2)

gmsh.view.combine("elements", "all", remove = False)

# gmsh.view.write(t, "data.pos")

gmsh.view.addAlias(t)

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
