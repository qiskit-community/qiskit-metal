# See the corresponding Python tutorial for detailed comments.

import gmsh

gmsh.initialize()

gmsh.model.add("t16")

gmsh.model.occ.addBox(0,0,0, 1,1,1, 1)
gmsh.model.occ.addBox(0,0,0, 0.5,0.5,0.5, 2)
gmsh.model.occ.cut([(3,1)], [(3,2)], 3)

x = 0; y = 0.75; z = 0; r = 0.09

holes = []
for t in 1:5
    global x, z
    x += 0.166
    z += 0.166
    gmsh.model.occ.addSphere(x,y,z,r, 3 + t)
    t = (3, 3 + t)
    push!(holes, t)
end

ov = gmsh.model.occ.fragment([(3,3)], holes)
gmsh.model.occ.synchronize()

lcar1 = .1
lcar2 = .0005
lcar3 = .055

ov = gmsh.model.getEntities(0);
gmsh.model.mesh.setSize(ov, lcar1);

ov = gmsh.model.getBoundary(holes, false, false, true);
gmsh.model.mesh.setSize(ov, lcar3);

eps = 1e-3
ov = gmsh.model.getEntitiesInBoundingBox(0.5-eps, 0.5-eps, 0.5-eps,
                                         0.5+eps, 0.5+eps, 0.5+eps, 0)
gmsh.model.mesh.setSize(ov, lcar2)

gmsh.model.mesh.generate(3)

gmsh.write("t16.msh")

if !("-nopopup" in ARGS)
    gmsh.fltk.run()
end

gmsh.finalize()
