// The two longitudinal bars

f4 = 0.6 ;
f5 = 1.33 ;

xmin =-27.e-3 ;
LL   = 1821.3e-3 ;
ll   = 20.e-3 ;
hh   = 20.e-3 ;
dc   = 8.e-3 ;
em   = 8.e-3/2 ;
eM   = 40.e-3/2 ;
t    = ArcTan(eM/2-em/2/LL) ;

Point(1) = {xmin, -em-hh, -ll/2, f4*ll/2} ; Point(5) = {xmin, em, -ll/2, f4*ll/2} ;
Point(2) = {xmin, -em-hh,  ll/2, f4*ll/2} ; Point(6) = {xmin, em,  ll/2, f4*ll/2} ;
Point(3) = {xmin, -em,    -ll/2, f4*ll/2} ; Point(7) = {xmin, em+hh, -ll/2, f4*ll/2} ;
Point(4) = {xmin, -em,     ll/2, f4*ll/2} ; Point(8) = {xmin, em+hh,  ll/2, f4*ll/2} ;

Point(9)  = {xmin+LL, -eM-hh, -ll/2, f5*ll/2} ; Point(13) = {xmin+LL, eM, -ll/2, f5*ll/2} ;
Point(10) = {xmin+LL, -eM-hh,  ll/2, f5*ll/2} ; Point(14) = {xmin+LL, eM,  ll/2, f5*ll/2} ;
Point(11) = {xmin+LL, -eM,    -ll/2, f5*ll/2} ; Point(15) = {xmin+LL, eM+hh, -ll/2, f5*ll/2} ;
Point(12) = {xmin+LL, -eM,     ll/2, f5*ll/2} ; Point(16) = {xmin+LL, eM+hh,  ll/2, f5*ll/2} ;

Line(1) = {5,6};  Line(11) = {13,14};
Line(2) = {6,8};  Line(12) = {14,16};
Line(3) = {8,7};  Line(13) = {16,15};
Line(4) = {7,5};  Line(14) = {15,13};
Line(5) = {1,2};  Line(15) = {9,10};
Line(6) = {2,4};  Line(16) = {10,12};
Line(7) = {4,3};  Line(17) = {12,11};
Line(8) = {3,1};  Line(18) = {11,9};
Line(9) = {4,6};  Line(19) = {12,14};
Line(10) = {3,5}; Line(20) = {11,13};

Line(21) = {8,16}; Line(25) = {2,10};
Line(22) = {7,15}; Line(26) = {4,12};
Line(23) = {6,14}; Line(27) = {3,11};
Line(24) = {5,13}; Line(28) = {1,9};

// The 22 resonators

f1 = 2 ; f2 = 3.5 ; f3 = 5 ;

// length             ;  radius        ; dist % 1st bar  ; dist % y=0                   ; charact. length
 l1 =   77.e-3/2-ll/2 ;  r1 =  8.e-3/2 ;  d1 =         0 ;  e1 = em+dc+d1*Sin(t)-2.e-3  ;  s1 = f1*r1 ;
 l2 =   91.e-3/2-ll/2 ;  r2 =  8.e-3/2 ;  d2 =   11.9e-3 ;  e2 = em+dc+d2*Sin(t)-2.e-3  ;  s2 = f1*r2 ;
 l3 =  105.e-3/2-ll/2 ;  r3 =  8.e-3/2 ;  d3 =   25.8e-3 ;  e3 = em+dc+d3*Sin(t)-2.e-3  ;  s3 = f1*r3 ;
 l4 =  122.e-3/2-ll/2 ;  r4 =  8.e-3/2 ;  d4 =   41.8e-3 ;  e4 = em+dc+d4*Sin(t)-2.e-3  ;  s4 = f1*r4 ;
 l5 =  142.e-3/2-ll/2 ;  r5 = 10.e-3/2 ;  d5 =   60.5e-3 ;  e5 = em+dc+d5*Sin(t)-1.e-3  ;  s5 = f1*r5 ;
 l6 =  164.e-3/2-ll/2 ;  r6 = 10.e-3/2 ;  d6 =   82.5e-3 ;  e6 = em+dc+d6*Sin(t)-1.e-3  ;  s6 = f1*r6 ;
 l7 =  192.e-3/2-ll/2 ;  r7 = 12.e-3/2 ;  d7 =  107.0e-3 ;  e7 = em+dc+d7*Sin(t)        ;  s7 = f1*r7 ;
 l8 =  224.e-3/2-ll/2 ;  r8 = 12.e-3/2 ;  d8 =  138.5e-3 ;  e8 = em+dc+d8*Sin(t)        ;  s8 = f1*r8 ;
 l9 =  260.e-3/2-ll/2 ;  r9 = 12.e-3/2 ;  d9 =  172.0e-3 ;  e9 = em+dc+d9*Sin(t)        ;  s9 = f1*r9 ;
