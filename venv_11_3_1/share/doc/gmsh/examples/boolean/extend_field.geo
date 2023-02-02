SetFactory("OpenCASCADE");
Box(1) = {0,0,0, 1,1,0.5};
Sphere(2) = {1,1,0.5,0.4};
BooleanDifference(3) = { Volume{1}; Delete; }{ Volume{2}; Delete; };

Box(10) = {0.3,0.3,0.5, 0.1,0.1,0.05};
Box(11) = {0.5,0.5,0.5, 0.1,0.1,0.05};
BooleanFragments{ Volume{10, 11}; Delete; }{ Volume{3}; Delete; }

DefineConstant[
  size_large = {0.04, Min 0.002, Max 0.2, Step 0.001,
    Name "Parameters/Size on large shape"}
  size_small = {0.002, Min 0.002, Max 0.2, Step 0.001,
    Name "Parameters/Size on small shapes"}
  use_field = {1, Choices{0, 1},
    Name "Parameters/0Use Extend field?"}
  size_max = {0.04, Min 0.002, Max 0.2, Step 0.001,
    Name "Parameters/Extend Field/SizeMax", Visible use_field}
  dist_max = {0.1, Min 0.01, Max 1, Step 0.01,
    Name "Parameters/Extend Field/DistMax", Visible use_field}
  power = {2, Min 0.1, Max 10, Step 0.1,
    Name "Parameters/Extend Field/Power", Visible use_field}
];

MeshSize{ : } = size_large;
MeshSize{ PointsOf{ Volume{10, 11}; } } = size_small;
Mesh.Algorithm3D = 10;

If(use_field == 0)
  Mesh.MeshSizeExtendFromBoundary = 1;
Else
  // set to -2 or -3 to only extend in 2D or 3D
  Mesh.MeshSizeExtendFromBoundary = 0;
  Field[1] = Extend;
  Field[1].SurfacesList = {Surface{:}};
  Field[1].CurvesList = {Curve{:}};
  Field[1].DistMax = dist_max;
  Field[1].SizeMax = size_max;
  Field[1].Power = power;
  Background Field = 1;
EndIf
