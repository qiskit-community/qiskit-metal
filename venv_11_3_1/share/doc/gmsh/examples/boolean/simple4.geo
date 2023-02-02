SetFactory("OpenCASCADE");

Mesh.Algorithm = 6;
Mesh.MeshSizeMin = 0.1;
Mesh.MeshSizeMax = 0.1;

Point(1) = {0,0,0};
Point(2) = {1,0,0};
Point(3) = {1,1,0};
Point(4) = {0,1,0};
Point(5) = {0.5,0.5,1};
Line(1) = {1,2};
Line(2) = {3,2};
Line(3) = {4,3};
Line(4) = {1,4};
Line(5) = {5,1};
Line(6) = {5,2};
Line(7) = {5,3};
Line(8) = {5,4};
Curve Loop(1) = {1,2,3,4};
Curve Loop(2) = {1,5,6};
Curve Loop(3) = {2,6,7};
Curve Loop(4) = {3,7,8};
Curve Loop(5) = {4,5,8};
Plane Surface(1) = {1};
Plane Surface(2) = {2};
Plane Surface(3) = {3};
Plane Surface(4) = {4};
Plane Surface(5) = {5};
Surface Loop(1) = {1,2,3,4,5};
Volume(1) = {1};
Cylinder(2) = {0.5,0.5,-0.5, 0,0,2, 0.2};
BooleanFragments{ Volume{1,2}; Delete; }{}
