import gmsh
import sys

gmsh.initialize()
gmsh.model.occ.addSphere(0,0,0,1, 10)
gmsh.model.occ.addBox(0.5,0,0,1.3,2,4, 11)
gmsh.model.occ.fragment([(3,10)], [(3,11)])
gmsh.model.occ.synchronize()

dim = 2
tag = 6 # 1
N = 20

bnd = gmsh.model.getBoundary([(dim, tag)], combined=False)
for c in bnd:
    print(c)
    bounds = gmsh.model.getParametrizationBounds(c[0], abs(c[1]))
    t = [bounds[0][0] + i * (bounds[1][0] - bounds[0][0]) / N for i in range(N)]
    uv = gmsh.model.reparametrizeOnSurface(1, abs(c[1]), t, tag)
    xyz = gmsh.model.getValue(dim,tag,uv)
    for i in range(0, len(xyz), 3):
        p = gmsh.model.addDiscreteEntity(0)
        gmsh.model.setCoordinates(p, xyz[i], xyz[i+1], xyz[i+2])

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()
gmsh.finalize()
