SetFactory("OpenCASCADE");

// this step file contains several assemblies, with overlapping surfaces
Merge "as1-tu-203.stp";

vol() = Volume{:};

Mesh.Algorithm = 6;
Mesh.MeshSizeMin = 5;
Mesh.MeshSizeMax = 5;

Physical Volume("Rod") = {};
Physical Volume("Nuts and bolts") = {};
Physical Volume("Left bracket") = {};
Physical Volume("Right bracket") = {};
Physical Volume("Plate") = {};

Physical Volume("My red volumes") = {};

For i In {0 : #vol()-1}
  // get the STEP name associated to the volume, and store the volume in a
  // physical group depending on this name
  name = Str( Volume{vol(i)} );
  If(StrFind(name, "ROD-ASSEMBLY"))
    Physical Volume("Rod") += vol(i);
  ElseIf(StrFind(name, "nut-bolt-assembly"))
    Physical Volume("Nuts and bolts") += vol(i);
  ElseIf(StrFind(name, "L-BRACKET-ASSEMBLY::1"))
    Physical Volume("Left bracket") += vol(i);
  ElseIf(StrFind(name, "L-BRACKET-ASSEMBLY::2"))
    Physical Volume("Right bracket") += vol(i);
  ElseIf(StrFind(name, "PLATE"))
    Physical Volume("Plate") += vol(i);
  EndIf

  // get the color associated to the volume and add all the red volumes in a
  // physical group
  color() = Color Volume {vol(i)};
  If (#color() >= 3)
    If(color(0) == 255 && color(1) == 0 && color(2) == 0)
      Physical Volume("My red volumes") += vol(i);
    EndIf
  EndIf
EndFor
