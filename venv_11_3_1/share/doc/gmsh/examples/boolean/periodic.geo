SetFactory("OpenCASCADE");

R = 2;
Box(1) = {0,0,0, R,R,R};
Torus(2) = {3,0,0, 1.5, 1, Pi/3};

pts() = PointsOf{ Volume{1, 2}; };

MeshSize{ pts() } = 0.4;

MeshSize{ 2 } = 0.01;

// Find bottom and top surfaces using a bounding box search:
e = 1e-6;
bottom() = Surface In BoundingBox{-e,-e,-e, R+e,R+e,e};
top() = Surface In BoundingBox{-e,-e,R-e, R+e,R+e,R+e};

// Set a translation mesh periodicity constraint:
Periodic Surface{top()} = {bottom()} Translate{0, 0, R};

// This is a shortcut for:
// Periodic Surface{top()} = {bottom()} Affine{1,0,0,0, 0,1,0,0, 0,0,1,R};

// Set a rotation periodicity constraint:
Periodic Surface{9} = {8} Rotate{{0,0,1}, {3,0,0}, Pi/3 };
