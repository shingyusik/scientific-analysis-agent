# Manually find VTK headers and libraries in Python environment
find_package(Python COMPONENTS Interpreter REQUIRED)

execute_process(
    COMMAND "${Python_EXECUTABLE}" -c "import vtkmodules; import os; print(os.path.dirname(vtkmodules.__file__))"
    OUTPUT_VARIABLE VTK_PYTHON_PATH
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

if (EXISTS "${VTK_PYTHON_PATH}")
    message(STATUS "Found VTK in Python: ${VTK_PYTHON_PATH}")
    # Add include directories
    # Usually in vtkmodules/include or ../include/vtk-x.x
    # BUT pip vtk binary wheels often DON'T include headers!
    # If headers are missing, we cannot build.
    # We must check if headers exist.
    
    # Try to find valid include dir
    file(GLOB VTK_INCLUDE_CANDIDATES 
        "${VTK_PYTHON_PATH}/../../include/vtk-*"
        "${VTK_PYTHON_PATH}/include"
    )
    
    if (VTK_INCLUDE_CANDIDATES)
        list(GET VTK_INCLUDE_CANDIDATES 0 VTK_INCLUDE_DIR)
        message(STATUS "Assuming VTK include dir: ${VTK_INCLUDE_DIR}")
        include_directories(${VTK_INCLUDE_DIR})
    else()
        message(WARNING "VTK headers not found in Python package. PIP wheels might be missing headers. You may need to install VTK SDK system-wide or use 'conda install vtk' which usually includes headers, or build VTK from source.")
    endif()

    # Link libraries - for now, we might rely on dynamic loading or find .lib files
    file(GLOB VTK_LIBS "${VTK_PYTHON_PATH}/../../libs/vtk*.lib") # Windows specific
    if (VTK_LIBS)
        link_libraries(${VTK_LIBS})
    endif()

else()
    message(WARNING "VTK python module not found for path estimation.")
endif()

# We still try standard find_package as a backup or primary
find_package(VTK QUIET)
if (NOT VTK_FOUND)
    message(STATUS "Standard find_package(VTK) failed. Relying on manual path/header usage if successful.")
endif()

pybind11_add_module(sa_engine engine.cpp)

target_link_libraries(sa_engine PRIVATE ${VTK_LIBRARIES})
target_include_directories(sa_engine PRIVATE ${VTK_INCLUDE_DIRS})

# Install the module to the python package directory or directly to site-packages
# scikit-build-core handles installation if we set it up right.
install(TARGETS sa_engine DESTINATION .)
