lc = 0.02;
nn = 40; // mesh subdivisions per turn

DefineConstant
[
  turns = {5, Name "Parameters/Number of coil turns"},
 r = {0.11, Name "Parameters/Coil radius"},
 rc = {0.01, Name "Parameters/Coil wire radius"},
 hc = {0.25, Name "Parameters/Coil height"},
 ht = {0.4, Name "Parameters/Tube height"},
 rt1 = {0.075, Name "Parameters/Tube internal radius"},
 rt2 = {0.092, Name "Parameters/Tube external radius"},
 lb = {1, Name "Parameters/Infinite box width"},
 left = {1, Choices{0,1}, Name "Parameters/Terminals on the left?"}
 macro = {"title.script", Name "Macros/Add title",
          Macro "Gmsh", AutoCheck 0 /*, Highlight "Turquoise"*/ },
 showLines = {Geometry.Curves, Choices {0,1}, Name "Options/Show curves?",
              GmshOption "Geometry.Curves", AutoCheck 0}
];

// inductor
p = newp;
Point(p)={0, -r, -hc/2, lc};
Point(p+1)={0, -r+rc, -hc/2, lc};
Point(p+2)={0, -r, -hc/2+rc, lc};
Point(p+3)={0, -r-rc, -hc/2, lc};
Point(p+4)={0, -r, -hc/2-rc,lc};
c = newl;
Circle(c) = {p+1,p,p+2};
Circle(c+1) = {p+2,p,p+3};
Circle(c+2) = {p+3,p,p+4};
Circle(c+3) = {p+4,p,p+1};
ll = newll;
Curve Loop(ll) = {c,c+1,c+2,c+3};
s = news;
Plane Surface(s) = {ll};
tmp[] = {s};
vol_coil[] = {};
For j In {1:4*Floor(turns)+(left?2:0)}
  tmp[] = Extrude { {0,0,hc/Floor(turns)/4}, {0,0,1} , {0,0,0} , Pi/2}
                  { Surface {tmp[0]}; /*Layers {nn / 4};*/ };
  vol_coil[] += tmp[1];
EndFor
tmp[] = Extrude {(left?-1:1)*lb/2, 0, 0} { Surface{tmp[0]}; /*Layers{nn};*/ };
vol_coil[] += tmp[1];
out = tmp[0];
tmp[] = Extrude {-lb/2, 0, 0} { Surface{s}; /*Layers{nn};*/ };
vol_coil[] += tmp[1];
in = tmp[0];

// tube
p = newp;
Point(p) = {0, 0, -ht/2, lc};
Point(p+1) = {rt1, 0, -ht/2, lc};
Point(p+2) = {0, rt1, -ht/2, lc};
Point(p+3) = {-rt1, 0, -ht/2, lc};
Point(p+4) = {0, -rt1, -ht/2, lc};
Point(p+5) = {rt2, 0, -ht/2, lc};
Point(p+6) = {0, rt2, -ht/2, lc};
Point(p+7) = {-rt2, 0, -ht/2, lc};
Point(p+8) = {0, -rt2, -ht/2, lc};
c = newl;
Circle(c) = {p+1, p, p+2};
Circle(c+1) = {p+2, p, p+3};
Circle(c+2) = {p+3, p, p+4};
Circle(c+3) = {p+4, p, p+1};
Circle(c+4) = {p+5, p, p+6};
Circle(c+5) = {p+6, p, p+7};
Circle(c+6) = {p+7, p, p+8};
Circle(c+7) = {p+8, p, p+5};
ll = newll;
Curve Loop(ll) = {c+4, c+5, c+6, c+7, -c, -(c+1), -(c+2), -(c+3)};
s = news;
Plane Surface(s) = {ll};
tmp[] = Extrude {0,0,ht}{ Surface{s}; /*Layers{nn};*/ };
vol_tube = tmp[1];

// box
p = newp;
Point(p) = {-lb/2,-lb/2,-lb/2};
Point(p+1) = {lb/2,-lb/2,-lb/2};
Point(p+2) = {lb/2,lb/2,-lb/2};
Point(p+3) = {-lb/2,lb/2,-lb/2};
Point(p+4) = {-lb/2,-lb/2,lb/2};
Point(p+5) = {lb/2,-lb/2,lb/2};
Point(p+6) = {lb/2,lb/2,lb/2};
Point(p+7) = {-lb/2,lb/2,lb/2};
l = newl;
Line(l) = {p,p+1};
Line(l+1) = {p+1,p+2};
Line(l+2) = {p+2,p+3};
Line(l+3) = {p+3,p};
Line(l+4) = {p+4,p+5};
Line(l+5) = {p+5,p+6};
Line(l+6) = {p+6,p+7};
Line(l+7) = {p+7,p+4};
Line(l+8) = {p, p+4};
Line(l+9) = {p+1, p+5};
Line(l+10) = {p+2, p+6};
Line(l+11) = {p+3, p+7};
ll = newll;
Curve Loop(ll) = Boundary {Surface{in}; };
Curve Loop(ll+1) = {l+8, -(l+7), -(l+11), l+3};
Curve Loop(ll+2) = Boundary {Surface{out}; };
Curve Loop(ll+3) = {l+9, l+5, -(l+10), -(l+1)};
Curve Loop(ll+4) = {l,l+1,l+2,l+3};
Curve Loop(ll+5) = {l+4,l+5,l+6,l+7};
Curve Loop(ll+6) = {l+2, l+11, -(l+6), -(l+10)};
Curve Loop(ll+7) = {l, l+9, -(l+4), -(l+8)};
s = news;
tmp[] = {ll+1, ll};
If(left)
  tmp[] += ll+2;
EndIf
Plane Surface(s) = tmp[];
tmp[] = {ll+3};
If(!left)
  tmp[] += ll+2;
EndIf
Plane Surface(s+1) = tmp[];
Plane Surface(s+2) = {ll+4};
Plane Surface(s+3) = {ll+5};
Plane Surface(s+4) = {ll+6};
Plane Surface(s+5) = {ll+7};
sl = newsl;
skin_coil[] = CombinedBoundary{ Volume{vol_coil[]}; };
skin_coil[] -= {in, out};
Surface Loop(sl) = {s:s+5,skin_coil[]};
Surface Loop(sl+1) = CombinedBoundary{ Volume{vol_tube[]}; };
v = newv;
Volume(v) = {sl, sl+1};

COIL = 1000;
TUBE = 1001;
AIR = 1002;
SKIN_COIL = 2000;
SKIN_TUBE = 2001;
IN = 2002;
OUT = 2003;
INF = 2004;
Physical Volume(COIL) = {vol_coil[]};
Physical Volume(TUBE) = {vol_tube[]};
Physical Volume(AIR) = {v};
Physical Surface(SKIN_COIL) = {skin_coil[]};
Physical Surface(SKIN_TUBE) = CombinedBoundary{ Volume{vol_tube[]}; };
Physical Surface(IN) = in;
Physical Surface(OUT) = out;
Physical Surface(INF) = {s:s+5};

//Homology(2) {{COIL,TUBE},{SKIN_COIL, SKIN_TUBE}};
//Cohomology(1) {{AIR},{}};
