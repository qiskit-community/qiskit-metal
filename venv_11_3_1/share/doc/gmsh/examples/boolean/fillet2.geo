SetFactory("OpenCASCADE");

Mesh.MeshSizeMin = 1;
Mesh.MeshSizeMax = 1;

a() = ShapeFromFile("component8.step");

f() = Abs(Boundary{ Volume{a()}; });
e() = Unique(Abs(Boundary{ Surface{f()}; }));

Fillet{a()}{e()}{1}
