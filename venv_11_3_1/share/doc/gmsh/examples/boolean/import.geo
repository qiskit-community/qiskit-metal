SetFactory("OpenCASCADE");

Mesh.MeshSizeMin = 3;
Mesh.MeshSizeMax = 3;

DefineConstant[
  z = {16, Name "Parameters/z position of box"}
  sph = {0, Choices{0,1}, Name "Parameters/Add sphere?"}
];

a() = ShapeFromFile("component8.step");

b() = 2;
Box(b(0)) = {0,156,z, 10,14,10};

If(sph)
  b() += 3;
  Sphere(b(1)) = {0,150,0, 20};
EndIf


r() = BooleanFragments{ Volume{a(),b()}; Delete; }{};

//Recursive Color SteelBlue { Volume{r()}; }

Save "merged.brep";

Physical Volume("Combined volume", 1) = {r()};
Physical Surface("Combined boundary", 2) = CombinedBoundary{ Volume{r()}; };
