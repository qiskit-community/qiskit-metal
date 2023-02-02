SetFactory("OpenCASCADE");

Mesh.Algorithm = 6;
Mesh.MeshSizeMin = 1;
Mesh.MeshSizeMax = 1;

Box(1) = {0,0,0, 1,1,1};
Cylinder(2) = {0.5,0,0, 0,1,0, 0.7};
BooleanDifference(3) = { Volume{1}; Delete; }{ Volume{2}; Delete; };

s() = Abs(Boundary{ Volume{3}; });
l() = Unique(Abs(Boundary{ Surface{s()}; }));

N = DefineNumber[ 10, Name "Parameters/N" ];

// simple transfinite mesh
Transfinite Curve{l()} = N;
Transfinite Surface{5};

// transfinite mesh with explicit corners
Transfinite Curve{9} = 2*N-1;
l4() = Abs(Boundary{ Surface{4}; });
p4() = Unique(Abs(Boundary{ Curve{l4()}; }));
Transfinite Surface{4} = {p4({0:3})};
