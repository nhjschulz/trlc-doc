# Greeter - a C++ example project using trlcdoc.
#
#   cmake -B build/cmake
#   cmake --build build/cmake
#   ctest --test-dir build/cmake --output-on-failure

cmake_minimum_required(VERSION 3.20)

project(greeter LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(GREETER_COVERAGE "Instrument the greeter sources for gcov coverage (GCC or Clang)" OFF)

include(CTest)

# Application logic, shared by the program and the tests.
add_library(greeter_core STATIC
    src/App.cpp
    src/Greeter.cpp
    src/LocalTime.cpp
)
target_include_directories(greeter_core PUBLIC src)
target_compile_options(greeter_core PRIVATE
    $<$<CXX_COMPILER_ID:GNU,Clang,AppleClang>:-Wall -Wextra>
)
if(GREETER_COVERAGE)
    target_compile_options(greeter_core PRIVATE --coverage)
    target_link_options(greeter_core PUBLIC --coverage)
endif()

# The greet program.
add_executable(greet src/main.cpp)
target_link_libraries(greet PRIVATE greeter_core)

if(BUILD_TESTING)
    # googletest with googlemock: the installed package, otherwise downloaded.
    find_package(GTest 1.11 CONFIG QUIET)
    if(NOT GTest_FOUND)
        include(FetchContent)
        FetchContent_Declare(googletest
            URL https://github.com/google/googletest/releases/download/v1.17.0/googletest-1.17.0.tar.gz
            DOWNLOAD_EXTRACT_TIMESTAMP ON
        )
        # Use the same runtime library as the project on Windows.
        set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
        set(INSTALL_GTEST OFF CACHE BOOL "" FORCE)
        FetchContent_MakeAvailable(googletest)
    endif()

    # The test program: main.cpp built with TEST runs the googletest tests.
    add_executable(greet_test
        src/main.cpp
        test/testCmdLine.cpp
        test/testGreet.cpp
    )
    target_compile_definitions(greet_test PRIVATE TEST)
    target_include_directories(greet_test PRIVATE test)
    target_link_libraries(greet_test PRIVATE greeter_core GTest::gtest GTest::gmock)

    # One test run with the googletest XML report. Unlike the JUnit report of ctest,
    # it contains the test case links recorded by LOBSTER_TRACE().
    add_test(NAME greet_test
        COMMAND greet_test --gtest_output=xml:${CMAKE_BINARY_DIR}/greet_test.xml
    )
endif()
