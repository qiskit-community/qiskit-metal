This directory contains C versions of some of the tutorials, written using the
Gmsh API.

To compile and run the C tutorials, you need the Gmsh dynamic library and the
associated header file (`gmshc.h'). These can be either obtained

- from the binary Software Development Kit (SDK) available on the Gmsh website
  https://gmsh.info/bin/, for Windows, Linux and macOS. Download and uncompress
  the relevant gmsh*-sdk.* archive for your operating system. To compile the
  first tutorial, assuming that you are currently in the root directory of the
  SDK and that you are using the gcc compiler:

    gcc -o t1 -Iinclude share/doc/gmsh/tutorials/c/t1.c -Llib -lgmsh

  Then run

    ./t1

- by compiling the Gmsh source code. Follow these steps in the top-level
  directory of the Gmsh source code:

    mkdir build
    cd build
    cmake -DENABLE_BUILD_DYNAMIC=1 ..
    make
    make install
    cd ..

  Then, assuming that you are using the gcc compiler:

    gcc -o t1 t1.c -lgmsh
    ./t1

For other C API examples, see the `examples/api' directory.
