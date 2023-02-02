SetFactory("OpenCASCADE");

Mesh.MeshSizeMin = 0.1;
Mesh.MeshSizeMax = 0.1;

Box(1) = {0,0,0,1,1,1};
f() = Abs(Boundary{ Volume{1}; });
e() = Unique(Abs(Boundary{ Surface{f()}; }));

Fillet{1}{e()}{0.2}