l10 =  303.e-3/2-ll/2 ; r10 = 12.e-3/2 ; d10 =  212.0e-3 ; e10 = em+dc+d10*Sin(t)       ; s10 = f1*r10 ;
l11 =  353.e-3/2-ll/2 ; r11 = 12.e-3/2 ; d11 =  258.5e-3 ; e11 = em+dc+d11*Sin(t)       ; s11 = f1*r11 ;
l12 =  410.e-3/2-ll/2 ; r12 = 12.e-3/2 ; d12 =  312.5e-3 ; e12 = em+dc+d12*Sin(t)       ; s12 = f1*r12 ;
l13 =  477.e-3/2-ll/2 ; r13 = 12.e-3/2 ; d13 =  375.0e-3 ; e13 = em+dc+d13*Sin(t)       ; s13 = f1*r13 ;
l14 =  554.e-3/2-ll/2 ; r14 = 12.e-3/2 ; d14 =  448.5e-3 ; e14 = em+dc+d14*Sin(t)       ; s14 = f1*r14 ;
l15 =  645.e-3/2-ll/2 ; r15 = 12.e-3/2 ; d15 =  533.0e-3 ; e15 = em+dc+d15*Sin(t)       ; s15 = f1*r15 ;
l16 =  749.e-3/2-ll/2 ; r16 = 12.e-3/2 ; d16 =  632.5e-3 ; e16 = em+dc+d16*Sin(t)       ; s16 = f1*r16 ;
l17 =  877.e-3/2-ll/2 ; r17 = 12.e-3/2 ; d17 =  750.5e-3 ; e17 = em+dc+d17*Sin(t)       ; s17 = f2*r17 ;
l18 = 1023.e-3/2-ll/2 ; r18 = 12.e-3/2 ; d18 =  888.0e-3 ; e18 = em+dc+d18*Sin(t)       ; s18 = f2*r18 ;
l19 = 1196.e-3/2-ll/2 ; r19 = 12.e-3/2 ; d19 = 1050.3e-3 ; e19 = em+dc+d19*Sin(t)       ; s19 = f3*r19 ;
l20 = 1404.e-3/2-ll/2 ; r20 = 12.e-3/2 ; d20 = 1241.7e-3 ; e20 = em+dc+d20*Sin(t)       ; s20 = f3*r20 ;
l21 = 1648.e-3/2-ll/2 ; r21 = 12.e-3/2 ; d21 = 1467.7e-3 ; e21 = em+dc+d21*Sin(t)       ; s21 = f3*r21 ;
l22 = 1934.e-3/2-ll/2 ; r22 = 12.e-3/2 ; d22 = 1734.3e-3 ; e22 = em+dc+d22*Sin(t)       ; s22 = f3*r22 ;

dx = d1 ; rx = r1 ; sx = s1 ; lx = l1 ; e = e1 ; x = 100; Include "antenna.i1" ;
dx = d2 ; rx = r2 ; sx = s2 ; lx = l2 ; e =-e2 ; x = 200; Include "antenna.i1" ;
dx = d3 ; rx = r3 ; sx = s3 ; lx = l3 ; e = e3 ; x = 300; Include "antenna.i1" ;
dx = d4 ; rx = r4 ; sx = s4 ; lx = l4 ; e =-e4 ; x = 400; Include "antenna.i1" ;
dx = d5 ; rx = r5 ; sx = s5 ; lx = l5 ; e = e5 ; x = 500; Include "antenna.i1" ;
dx = d6 ; rx = r6 ; sx = s6 ; lx = l6 ; e =-e6 ; x = 600; Include "antenna.i1" ;
dx = d7 ; rx = r7 ; sx = s7 ; lx = l7 ; e = e7 ; x = 700; Include "antenna.i1" ;
dx = d8 ; rx = r8 ; sx = s8 ; lx = l8 ; e =-e8 ; x = 800; Include "antenna.i1" ;
dx = d9 ; rx = r9 ; sx = s9 ; lx = l9 ; e = e9 ; x = 900; Include "antenna.i1" ;
dx = d10; rx = r10; sx = s10; lx = l10; e =-e10; x =1000; Include "antenna.i1" ;
dx = d11; rx = r11; sx = s11; lx = l11; e = e11; x =1100; Include "antenna.i1" ;
dx = d12; rx = r12; sx = s12; lx = l12; e =-e12; x =1200; Include "antenna.i1" ;
dx = d13; rx = r13; sx = s13; lx = l13; e = e13; x =1300; Include "antenna.i1" ;
dx = d14; rx = r14; sx = s14; lx = l14; e =-e14; x =1400; Include "antenna.i1" ;
dx = d15; rx = r15; sx = s15; lx = l15; e = e15; x =1500; Include "antenna.i1" ;
dx = d16; rx = r16; sx = s16; lx = l16; e =-e16; x =1600; Include "antenna.i1" ;
dx = d17; rx = r17; sx = s17; lx = l17; e = e17; x =1700; Include "antenna.i1" ;
dx = d18; rx = r18; sx = s18; lx = l18; e =-e18; x =1800; Include "antenna.i1" ;
dx = d19; rx = r19; sx = s19; lx = l19; e = e19; x =1900; Include "antenna.i1" ;
dx = d20; rx = r20; sx = s20; lx = l20; e =-e20; x =2000; Include "antenna.i1" ;
dx = d21; rx = r21; sx = s21; lx = l21; e = e21; x =2100; Include "antenna.i1" ;
dx = d22; rx = r22; sx = s22; lx = l22; e =-e22; x =2200; Include "antenna.i1" ;

