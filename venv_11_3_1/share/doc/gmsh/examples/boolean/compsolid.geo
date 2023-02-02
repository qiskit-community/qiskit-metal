SetFactory("OpenCASCADE");

//Mesh.Algorithm = 6;
Mesh.MeshSizeMin = 0.2;
Mesh.MeshSizeMax = 0.2;

DefineConstant[
  x = {0, Min -5, Max 5, Step 0.1, Name "Bloc 1/0x"}
  y = {0, Min -5, Max 5, Step 0.1, Name "Bloc 1/0y"}
  z = {0, Min -5, Max 5, Step 0.1, Name "Bloc 1/0z"}
  dx = {2, Min 0.1, Max 5, Step 0.1, Name "Bloc 1/dx"}
  dy = {2, Min 0.1, Max 5, Step 0.1, Name "Bloc 1/dy"}
  dz = {2, Min 0.1, Max 5, Step 0.1, Name "Bloc 1/dz"}
  x2 = {x+dx, Min -5, Max 5, Step 0.1, Name "Bloc 2/0x"}
  y2 = {0, Min -5, Max 5, Step 0.1, Name "Bloc 2/0y"}
  z2 = {0, Min -5, Max 5, Step 0.1, Name "Bloc 2/0z"}
  dx2 = {1, Min 0.1, Max 5, Step 0.1, Name "Bloc 2/dx"}
  dy2 = {1, Min 0.1, Max 5, Step 0.1, Name "Bloc 2/dy"}
  dz2 = {3, Min 0.1, Max 5, Step 0.1, Name "Bloc 2/dz"}
];

Box(1) = {x,y,z, dx,dy,dz};
Box(2) = {x2,y2,z2, dx2,dy2,dz2};

f() = BooleanFragments { Volume{1,2}; Delete; }{};

Printf("Resulting elementary entities:");
For i In {0:#f()-1}
  Printf("- volume %g", f(i));
  b() = Boundary{ Volume{f(i)}; };
  Printf("    surfaces", b());
EndFor

Physical Volume(1) = {1};
Physical Volume(2) = {2};
