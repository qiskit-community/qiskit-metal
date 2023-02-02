SetFactory("OpenCASCADE");

//Mesh.Algorithm = 6;
Mesh.MeshSizeMin = 0.2;
Mesh.MeshSizeMax = 0.2;

DefineConstant[
  sph = {0, Choices{0,1}, Name "Make sphere a single volume"}
  xx = {2.2, Min -1, Max 5, Step 0.01, Name "Sphere position"}
  rr = {0.5, Min 0.1, Max 3, Step 0.01, Name "Sphere radius"}
];


Box(1) = {0,0,0, 2,2,2};
Sphere(2) = {xx, 1, 1, rr};
Box(3) = {2,0,0, 2,2,2};

f() = BooleanFragments { Volume{1:3}; Delete; }{};
Printf("f()", f());
If(sph)
  tol = 1e-3;
  s() = Volume In BoundingBox {xx-rr-tol, 1-rr-tol, 1-rr-tol, xx+rr+tol,1+rr+tol,1+rr+tol};
  Printf("sphere parts = ", s());
  BooleanUnion { Volume{s(0)}; Delete; }{ Volume{s({1:#s()-1})}; Delete; }
EndIf
