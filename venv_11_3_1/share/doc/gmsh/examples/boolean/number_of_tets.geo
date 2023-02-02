SetFactory("OpenCASCADE");

N = 1e5; // approx. number of tets desired

Sphere(1) = {0, 0, 0, 1};
Box(2) = {0.3, 0, 0, 3, 0.3, 0.3};
BooleanUnion(3) = { Volume{1}; Delete; }{ Volume{2}; Delete; };

Mesh.Algorithm = 6;
Mesh.Algorithm3D = 10;
Mesh.Optimize = 1;
Mesh.OptimizeNetgen = 1;

vol = Mass Volume {3};

Mesh.MeshSizeMax = (vol*4/N)^(1/3);
Mesh.MeshSizeMin = Mesh.MeshSizeMax;
