SetFactory("OpenCASCADE");

Mesh.Algorithm = 6;
Mesh.MeshSizeMin = 0.1;
Mesh.MeshSizeMax = 0.1;

For i In {1:5}
  Disk(i) = {0,0,0, 1};
  Rotate { {1,0,0}, {0,0,0}, Pi/6 } { Surface{i}; }
  Translate {0,0,i/5} { Surface{i}; }
EndFor

Cylinder(1) = {0,0,-0.5, 0,0,2, 0.5};

BooleanFragments{ Volume{1}; Delete; }{ Surface{1:5}; Delete; }
