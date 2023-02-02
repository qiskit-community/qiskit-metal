This directory contains the Gmsh C++ tutorials, written using the Gmsh C++ API.

To compile and run the C++ tutorials, you need the Gmsh dynamic library and the
associated header file (`gmsh.h'). These can be either obtained

- from the binary Software Development Kit (SDK) available on the Gmsh website
  https://gmsh.info/bin/, for Windows, Linux and macOS. Download and uncompress
  the relevant gmsh*-sdk.* archive for your operating system. To compile the
  first tutorial, assuming that you are currently in the root directory of the
  SDK and that you are using the g++ compiler:

    g++ -o t1 -Iinclude share/doc/gmsh/tutorials/c++/t1.cpp -Llib -lgmsh

  Then run

    ./t1

  If your compiler has a different ABI than the compiler used to generate the
  binary SDK (see the top-level `README.txt' file in the SDK for additional
  information), you should use the `gmsh.h_cwrap' header instead of `gmsh.h'.
  For example, to compile a C++ example with Microsoft Visual Studio 2017 in the
  Visual Studio shell:

    C:\gmsh-git-Windows64-sdk> ren include\gmsh.h gmsh.h_original
    C:\gmsh-git-Windows64-sdk> ren include\gmsh.h_cwrap gmsh.h
    C:\gmsh-git-Windows64-sdk> cl /Iinclude share\doc\gmsh\tutorial\c++\t1.cpp lib\gmsh.lib
    C:\gmsh-git-Windows64-sdk> cd lib
    C:\gmsh-git-Windows64-sdk\lib> ..\t1.exe

- by compiling the Gmsh source code. Follow these steps in the top-level
  directory of the Gmsh source code:

    mkdir build
    cd build
    cmake -DENABLE_BUILD_DYNAMIC=1 ..
    make
    make install
    cd ..

  Then, assuming that you are using the g++ compiler:

    g++ -o t1 t1.cpp -lgmsh
    ./t1

For other C++ API examples, see the `examples/api' directory.
