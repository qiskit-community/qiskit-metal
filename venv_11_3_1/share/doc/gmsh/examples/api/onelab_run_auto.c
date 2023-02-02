#include <stdio.h>
#include <stdlib.h>
#include <gmshc.h>

#define chk(ierr)                                               \
  if(ierr != 0){                                                \
    fprintf(stderr, "Error on line %i in function '%s': "       \
            "gmsh function returned non-zero error code: %i\n", \
            __LINE__, __FUNCTION__, ierr);                      \
    gmshFinalize(NULL);                                         \
    exit(ierr);                                                 \
  }

int main(int argc, char **argv)
{
  int ierr;
  char *json;

  if(argc < 2){
    printf("Usage: %s file [options]\n", argv[0]);
    return 0;
  }

  gmshInitialize(0, 0, 1, 0, &ierr); chk(ierr);

  gmshOpen(argv[1], &ierr); chk(ierr);

  gmshOnelabRun("", "", &ierr); chk(ierr);

  gmshOnelabGet(&json, "json", "", &ierr); chk(ierr);
  printf("%s", json);

  gmshFinalize(&ierr); chk(ierr);

  return 0;
}
