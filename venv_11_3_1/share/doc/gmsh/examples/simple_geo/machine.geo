// Original author: Francois Henrotte

// All dimensions in meters and rads

Lc = 0.0004 ;           // Base char length
Z  = 0.0 ;              // Z-coord

// Stator data

nbs = 36 ;		// Num. of poles
dths = 2 * Pi / nbs ;   // Ang. shift between 2 poles.

// Pi is the only constant predefined in Gmsh

th0s = dths / 2 ;       // Angular pos.
des = 0.1529 ;          // Ext. diam.
res = des / 2 ;
dis = 0.09208 ;         // Int. diam.
ris = dis / 2 ;

hs = 0.0153 ;           // Pole height
h1s = 0.000762 ;        // Dist. intersection rec.-int. circle
d1s = 0.00636 ;         // Diam. sup. circle
r1s = d1s / 2 ;
rc1s = 0.00084 ;        // Radius convex rec.
rc2s = 0.000508 ;       // Radius concave rec.
e1s = 0.0025 ;          // Dist. between 2 sides at int diam
e2s = 0.00424 ;         // Dist. between 2 sides at 1st rec.

// Rotor data

nbr = 32 ;		// Num. of poles
dthr = 2 * Pi / nbr ;   // Angular shift betw. 2 poles

th0r = dths / 2 ;       // Ang. pos. rotor
gap = 0.00080 ;         // Air gap width
espa = 0.0015 ;         // Dist. stator-pole top
der = 0.09208 ;         // Ext. diam rotor
rer = der / 2 ;
dir = 0.03175 ;         // Diam. int.
rir = dir / 2 ;

hr = 0.01425 ;          // Pole height
d1r = 0.00426 ;         // Diam. sup circle
r1r = d1r / 2 ;
d2r = 0.00213 ;         // Diam. inf. circle
r2r = d2r / 2 ;

dist = rer - espa ;	// Radial dist. of intersect. point

/* 'newp' is a meta variable defining a new point number for you.
   This is mostly useful with included files. There is also 'newreg'
   which defines a new region number (that is, everything that is not
   a point). */

pAxe = newp ; Point(pAxe) = { 0. , 0. , 0., 15*Lc} ;

// axis

p1 = newp ; Point(p1) = { rir, 0. , 0., 15*Lc} ;
p2 = newp ; Point(p2) = { 0. , rir, 0., 15*Lc} ;

lin1 = newreg ;	Line(lin1)   = {pAxe,p1} ;
arc1 = newreg ;	Circle(arc1) = {p1,pAxe,p2} ;
lin2 = newreg ;	Line(lin2)   = {p2, pAxe} ;

reg1 = newreg ; Curve Loop(reg1) = {lin1,arc1,lin2} ;
reg2 = newreg ; Plane Surface(reg2) = {reg1} ;

// Rotor lateral sides

p3 = newp ; Point(p3) = { rer-gap, 0.     , 0., Lc} ;
p4 = newp ; Point(p4) = { 0.     , rer-gap, 0., Lc} ;

lin3 = newreg ; Line(lin3)   = {p1, p3} ;
arc2 = newreg ; Circle(arc2) = {p3,pAxe,p4} ;
lin4 = newreg ;	Line(lin4)   = {p4, p2} ;

// Air gap

p5 = newp ; Point(p5) = { ris, 0. , 0., Lc} ;
p6 = newp ; Point(p6) = { 0. , ris, 0., Lc} ;

lin5 = newreg ; Line(lin5) = {p3, p5} ;
lin6 = newreg ; Line(lin6) = {p6, p4} ;

// Stator exterior

p7 = newp ; Point(p7) = { res, 0. , 0. , 15*Lc } ;
p8 = newp ; Point(p8) = { 0. , res, 0. , 15*Lc } ;

lin7 = newreg ;	Line(lin7)   = {p5, p7} ;
arc4 = newreg ;	Circle(arc4) = {p7,pAxe,p8} ;
lin8 = newreg ;	Line(lin8)   = {p8, p6} ;

PP1 = p5 ; PPB = p6 ;

// 8 rotor poles

D1 = dist ;
H  = hr ;
R1 = r1r ;
R2 = r2r ;

/* You can include files with the 'Include' command. Note that *ALL*
   variables in Gmsh are global. Including a file is similar to paste
   its content where the include command is located. */

i = 0;

For(1:8)
  i++ ;
  th = th0r + (i - 1) * dthr ;
  Include "machine.i1" ;
EndFor

// 9 stator poles

dth = dths ;
D2  = ris ;
H   = hs ;
R1 = r1s ;
R2 = rc1s ;
R3 = rc2s ;
E1 = e1s ;
E2 = e2s ;
H1 = h1s ;

i = 1 ; th = th0s + (i - 1) * dths ;
Include "machine.i2" ;
PP2 = p1 ; PP3 = p9 ;
i = 2 ; th = th0s + (i - 1) * dths ;
Include "machine.i2" ;
PP4 = p1 ; PP5 = p9 ;
i = 3 ; th = th0s + (i - 1) * dths ;
Include "machine.i2" ;
PP6 = p1 ; PP7 = p9 ;
i = 4 ; th = th0s + (i - 1) * dths ;
Include "machine.i2" ;
PP8 = p1 ; PP9 = p9 ;
i = 5 ; th = th0s + (i - 1) * dths ;
Include "machine.i2" ;
PP10 = p1 ; PP11 = p9 ;
i = 6 ; th = th0s + (i - 1) * dths ;
Include "machine.i2" ;
PP12 = p1 ; PP13 = p9 ;
i = 7 ; th = th0s + (i - 1) * dths ;
Include "machine.i2" ;
PP14 = p1 ; PP15 = p9 ;
i = 8 ; th = th0s + (i - 1) * dths ;
Include "machine.i2" ;
PP16 = p1 ; PP17 = p9 ;
i = 9 ; th = th0s + (i - 1) * dths ;
Include "machine.i2" ;
PP18 = p1 ; PP19 = p9 ;

lin1 = newreg ; Line(lin1) = {PP1 , PP2 } ;
lin1 = newreg ; Line(lin1) = {PP3 , PP4 } ;
lin1 = newreg ; Line(lin1) = {PP5 , PP6 } ;
lin1 = newreg ; Line(lin1) = {PP7 , PP8 } ;
lin1 = newreg ; Line(lin1) = {PP9 , PP10} ;
lin1 = newreg ; Line(lin1) = {PP11, PP12} ;
lin1 = newreg ; Line(lin1) = {PP13, PP14} ;
lin1 = newreg ; Line(lin1) = {PP15, PP16} ;
lin1 = newreg ; Line(lin1) = {PP17, PP18} ;
lin1 = newreg ; Line(lin1) = {PP19, PPB } ;


Curve Loop(145) = {8,-2,6,7};
Plane Surface(146) = {145,68,61,54,47,40,33,26,19};

Curve Loop(147) = {-7,9,133,-74,134,-81,135,-88,136,-95,137,-102,
                  138,-109,139,-116,140,-123,141,-130,142,10};
Plane Surface(148) = {147};

Curve Loop(149) = {70,71,72,73,134,77,78,79,80,135,84,85,86,87,136,
                  91,92,93,94,137,98,99,100,101,138,105,106,107,108,
                  139,112,113,114,115,140,119,120,121,122,141,126,127,
                  128,129,142,-13,-12,-11,133};
Plane Surface(150) = {149};

/* One should define physical regions to specify what to
   save. Otherwise, only mesh points will be output in the mesh
   file. */
