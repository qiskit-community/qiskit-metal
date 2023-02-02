SetFactory("OpenCASCADE");

// load volume(s) from step file
v() = ShapeFromFile("component8.step");
//v() = ShapeFromFile("as1-tu-203.stp");

// get bounding box of volume
bbox() = BoundingBox Volume{v()};
xmin = bbox(0);
ymin = bbox(1);
zmin = bbox(2);
xmax = bbox(3);
ymax = bbox(4);
zmax = bbox(5);

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

// delete all surfaces that are not on the boundary of a volume, all curves that
// are not on the boundary of a surface, and all points that are not on the
// boundary of a curve
Delete { Surface{:}; Curve{:}; Point{:}; }

// get surfaces in bounding boxes around the cutting planes
eps = 1e-4;
s() = {};
For i In {1:N-1}
  s() += Surface In BoundingBox{xmin-eps,ymin-eps,zmin + i * dz - eps,
                                xmax+eps,ymax+eps,zmin + i * dz + eps};
EndFor

// delete all other entities
dels = Surface{:};
dels -= s();
Delete { Volume{:}; Surface{dels()}; Curve{:}; Point{:}; }
