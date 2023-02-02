This directory contains the Gmsh Julia tutorials, written using the Gmsh Julia
API.

To run the Julia tutorials, you need the Gmsh dynamic library and the Julia
module (`gmsh.jl'). These can be either obtained

- from the binary Software Development Kit (SDK) available on the Gmsh website
  https://gmsh.info/bin/, for Windows, Linux and macOS. Download and uncompress
  the relevant gmsh*-sdk.* archive for your operating system and add the "lib"
  directory from the SDK to JULIA_LOAD_PATH, e.g., if you are currently in the
  root directory of the SDK:

    export JULIA_LOAD_PATH=${JULIA_LOAD_PATH}:${PWD}/lib

- by compiling the Gmsh source code. Follow these steps in the top-level
  directory of the Gmsh source code:

    mkdir build
    cd build
    cmake -DENABLE_BUILD_DYNAMIC=1 ..
    make
    make install
    cd ..

  Add the installation directory (by default /usr/local/lib) to JULIA_LOAD_PATH,
  e.g.

    export JULIA_LOAD_PATH=${JULIA_LOAD_PATH}:/usr/local/lib

You can then run e.g. "julia t1.jl"

For other Julia API examples, see the `examples/api' directory.
