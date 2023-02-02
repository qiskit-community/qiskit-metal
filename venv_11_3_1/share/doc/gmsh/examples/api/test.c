#include <stdio.h>
#include <stdlib.h>
#include "gmshc.h"

#define chk(ierr)                                               \
  if(ierr != 0){                                                \
    fprintf(stderr, "Error on line %i in function '%s': "       \
            "gmsh function returned non-zero error code: %i\n", \
            __LINE__, __FUNCTION__, ierr);                      \
    gmshFinalize(NULL);                                         \
    exit(0 /* ierr  --- for ctest */);                          \
  }

void genGeometry() {
  int ierr;
  gmshModelAdd("square",&ierr);chk(ierr);
  gmshModelGeoAddPoint(0,0,0,0.1,1,&ierr);chk(ierr);
  gmshModelGeoAddPoint(1,0,0,0.1,2,&ierr);chk(ierr);
  gmshModelGeoAddPoint(1,1,0,0.1,3,&ierr);chk(ierr);
  gmshModelGeoAddPoint(0,1,0,0.1,4,&ierr);chk(ierr);
  gmshModelGeoAddLine(1,2,1,&ierr); chk(ierr);
  gmshModelGeoAddLine(2,3,2,&ierr); chk(ierr);
  gmshModelGeoAddLine(3,4,3,&ierr); chk(ierr);
  // try automatic assignement of tag
  int line4 = gmshModelGeoAddLine(4,1,-1,&ierr); chk(ierr);
  printf("line4 received tag %i\n\n", line4);
  int ll[] = {1,2,3,line4};
  gmshModelGeoAddCurveLoop(ll,4,1,0,&ierr); chk(ierr);
  int s[] = {1};
  gmshModelGeoAddPlaneSurface(ll,1,6,&ierr); chk(ierr);
  gmshModelGeoSynchronize(&ierr); chk(ierr);
}

void printMesh() {
  int ierr;
  int *dimTags;
  size_t ndimTags;

  gmshModelGetEntities(&dimTags, &ndimTags, -1,&ierr); chk(ierr);

  for (size_t ie = 0; ie < ndimTags/2; ++ie) {
    int *types;
    size_t **elementTags, **vertexTags;
    size_t ntypes, *nelementTags, nnelementTags, *nvertexTags, nnvertexTags;

    gmshModelMeshGetElements(&types, &ntypes, &elementTags, &nelementTags,
                             &nnelementTags, &vertexTags, &nvertexTags,
                             &nnvertexTags,dimTags[ie*2+0], dimTags[ie*2+1],
                             &ierr); chk(ierr);

    printf("entity %i of dim %i\n", dimTags[ie*2+1], dimTags[ie*2+0]);
    for (size_t i = 0; i < nnelementTags; ++i) {
      printf("  %lu elements of type %i : ", nelementTags[i], types[i]);
      size_t nnodesbyel = nvertexTags[i]/nelementTags[i];
      for (size_t j = 0; j < nelementTags[i] && j < 3; ++j) {
        printf("%lu ( ", elementTags[i][j]);
        for (size_t k = 0; k < nnodesbyel; ++k)
          printf("%lu ", vertexTags[i][j*nnodesbyel+k]);
        printf(") ");
      }
      if (nelementTags[i] > 3)
        printf("...");
      printf("\n");
    }

    gmshFree(types);
    for (size_t i = 0; i < nnelementTags; ++i)
      gmshFree(elementTags[i]);
    for (size_t i = 0; i < nnvertexTags; ++i)
      gmshFree(vertexTags[i]);
    gmshFree(nelementTags);
    gmshFree(nvertexTags);
  }
  gmshFree(dimTags);
}

void genError() {
  int ierr;
  printf("\n** generate an error **\n");
  gmshModelMeshGetElements(NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,
                           999, 999, &ierr); chk(ierr);
}

int main(int argc, char **argv) {
  int ierr;
  gmshInitialize(argc, argv, 1, 0, &ierr); chk(ierr);
  genGeometry();
  gmshModelMeshGenerate(2,&ierr); chk(ierr);
  gmshWrite("square.msh",&ierr); chk(ierr);
  printMesh();
  genError();
  gmshFinalize(&ierr); chk(ierr);
}
