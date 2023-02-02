SetFactory("OpenCASCADE");
a = 0.300;
b = 0.075;
L = 0.5;

lc1 = 0.100;
lc2 = 0.050;
lc3 = 0.025;

Point(1) = {a*Cos(Pi/6), a*Sin(Pi/6), 0, lc2};
Point(2) = {-b*Sin(Pi/6), b*Cos(Pi/6), 0, lc2};
Point(3) = {-a*Cos(Pi/6), -a*Sin(Pi/6), 0, lc2};
Point(4) = {b*Sin(Pi/6), -b*Cos(Pi/6), 0, lc2};
Point(5) = {0, 0, 0, lc2};

Ellipse(1) = {3, 5, 3, 2};
Ellipse(2) = {3, 5, 3, 4};
Ellipse(3) = {1, 5, 1, 4};
Ellipse(4) = {1, 5, 1, 2};
l~{1}() = {1:4};
Curve Loop(1) = l~{1}();

N = DefineNumber[3, Name "Parameters/Number of slices", Min 2, Max 10, Step 1];
angle = DefineNumber[Pi/4, Name "Parameters/Angle", Min 0, Max 2*Pi, Step 0.1];
For i In {2:N}
  l~{i}() = Translate{0,0,1/(N-1)}{ Duplicata{ Curve{l~{i-1}()}; } };
  Rotate {{0, 0, 1}, {0, 0, 0}, angle/(N-1)} { Curve{l~{i}()}; }
  Curve Loop(i) = l~{i}();
EndFor

ThruSections(1) = {1:N};
Box(2) = {-0.5,-0.5,0, 1,1,1};

MeshSize { PointsOf{ Volume{2}; } } = lc1;

BooleanFragments{ Volume{1,2}; Delete; }{}
