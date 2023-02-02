// -----------------------------------------------------------------------------
//
//  Gmsh C tutorial 2
//
//  Transformations, extruded geometries, volumes
//
// -----------------------------------------------------------------------------

#include <stdio.h>
#include <string.h>
#include <math.h>
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

  gmshModelGeoSynchronize(&ierr);

  const int g5[] = {1, 2, 4}, g6[] = {1};
  gmshModelAddPhysicalGroup(1, g5, sizeof(g5) / sizeof(g5[0]), 5, "", &ierr);
  gmshModelAddPhysicalGroup(2, g6, sizeof(g6) / sizeof(g6[0]), -1, "My surface", &ierr);

  // We can then add new points and curves in the same way as we did in
  // `t1.c':
  gmshModelGeoAddPoint(0, .4, 0, lc, 5, &ierr);
  gmshModelGeoAddLine(4, 5, 5, &ierr);

  // But Gmsh also provides tools to transform (translate, rotate, etc.)
  // elementary entities or copies of elementary entities.  Geometrical
  // transformations take a vector of pairs of integers as first argument, which
  // contains the list of entities, represented by (dimension, tag) pairs.  For
  // example, the point 5 (dimension=0, tag=5) can be moved by 0.02 to the left
  // (dx=-0.02, dy=0, dz=0) with
  const int t2[] = {0, 5};
  gmshModelGeoTranslate(t2, 2, -0.02, 0, 0, &ierr);

  // And it can be further rotated by -Pi/4 around (0, 0.3, 0) (with the
  // rotation along the z axis) with:
  gmshModelGeoRotate(t2, 2, 0, 0.3, 0, 0, 0, 1, -M_PI / 4, &ierr);

  // Note that there are no units in Gmsh: coordinates are just numbers - it's
  // up to the user to associate a meaning to them.

  // Point 3 can be duplicated and translated by 0.05 along the y axis by using
  // the `copy()' function, which takes a vector of (dim, tag) pairs as input,
  // and returns another vector of (dim, tag) pairs:
  const int iv[] = {0, 3};
  int *ov;
  size_t ov_n;
  gmshModelGeoCopy(iv, 2, &ov, &ov_n, &ierr);
  gmshModelGeoTranslate(ov, ov_n, 0, 0.05, 0, &ierr);

  // The new point tag is available in ov[0].second, and can be used to create
  // new lines:
  gmshModelGeoAddLine(3, ov[1], 7, &ierr);
  gmshModelGeoAddLine(ov[1], 5, 8, &ierr);

  // Output vectors are allocated with `gmshMalloc()' inside the C API, and
  // should be freed with `gmshFree()' when not used anymore:
  gmshFree(ov);

  // Note that in the C API, undesired output values can be ignored by passing a
  // NULL pointer. For example, to ignore the error flag, we can pass NULL as
  // the last argument:
  const int cl2[] = {5, -8, -7, 3};
  gmshModelGeoAddCurveLoop(cl2, sizeof(cl2) / sizeof(cl2[0]), 10, 0, NULL);

  const int s2[] = {10};
  gmshModelGeoAddPlaneSurface(s2, sizeof(s2) / sizeof(s2[0]), 11, &ierr);

  // In the same way, we can translate copies of the two surfaces 1 and 11 to
  // the right with the following command:
  const int iv2[] = {2, 1, 2, 11};
  gmshModelGeoCopy(iv2, 4, &ov, &ov_n, &ierr);
  gmshModelGeoTranslate(ov, ov_n, 0.12, 0, 0, &ierr);

  printf("New surfaces '%d' and '%d'\n", ov[1], ov[3]);

  // Volumes are the fourth type of elementary entities in Gmsh. In the same way
  // one defines curve loops to build surfaces, one has to define surface loops
  // (i.e. `shells') to build volumes. The following volume does not have holes
  // and thus consists of a single surface loop:
  gmshModelGeoAddPoint(0., 0.3, 0.12, lc, 100, &ierr);
  gmshModelGeoAddPoint(0.1, 0.3, 0.12, lc, 101, &ierr);
  gmshModelGeoAddPoint(0.1, 0.35, 0.12, lc, 102, &ierr);

  // We would like to retrieve the coordinates of point 5 to create point 103,
  // so we synchronize the model, and use `getValue()'
  gmshModelGeoSynchronize(&ierr);

  const double *param;
  const size_t param_n = 0;
  double *xyz;
  size_t xyz_n;
  gmshModelGetValue(0, 5, param, param_n, &xyz, &xyz_n, &ierr);
  gmshModelGeoAddPoint(xyz[0], xyz[1], 0.12, lc, 103, &ierr);
  gmshFree(xyz);

  gmshModelGeoAddLine(4, 100, 110, &ierr);
  gmshModelGeoAddLine(3, 101, 111, &ierr);
  gmshModelGeoAddLine(6, 102, 112, &ierr);
  gmshModelGeoAddLine(5, 103, 113, &ierr);
  gmshModelGeoAddLine(103, 100, 114, &ierr);
  gmshModelGeoAddLine(100, 101, 115, &ierr);
  gmshModelGeoAddLine(101, 102, 116, &ierr);
  gmshModelGeoAddLine(102, 103, 117, &ierr);

  const int cl3[] = {115, -111, 3, 110};
  gmshModelGeoAddCurveLoop(cl3, sizeof(cl3) / sizeof(cl3[0]), 118, 0, &ierr);
  const int s3[] = {118};
  gmshModelGeoAddPlaneSurface(s3, sizeof(s3) / sizeof(s3[0]), 119, &ierr);

  const int cl4[] = {111, 116, -112, -7};
  gmshModelGeoAddCurveLoop(cl4, sizeof(cl4) / sizeof(cl4[0]), 120, 0, &ierr);
  const int s4[] = {120};
  gmshModelGeoAddPlaneSurface(s4, sizeof(s4) / sizeof(s4[0]), 121, &ierr);

  const int cl5[] = {112, 117, -113, -8};
  gmshModelGeoAddCurveLoop(cl5, sizeof(cl5) / sizeof(cl5[0]), 122, 0, &ierr);
  const int s5[] = {122};
  gmshModelGeoAddPlaneSurface(s5, sizeof(s5) / sizeof(s5[0]), 123, &ierr);

  const int cl6[] = {114, -110, 5, 113};
  gmshModelGeoAddCurveLoop(cl6, sizeof(cl6) / sizeof(cl6[0]), 124, 0, &ierr);
  const int s6[] = {124};
  gmshModelGeoAddPlaneSurface(s6, sizeof(s6) / sizeof(s6[0]), 125, &ierr);

  const int cl7[] = {115, 116, 117, 114};
  gmshModelGeoAddCurveLoop(cl7, sizeof(cl7) / sizeof(cl7[0]), 126, 0, &ierr);
  const int s7[] = {126};
  gmshModelGeoAddPlaneSurface(s7, sizeof(s7) / sizeof(s7[0]), 127, &ierr);

  const int sl1[] = {127, 119, 121, 123, 125, 11};
  gmshModelGeoAddSurfaceLoop(sl1, sizeof(sl1) / sizeof(sl1[0]), 128, &ierr);
  const int v1[] = {128};
  gmshModelGeoAddVolume(v1, sizeof(v1) / sizeof(v1[0]), 129, &ierr);

  // When a volume can be extruded from a surface, it is usually easier to use
  // the `extrude()' function directly instead of creating all the points,
  // curves and surfaces by hand. For example, the following command extrudes
  // the surface 11 along the z axis and automatically creates a new volume (as
  // well as all the needed points, curves and surfaces). As expected, the
  // function takes a vector of (dim, tag) pairs as input as well as the
  // translation vector; since we don't plan to use the output vector of (dim,
  // tag) pairs, we pass NULL instead:
  const int *numElements;
  const size_t numElements_n = 0;
  const double *heights;
  const size_t heights_n = 0;
  const int recombine = 0;
  gmshModelGeoExtrude(&(ov[2]), 2, 0.0, 0.0, 0.12, NULL, NULL, numElements,
                      numElements_n, heights, heights_n, recombine, &ierr);

  // Mesh sizes associated to geometrical points can be set by passing a vector
  // of (dim, tag) pairs for the corresponding points:
  const int ss[] = {0, 103, 0, 105, 0, 109, 0, 102, 0, 28, 0, 24, 0, 6, 0, 5};
  gmshModelGeoMeshSetSize(ss, sizeof(ss) / sizeof(ss[0]), lc * 3, &ierr);

  // We finish by synchronizing the data from the built-in CAD kernel with the
  // Gmsh model:
  gmshModelGeoSynchronize(&ierr);

  // We group volumes 129 and 130 in a single physical group with tag `1' and
  // name "The volume":
  const int g7[] = {129, 130};
  gmshModelAddPhysicalGroup(3, g7, sizeof(g7) / sizeof(g7[0]), 1, "The volume", &ierr);

  // We finally generate and save the mesh:
  gmshModelMeshGenerate(3, &ierr);
  gmshWrite("t2.msh", &ierr);

  // Note that, if the transformation tools are handy to create complex
  // geometries, it is also sometimes useful to generate the `flat' geometry,
  // with an explicit representation of all the elementary entities.
  //
  // With the built-in CAD kernel, this can be achieved by saving the model in
  // the `Gmsh Unrolled GEO' format:
  //
  // gmshWrite("t2.geo_unrolled", &ierr);
  //
  // With the OpenCASCADE CAD kernel, unrolling the geometry can be achieved by
  // exporting in the `OpenCASCADE BRep' format:
  //
  // gmshWrite("t2.brep", &ierr);
  //
  // (OpenCASCADE geometries can also be exported as STEP files.)

  // It is important to note that Gmsh never translates geometry data into a
  // common representation: all the operations on a geometrical entity are
  // performed natively with the associated CAD kernel. Consequently, one cannot
  // export a geometry constructed with the built-in kernel as an OpenCASCADE
  // BRep file; or export an OpenCASCADE model as an Unrolled GEO file.

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
