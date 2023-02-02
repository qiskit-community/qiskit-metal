SetFactory("OpenCASCADE");
Box(1) = {0, 0, 0, 1, 1, 1};

Point(10) = {0.5, 0.5, 0};
Point(11) = {0.7, 0.7, 0};
Point(12) = {0.5, 0.5, 1};
Point(13) = {0.7, 0.7, 1};

Point(20) = {0.1, 0.1, 0};
Point(21) = {0.1, 0.1, 1};

Line(15) = {10, 11};
Line(16) = {12, 13};

Curve {15} In Surface{5};
Curve {16} In Surface{6};

Point {20} In Surface{5};
Point {21} In Surface{6};

Periodic Surface{6} = {5} Translate{0, 0, 1};
