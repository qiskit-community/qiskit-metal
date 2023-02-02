SetFactory("OpenCASCADE");

//Geometry.CurveNumbers = 1;
Geometry.SurfaceNumbers = 1;

DefineConstant[
  w = {0.05, Name "Width"}
  N = {10, Name "Number of disks"}
  R = {0.002, Name "Disk radius"}
  spacing = {0, Min 0, Max R, Step R/10, Name "Disk spacing"}
];

Rectangle(1) = {-3*w, w, 0, 6*w, w, 0};
Rectangle(2) = {-3*w, 0., 0, w, w, 0};
Translate {2*w, 0, 0} { Duplicata { Surface{2}; } }
Translate {w, 0, 0} { Duplicata { Surface{3}; } }
Translate {2*w, 0, 0} { Duplicata { Surface{4}; } }

Rectangle(6) = {-6*w, 0, 0, 12*w, 5*w, 0};

b() = Boundary{ Surface{6}; };
t = b(2);
Printf("top line tag: ", t);

b() = {};
For i In {1:N}
  s = news; b() += s; Disk(s) = {-w-R-spacing, (2*R+spacing)*i, 0, R};
EndFor

Printf("disk tags: ", b());

c() = BooleanFragments{ Curve{t}; Surface{1:6,b()}; Delete; }{};

Printf("all tags (disk and top line tags should be unchanged!): ", c());
