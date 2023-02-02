// -----------------------------------------------------------------------------
//
//  Gmsh C tutorial 6
//
//  Transfinite meshes
//
// -----------------------------------------------------------------------------

#include <string.h>
#include <gmshc.h>

int main(int argc, char **argv)
{
  int ierr;

  gmshInitialize(argc, argv, 1, 0, &ierr);

  gmshModelAdd("t2", &ierr);

  // Copied from `t1.c'...
  const double lc = 1e-2;
  gmshModelGeoAddPoint(0, 0, 0, lc, 1, &ierr);
  gmshModelGeoAddPoint(.1, 0, 0, lc, 2, &ierr);
  gmshModelGeoAddPoint(.1, .3, 0, lc, 3, &ierr);
  gmshModelGeoAddPoint(0, .3, 0, lc, 4, &ierr);

  gmshModelGeoAddLine(1, 2, 1, &ierr);
  gmshModelGeoAddLine(3, 2, 2, &ierr);
  gmshModelGeoAddLine(3, 4, 3, &ierr);
  gmshModelGeoAddLine(4, 1, 4, &ierr);

  const int cl1[] = {4, 1, -2, 3};
  gmshModelGeoAddCurveLoop(cl1, sizeof(cl1) / sizeof(cl1[0]), 1, 0, &ierr);

  const int s1[] = {1};
  gmshModelGeoAddPlaneSurface(s1, sizeof(s1) / sizeof(s1[0]), 1, &ierr);

  // Delete the surface and the left line, and replace the line with 3 new ones:
  const int r4[] = {2, 1, 1, 4};
  gmshModelGeoRemove(r4, 4, 0, &ierr);

  int p1 = gmshModelGeoAddPoint(-0.05, 0.05, 0, lc, -1, &ierr);
  int p2 = gmshModelGeoAddPoint(-0.05, 0.1, 0, lc, -1, &ierr);

  int l1 = gmshModelGeoAddLine(1, p1, -1, &ierr);
  int l2 = gmshModelGeoAddLine(p1, p2, -1, &ierr);
  int l3 = gmshModelGeoAddLine(p2, 4, -1, &ierr);

  // Create surface:
  const int cl2[] = {2, -1, l1, l2, l3, -3};
  gmshModelGeoAddCurveLoop(cl2, sizeof(cl2) / sizeof(cl2[0]), 2, 0, &ierr);

  const int s2[] = {-2};
  gmshModelGeoAddPlaneSurface(s2, sizeof(s2) / sizeof(s2[0]), 1, &ierr);

  // The `setTransfiniteCurve()' meshing constraints explicitly specifies the
  // location of the nodes on the curve. For example, the following command
  // forces 20 uniformly placed nodes on curve 2 (including the nodes on the two
  // end points):
  gmshModelGeoMeshSetTransfiniteCurve(2, 20, "Progression", 1.0, &ierr);

  // Let's put 20 points total on combination of curves `l1', `l2' and `l3'
  // (beware that the points `p1' and `p2' are shared by the curves, so we do
  // not create 6 + 6 + 10 = 22 nodes, but 20!)
  gmshModelGeoMeshSetTransfiniteCurve(l1, 6, "Progression", 1.0, &ierr);
  gmshModelGeoMeshSetTransfiniteCurve(l2, 6, "Progression", 1.0, &ierr);
  gmshModelGeoMeshSetTransfiniteCurve(l3, 10, "Progression", 1.0, &ierr);

  // Finally, we put 30 nodes following a geometric progression on curve 1
  // (reversed) and on curve 3: Put 30 points following a geometric progression
  gmshModelGeoMeshSetTransfiniteCurve(1, 30, "Progression", -1.2, &ierr);
  gmshModelGeoMeshSetTransfiniteCurve(3, 30, "Progression", 1.2, &ierr);

  // The `setTransfiniteSurface()' meshing constraint uses a transfinite
  // interpolation algorithm in the parametric plane of the surface to connect
  // the nodes on the boundary using a structured grid. If the surface has more
  // than 4 corner points, the corners of the transfinite interpolation have to
  // be specified by hand:
  const int ts[] = {1, 2, 3, 4};
  gmshModelGeoMeshSetTransfiniteSurface(1, "Left", ts, 4, &ierr);

  // To create quadrangles instead of triangles, one can use the `setRecombine'
  // constraint:
  gmshModelGeoMeshSetRecombine(2, 1, 45.0, &ierr);

  // When the surface has only 3 or 4 points on its boundary the list of corners
  // can be omitted in the `setTransfiniteSurface()' call:
  gmshModelGeoAddPoint(0.2, 0.2, 0, 1.0, 7, &ierr);
  gmshModelGeoAddPoint(0.2, 0.1, 0, 1.0, 8, &ierr);
  gmshModelGeoAddPoint(0, 0.3, 0, 1.0, 9, &ierr);
  gmshModelGeoAddPoint(0.25, 0.2, 0, 1.0, 10, &ierr);
  gmshModelGeoAddPoint(0.3, 0.1, 0, 1.0, 11, &ierr);

  gmshModelGeoAddLine(8, 11, 10, &ierr);
  gmshModelGeoAddLine(11, 10, 11, &ierr);
  gmshModelGeoAddLine(10, 7, 12, &ierr);
  gmshModelGeoAddLine(7, 8, 13, &ierr);

  const int cl3[] = {13, 10, 11, 12};
  gmshModelGeoAddCurveLoop(cl3, sizeof(cl3) / sizeof(cl3[0]), 14, 0, &ierr);

  const int s3[] = {14};
  gmshModelGeoAddPlaneSurface(s3, sizeof(s3) / sizeof(s3[0]), 15, &ierr);

  for(int i = 10; i <= 13; i++)
    gmshModelGeoMeshSetTransfiniteCurve(i, 10, "Progression", 1.0, &ierr);

  // The way triangles are generated can be controlled by specifying "Left",
  // "Right" or "Alternate" in `setTransfiniteSurface()' command.

  // Finally we apply an elliptic smoother to the grid to have a more regular
  // mesh:
  gmshOptionSetNumber("Mesh.Smoothing", 100, &ierr);

  gmshModelGeoSynchronize(&ierr);
  gmshModelMeshGenerate(2, &ierr);
  gmshWrite("t6.msh", &ierr);

  // Launch the GUI to see the results:
  int gui = 1;
  for(int i = 0; i < argc; i++) {
    if(!strcmp(argv[i], "-nopopup")) {
      gui = 0;
      break;
    }
  }
  if(gui) gmshFltkRun(&ierr);

  gmshFinalize(&ierr);
  return 0;
}
