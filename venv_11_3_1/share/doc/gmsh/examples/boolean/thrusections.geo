SetFactory("OpenCASCADE");

Mesh.Algorithm = 6;
Mesh.MeshSizeMin = 0.1;
Mesh.MeshSizeMax = 0.1;

// build volume through (closed) curve loops
For i In {0:1}
  c = newl; ll = newll;
  Circle(c) = {i,0,0, 0.2};
  Circle(c+1) = {i+0.1,0.04,1, 0.3};
  Circle(c+2) = {i+0.03,-0.08,2, 0.25};
  For j In {0:2}
    Curve Loop(ll+j) = c+j;
  EndFor
  If(i)
    Ruled ThruSections(newv) = {ll:ll+2};
  Else
    ThruSections(newv) = {ll:ll+2};
  EndIf
EndFor

// build surfaces through (closed) curve loops
For i In {0:1}
  c = newl; ll = newll;
  Circle(c) = {i+2,0,0, 0.2};
  Circle(c+1) = {i+2.1,0.04,1, 0.3};
  Circle(c+2) = {i+2.03,-0.08,2, 0.25};
  For j In {0:2}
    Curve Loop(ll+j) = c+j;
  EndFor
  If(i)
    Ruled ThruSections{ll:ll+2}
  Else
    ThruSections{ll:ll+2}
  EndIf
EndFor

// build surfaces through (open) wires
For i In {0:1}
  c = newl; ll = newll;
  Circle(c) = {i+4,0,0, 0.2, Pi/3};
  Circle(c+1) = {i+4.1,0.04,1, 0.3, Pi/2};
  Circle(c+2) = {i+4.03,-0.08,2, 0.25, Pi/3};
  For j In {0:2}
    Wire(ll+j) = c+j;
  EndFor
  If(i)
    Ruled ThruSections{ll:ll+2}
  Else
    ThruSections{ll:ll+2}
  EndIf
EndFor
