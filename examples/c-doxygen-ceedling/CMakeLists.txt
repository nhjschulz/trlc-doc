# Greeter - a C example project using trlcdoc.
#
#   cmake -B build/cmake
#   cmake --build build/cmake
#
# The unit tests are built and run by Ceedling, see project.yml.

cmake_minimum_required(VERSION 3.20)

project(greeter LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

add_executable(greet
    src/App.c
    src/Greeter.c
    src/LocalTime.c
    src/Printer.c
    src/main.c
)
target_include_directories(greet PRIVATE src)
target_compile_options(greet PRIVATE
    $<$<C_COMPILER_ID:GNU,Clang,AppleClang>:-Wall -Wextra>
)
