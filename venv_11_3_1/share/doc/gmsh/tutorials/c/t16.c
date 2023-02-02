// -----------------------------------------------------------------------------
//
//  Gmsh C tutorial 16
//
//  Constructive Solid Geometry, OpenCASCADE geometry kernel
//
// -----------------------------------------------------------------------------

// Instead of constructing a model in a bottom-up fashion with Gmsh's built-in
// geometry kernel, starting with version 3 Gmsh allows you to directly use
// alternative geometry kernels. Here we will use the OpenCASCADE kernel.

#include <stdio.h>
#include <string.h>
#include <math.h>
#include <gmshc.h>

int main(int argc, char **argv)
{
  int ierr;

  gmshInitialize(argc, argv, 1, 0, &ierr);

  gmshModelAdd("t16", &ierr);

  // We first create two cubes:
  gmshModelOccAddBox(0, 0, 0, 1, 1, 1, 1, &ierr);
  if(ierr) {
    printf("Could not create OpenCASCADE shapes: bye!");
    return 0;
  }
  gmshModelOccAddBox(0, 0, 0, 0.5, 0.5, 0.5, 2, &ierr);

  // We apply a boolean difference to create the "cube minus one eigth" shape:
  const int o[] = {3, 1};
  const int t[] = {3, 2};
  gmshModelOccCut(o, sizeof(o) / sizeof(o[0]), t, sizeof(t) / sizeof(t[0]),
                  NULL, NULL, NULL, NULL, NULL, 3, 1, 1, &ierr);

  // Boolean operations with OpenCASCADE always create new entities. The
  // arguments `removeObject' and `removeTool' are set to `1', which will delete
  // the original entities.

  // We then create the five spheres:
  double x = 0, y = 0.75, z = 0, r = 0.09;
  int holes[10];
  for(int t = 1; t <= 5; t++) {
    x += 0.166;
    z += 0.166;
    gmshModelOccAddSphere(x, y, z, r, 3 + t, -M_PI / 2, M_PI / 2, 2 * M_PI, &ierr);
    holes[2 * (t - 1)] = 3;
    holes[2 * (t - 1) + 1] = 3 + t;
  }

  // If we had wanted five empty holes we would have used `gmshModelOccCut()'
  // again. Here we want five spherical inclusions, whose mesh should be
  // conformal with the mesh of the cube: we thus use `gmshModelOccFragment()',
  // which intersects all volumes in a conformal manner (without creating
  // duplicate interfaces):
  const int o2[] = {3, 3};
  int *ov, **ovv;
  size_t ov_n, *ovv_n, ovv_nn;
  gmshModelOccFragment(o2, sizeof(o) / sizeof(o[0]),
                       holes, sizeof(holes) / sizeof(holes[0]),
                       &ov, &ov_n, &ovv, &ovv_n, &ovv_nn, -1, 1, 1, &ierr);

  // ov contains all the generated entities of the same dimension as the input
  // entities:
  printf("fragment produced volumes: ");
  for(int i = 0; i < ov_n; i += 2)
    printf("(%d, %d) ", ov[i], ov[i + 1]);
  printf("\n");

  // ovv contains the parent-child relationships for all the input entities:
  for(size_t i = 0; i < ovv_nn; i++) {
    printf("parent (3, %d) -> child", !i ? o2[1] : holes[(i - 1) * 2 + 1]);
    for(size_t j = 0; j < ovv_n[i]; j += 2) {
      printf(" (%d, %d)", ovv[i][j], ovv[i][j + 1]);
    }
    printf("\n");
  }

  gmshModelOccSynchronize(&ierr);

  // When the boolean operation leads to simple modifications of entities, and
  // if one deletes the original entities, Gmsh tries to assign the same tag to
  // the new entities. (This behavior is governed by the
  // `Geometry.OCCBooleanPreserveNumbering' option.)

  // Here the `Physical Volume' definitions can thus be made for the 5 spheres
  // directly, as the five spheres (volumes 4, 5, 6, 7 and 8), which will be
  // deleted by the fragment operations, will be recreated identically (albeit
  // with new surfaces) with the same tags:
  for(int i = 1; i <= 5; i++) {
    const int gi[] = {3 + i};
    gmshModelAddPhysicalGroup(3, gi, sizeof(gi) / sizeof(gi[0]), i, "", &ierr);
  }

  // The tag of the cube will change though, so we need to access it
  // programmatically:
  const int g[] = {ov[ov_n - 1]};
  gmshModelAddPhysicalGroup(3, g, sizeof(g) / sizeof(g[0]), 10, "", &ierr);

  gmshFree(ov);
  for(int i = 0; i < ovv_nn; i++)
    gmshFree(ovv[i]);
  gmshFree(ovv_n);

  // Creating entities using constructive solid geometry is very powerful, but
  // can lead to practical issues for e.g. setting mesh sizes at points, or
  // identifying boundaries.

  // To identify points or other bounding entities you can take advantage of the
  // `gmshModelGetEntities()', `gmshModelGetBoundary()' and
  // `gmshModelGetEntitiesInBoundingBox()' functions:

  double lcar1 = .1;
  double lcar2 = .0005;
  double lcar3 = .055;

  // Assign a mesh size to all the points:
  gmshModelGetEntities(&ov, &ov_n, 0, &ierr);
  gmshModelMeshSetSize(ov, ov_n, lcar1, &ierr);
  gmshFree(ov);

  // Override this constraint on the points of the five spheres:
  gmshModelGetBoundary(holes, sizeof(holes) / sizeof(holes[0]),
                       &ov, &ov_n, 0, 0, 1, &ierr);
  gmshModelMeshSetSize(ov, ov_n, lcar3, &ierr);
  gmshFree(ov);

  // Select the corner point by searching for it geometrically:
  double eps = 1e-3;
  gmshModelGetEntitiesInBoundingBox(0.5 - eps, 0.5 - eps, 0.5 - eps,
                                    0.5 + eps, 0.5 + eps, 0.5 + eps,
                                    &ov, &ov_n, 0, &ierr);
  gmshModelMeshSetSize(ov, ov_n, lcar2, &ierr);
  gmshFree(ov);

  gmshModelMeshGenerate(3, &ierr);

  gmshWrite("t16.msh", &ierr);

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
