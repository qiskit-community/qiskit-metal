#include <gmshc.h>

int main(int argc, char **argv)
{
  int ierr;
  gmshInitialize(argc, argv, 1, 0, &ierr);
  gmshModelAdd("square", &ierr);
  gmshModelGeoAddPoint(0, 0, 0, 0.1, 1, &ierr);
  gmshModelGeoAddPoint(1, 0, 0, 0.1, 2, &ierr);
  gmshModelGeoAddPoint(1, 1, 0, 0.1, 3, &ierr);
  gmshModelGeoAddPoint(0, 1, 0, 0.1, 4, &ierr);
  gmshModelGeoAddLine(1, 2, 1, &ierr);
  gmshModelGeoAddLine(2, 3, 2, &ierr);
  gmshModelGeoAddLine(3, 4, 3, &ierr);
  // try automatic assignement of tag
  int line4 = gmshModelGeoAddLine(4, 1, -1, &ierr);
  int ll[] = {1, 2, 3, line4};
  gmshModelGeoAddCurveLoop(ll, 4, 1, 0, &ierr);
  int s[]= { 1 };
  gmshModelGeoAddPlaneSurface(s, 1, 6, &ierr);
  gmshModelGeoSynchronize(&ierr);
  gmshModelMeshGenerate(2, &ierr);
  gmshWrite("square.msh", &ierr);
  return 0;
};
