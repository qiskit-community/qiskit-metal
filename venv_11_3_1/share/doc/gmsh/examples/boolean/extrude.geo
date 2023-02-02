SetFactory("OpenCASCADE");

Mesh.Algorithm = 6;
Mesh.MeshSizeMin = 0.1;
Mesh.MeshSizeMax = 0.1;

Point(1) = {0,0,0};
Point(2) = {1,0,0};
Point(3) = {1,1,0};
Point(4) = {0,1,0};
Line(1) = {1,2};
Line(2) = {2,3};
Line(3) = {3,4};
Line(4) = {4,1};
Curve Loop(1) = {1,2,3,4};
Plane Surface(1) = {1};

Point(5) = {0.2,0.2,0};
Point(6) = {0.5,0.2,0};
Point(7) = {0.5,0.5,0};
Point(8) = {0.2,0.5,0};
Line(5) = {5,6};
Line(6) = {6,7};
Line(7) = {7,8};
Line(8) = {8,5};
Curve Loop(2) = {5,6,7,8};
Plane Surface(2) = {2};

Disk(3) = {0.6, 0.6, 0, 0.5, 0.3};

DefineConstant[
  order = {1, Choices{0="Extrude before boolean",1="Boolean before extrude"},
    Name "Parameters/Operation order"}
];

If(order == 0)
  Extrude{0,0,0.3}{ Surface{1:3}; }
  Delete{ Surface{1:3}; }
  BooleanFragments{ Volume{1:3}; Delete; }{}
Else
  BooleanFragments{ Surface{1:3}; Delete; }{}
  a() = Extrude{0,0,0.3}{ Surface{1:5}; };
  Printf("returned entities (top, body, laterals, etc.) = ", a());
EndIf
