cmake_minimum_required(VERSION 3.1 FATAL_ERROR)

# TODO: Gmsh should create a cmake file when installing the lib, so all the
# external dependencies can be obtained automatically

# if CMAKE_BUILD_TYPE is specified use it; otherwise set the default
# build type to "RelWithDebInfo" ("-O2 -g" with gcc) prior to calling
# project()
if(DEFINED CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE ${CMAKE_BUILD_TYPE} CACHE STRING "Choose build type")
else()
  set(CMAKE_BUILD_TYPE RelWithDebInfo CACHE STRING "Choose build type")
endif()

project(api_examples CXX C)

set(CMAKE_CXX_STANDARD 11)

find_library(GMSH_LIB gmsh)
if(NOT GMSH_LIB)
  message(FATAL_ERROR "Could not find libgmsh")
endif()

find_path(GMSH_INC gmsh.h)
if(NOT GMSH_INC)
  message(FATAL_ERROR "Could not find gmsh.h")
endif()

if(GMSH_LIB MATCHES ".a") # FIXME - generalize this
  find_library(BLAS_LIB blas)
  if(BLAS_LIB)
    list(APPEND EXTRA_LIBS ${BLAS_LIB})
  endif()
  find_library(LAPACK_LIB lapack)
  if(LAPACK_LIB)
    list(APPEND EXTRA_LIBS ${LAPACK_LIB})
  endif()
endif()

if(WIN32 OR CYGWIN)
  list(APPEND EXTRA_LIBS winmm wsock32 ws2_32 psapi)
endif()

include_directories(${GMSH_INC})

include(CTest)

file(GLOB EXAMPLES *.cpp)
foreach(EXAMPLE ${EXAMPLES})
  get_filename_component(EXAMPLENAME ${EXAMPLE} NAME_WE)
  file(STRINGS ${EXAMPLE} EXAMPLE_CONTENTS NEWLINE_CONSUME)
  string(REGEX MATCH "::fltk::" GUI ${EXAMPLE_CONTENTS})
  if(GUI)
    add_executable(${EXAMPLENAME} WIN32 MACOSX_BUNDLE ${EXAMPLE})
    if(APPLE)
      file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/${EXAMPLENAME}.plist
           "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n\
            <!DOCTYPE plist PUBLIC \"-//Apple Computer//DTD PLIST 1.0//EN\"\
             \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n\
            <plist version=\"1.0\">\n\
              <dict>\n\
                <key>CFBundleName</key><string>${EXAMPLENAME}</string>\n\
                <key>CFBundleExecutable</key><string>${EXAMPLENAME}</string>\n\
                <key>CFBundlePackageType</key><string>APPL</string>\n\
                <key>CFBundleVersion</key><string>1.0.0</string>\n\
                <key>CFBundleShortVersionString</key><string>1.0.0</string>\n\
                <key>CFBundleIconFile</key><string></string>\n\
                <key>CFBundleSignature</key><string>????</string>\n\
                <key>CFBundleGetInfoString</key><string></string>\n\
                <key>CFBundleIdentifier</key><string></string>\n\
                <key>NSHighResolutionCapable</key><true/>\n\
              </dict>\n\
            </plist>")
      set_target_properties(${EXAMPLENAME} PROPERTIES MACOSX_BUNDLE_INFO_PLIST
                            ${CMAKE_CURRENT_BINARY_DIR}/${EXAMPLENAME}.plist)
      add_test(${EXAMPLENAME}_cpp ${EXAMPLENAME}.app/Contents/MacOS/${EXAMPLENAME} -nopopup)
    else()
      add_test(${EXAMPLENAME}_cpp ${EXAMPLENAME} -nopopup)
    endif()
  else()
    add_executable(${EXAMPLENAME} ${EXAMPLE})
    add_test(${EXAMPLENAME}_cpp ${EXAMPLENAME} -nopopup)
  endif()
  target_link_libraries(${EXAMPLENAME} ${GMSH_LIB} ${EXTRA_LIBS})
endforeach()

file(GLOB EXAMPLES *.c)
foreach(EXAMPLE ${EXAMPLES})
  get_filename_component(EXAMPLENAME ${EXAMPLE} NAME_WE)
  add_executable(${EXAMPLENAME}c ${EXAMPLE})
  target_link_libraries(${EXAMPLENAME}c ${GMSH_LIB} ${EXTRA_LIBS})
  add_test(${EXAMPLENAME}_c ${EXAMPLENAME}c -nopopup)
endforeach()

find_program(PYTHON python3)
if(PYTHON)
  file(GLOB EXAMPLES *.py)
  foreach(EXAMPLE ${EXAMPLES})
    get_filename_component(EXAMPLENAME ${EXAMPLE} NAME_WE)
    add_test(${EXAMPLENAME}_py ${PYTHON} ${EXAMPLE} -nopopup)
  endforeach()
endif()

find_program(JULIA julia)
if(JULIA)
  file(GLOB EXAMPLES *.jl)
  foreach(EXAMPLE ${EXAMPLES})
    get_filename_component(EXAMPLENAME ${EXAMPLE} NAME_WE)
    add_test(${EXAMPLENAME}_jl ${JULIA} ${EXAMPLE} -nopopup)
  endforeach()
endif()
