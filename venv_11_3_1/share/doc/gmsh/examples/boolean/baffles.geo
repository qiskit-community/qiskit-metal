SetFactory("OpenCASCADE");

Box(1) = {0, 0, 0, 1, 1, 1};
Box(2) = {1, 0, 0, 1, 1, 1};

p() = PointsOf{ Volume{1, 2}; };
MeshSize{p()} = 0.2;

Rectangle(17) = {0.4, 0.7, 0.2, 0.3, 0.3, 0};
Rectangle(18) = {-0.2, 0.3, 0.5, 0.3, 0.3, 0};
Rectangle(19) = {0.8, -0.2, 0.5, 0.3, 0.3, 0};
Rectangle(20) = {0.3, 0.3, 0.5, 0.3, 0.3, 0};

b() = BooleanFragments{ Volume{1, 2}; Delete; }{ Surface{17:20}; Delete; };

p() = PointsOf{ Surface{b({2:7})}; };
MeshSize{p()} = 0.04;