// Surfaces for longitudinal bars

Curve Loop(3001) = {-13,-21,3,22};  Plane Surface(3101) = {3001}; // ymax
Curve Loop(3002) = {23,-11,-24,1};  Plane Surface(3102) = {3002}; // ymax - eps
Curve Loop(3003) = {-27,-7,26,17};  Plane Surface(3103) = {3003}; // ymin + eps
Curve Loop(3004) = {25,-15,-28,5};  Plane Surface(3104) = {3004}; // ymin
Curve Loop(3005) = {3,4,1,2};       Plane Surface(3105) = {3005}; // left top
Curve Loop(3006) = {7,8,5,6};       Plane Surface(3106) = {3006}; // left bottom
Curve Loop(3007) = {11,12,13,14};   Plane Surface(3107) = {3007}; // right top
Curve Loop(3008) = {18,15,16,17};   Plane Surface(3108) = {3008}; // right bottom

Curve Loop(3011) = {-9,7,10,1};     Plane Surface(3111) = {3011}; // input
Curve Loop(3012) = {-11,-20,-17,19};Plane Surface(3112) = {3012}; // output

Curve Loop(3013) = {-26,-6,25,16};
Curve Loop(3014) = {-28,-8,27,18};
Curve Loop(3015) = {-21,-2,23,12};
Curve Loop(3016) = {-24,-4,22,14};
Plane Surface(3113) = {3013,203,403,603,803,1003,1203,1403,1603,1803,2003,2203} ;
Plane Surface(3114) = {3014,101,301,501,701,901,1101,1301,1501,1701,1901,2101};
Plane Surface(3115) = {3015,103,303,503,703,903,1103,1303,1503,1703,1903,2103};
Plane Surface(3116) = {3016,201,401,601,801,1001,1201,1401,1601,1801,2001,2201};

// The physical entities

AIR       = 8001 ;
XM        = 8002 ;
XP        = 8003 ;
YM        = 8004 ;
YP        = 8005 ;
ZM        = 8006 ;
ZP        = 8007 ;

CLINPUT   = 9001 ;
CLBOX     = 9002 ;
CLLONG    = 9003 ;
CLBAR     = 9004 ;
CLBEM     = 9005 ;

Physical Surface(CLINPUT) = {3111};
Physical Surface(CLBEM) = {4119,4106,4115,4111,4122,4124};
Physical Surface(CLLONG) = {3102,3115,3101,3116,3105,3107,3103,3114,3104,3113,3108,3106};
Physical Surface(CLBAR) =
{
  122,125,126,127,128,
  124,129,130,131,132,
  222,225,226,227,228,
  224,229,230,231,232,
  322,325,326,327,328,
  324,329,330,331,332,
  422,425,426,427,428,
  424,429,430,431,432,
  522,525,526,527,528,
  524,529,530,531,532,
  622,625,626,627,628,
  624,629,630,631,632,
  722,725,726,727,728,
  724,729,730,731,732,
  822,825,826,827,828,
  824,829,830,831,832,
  922,925,926,927,928,
  924,929,930,931,932,
  1022,1025,1026,1027,1028,
  1024,1029,1030,1031,1032,
  1122,1125,1126,1127,1128,
  1124,1129,1130,1131,1132,
  1222,1225,1226,1227,1228,
  1224,1229,1230,1231,1232,
  1322,1325,1326,1327,1328,
  1324,1329,1330,1331,1332,
  1422,1425,1426,1427,1428,
  1424,1429,1430,1431,1432,
  1522,1525,1526,1527,1528,
  1524,1529,1530,1531,1532,
  1622,1625,1626,1627,1628,
  1624,1629,1630,1631,1632,
  1722,1725,1726,1727,1728,
  1724,1729,1730,1731,1732,
  1822,1825,1826,1827,1828,
  1824,1829,1830,1831,1832,
  1922,1925,1926,1927,1928,
  1924,1929,1930,1931,1932,
  2022,2025,2026,2027,2028,
  2024,2029,2030,2031,2032,
  2122,2125,2126,2127,2128,
  2124,2129,2130,2131,2132,
  2222,2225,2226,2227,2228,
  2224,2229,2230,2231,2232
 };
