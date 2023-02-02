SetFactory("OpenCASCADE");
Geometry.OCCAutoFix = 0;

Point(1) = {1, 0, 0};
Point(2) = {0, 0, 2};
Point(3) = {0, 0, 0};
Point(4) = {0, 0, -1};

Ellipse(100) = {2, 3, 2, 1};
Line(101) = {4, 1};

a() = Extrude{ {0,0,1}, {0,0,0}, 2*Pi }{ Line{100}; };
b() = Extrude{ {0,0,1}, {0,0,0}, 2*Pi }{ Line{101}; };

Surface Loop(1000) = {1, 2} Using Sewing;

Volume(2000) = {1000};
