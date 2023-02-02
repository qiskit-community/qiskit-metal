SetFactory("OpenCASCADE");

Mesh.MeshSizeMin = 3;
Mesh.MeshSizeMax = 3;

DefineConstant[
  angle = {90, Name "Parameters/wedge angle"}
  extrude = {10, Name "Parameters/extrusion length (with mesh)"}
];

a() = ShapeFromFile("component8.step");

Cylinder(2) = {0,150,0, 0,200,0, 40, angle*2*Pi/360};

BooleanIntersection{ Volume{a(0)}; Delete; }{ Volume{2}; Delete; }

Extrude {0, extrude, 0} {
  Surface{1}; Layers{5}; Recombine;
}
