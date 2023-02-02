
SetFactory("OpenCASCADE");

Geometry.CurveNumbers = 1;

xw_ = 0.1; yw_ = 0.1;
s_wire = news;
Rectangle(news) = {-xw_, -yw_, 0.,  2*xw_,  2*yw_};
l_wire[] = Abs(Boundary{Surface{s_wire};});
Delete{ Surface{s_wire}; } // Surface s_wire is deleted to keep only its boundary
Printf("init: l_wire[] = ", l_wire[]);

DefineConstant[
  flag_Symmetry_X = { 0, Choices{0,1}, Name "Symmetry X0-plane" }
  flag_Symmetry_Y = { 0, Choices{0,1}, Name "Symmetry Y0-plane" }
  flag_Symmetry_Z = { 0, Choices{0,1}, Name "Symmetry Z0-plane" }
];

dx = 0.4; dy = 0.4; dz = 0.4;
x_min_ = flag_Symmetry_X ? 0. : -dx/2;
y_min_ = flag_Symmetry_Y ? 0. : -dy/2;
z_min_ = flag_Symmetry_Z ? 0. : -dz/2;
ddx = flag_Symmetry_X ? dx / 2 : dx;
ddy = flag_Symmetry_Y ? dy / 2 : dy;
ddz = flag_Symmetry_Z ? dz / 2 : dz;

v_box=newv;
Box(newv) = {x_min_, y_min_, z_min_, ddx, ddy, ddz};

l_wire[] = BooleanIntersection { Curve{l_wire[]}; Delete; }{ Volume{v_box}; };

Printf("after intersection: new l_wire[] = ", l_wire[]);
