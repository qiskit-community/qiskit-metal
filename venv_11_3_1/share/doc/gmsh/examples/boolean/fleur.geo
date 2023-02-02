a = 0.71;
b = 0.145;
NrOfPetals = 12;
L = 4;

SetFactory("OpenCASCADE");
srec = news; Rectangle(srec) = {-L/2, -L/2, 0, L, L, 0};
sell = newl; Disk(sell) = {a, 0, 0, a, b};

s1() = {sell};
For t In {1:NrOfPetals-1}
  sn() = Rotate {{0, 0, 1}, {0, 0, 1}, 2*Pi/NrOfPetals*t} {
    Duplicata { Surface{s1()}; }
  };
  s1() = BooleanUnion{ Surface{s1()}; Delete; }{ Surface{sn()}; Delete; };
EndFor

b() = BooleanDifference{ Surface{srec}; Delete; }{ Surface{s1()}; Delete; };
Physical Surface(1000) = {b()};

Mesh.MeshSizeFromCurvature = 15;
Mesh.MeshSizeMax = 0.1;
