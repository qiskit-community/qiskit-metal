SetFactory("OpenCASCADE");

// load volume from step file
v() = ShapeFromFile("component8.step");

// get bounding box of volume
bbox() = BoundingBox Volume{v()};

eps = 1e-2;

xmin = bbox(0) - eps;
ymin = bbox(1) - eps;
zmin = bbox(2) - eps;
xmax = bbox(3) + eps;
ymax = bbox(4) + eps;
zmax = bbox(5) + eps;

// define number of slices along z-axis
DefineConstant[ N = {10, Min 2, Max 100, Step 1, Name "Number of slices"}];
dz = (zmax - zmin) / N;

// define cutting planes
For i In {1:N-1}
  Rectangle(1000 + i) = {xmin, ymin, zmin + i * dz,
                         xmax-xmin, ymax-ymin};
EndFor

// fragment (i.e. "intersect") the volume with all the cutting planes
BooleanFragments{ Volume{v()}; Delete; }{ Surface{1000+1:1000+N-1}; Delete; }

// delete all resulting surfaces that are not on the boundary of a volume, all
// curves that are not on the boundary of a surface, and all points that are not
// on the boundary of a curve
Delete { Surface{:}; Curve{:}; Point{:}; }

// Et voila :-)

// To slice the mesh instead the CAD, one can use the "SimplePartition" Plugin:
/*
  Plugin("SimplePartition").NumSlicesX = 1;
  Plugin("SimplePartition").NumSlicesY = 1;
  Plugin("SimplePartition").NumSlicesZ = N;
  Plugin("SimplePartition").Run
*/

// For general mesh partitions of course, use "PartitionMesh N;"
