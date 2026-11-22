# Build and run the googletest tests with coverage, the test command of trlcdoc.yaml.
#
#   cmake -P tools/run_tests.cmake
#
# Writes into build/test:
#   greet_test.xml   googletest XML report with the LOBSTER_TRACE() test case links
#   coverage/        gcovr HTML coverage report of the src folder
#
# Needs CMake, a GCC or Clang compiler and gcovr (pip install gcovr).

cmake_minimum_required(VERSION 3.20)

get_filename_component(ROOT "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
set(BUILD "${ROOT}/build/test")

find_program(GCOVR gcovr REQUIRED)

execute_process(
    COMMAND "${CMAKE_COMMAND}" -S "${ROOT}" -B "${BUILD}" -DCMAKE_BUILD_TYPE=Debug -DGREETER_COVERAGE=ON
    COMMAND_ERROR_IS_FATAL ANY
)
execute_process(
    COMMAND "${CMAKE_COMMAND}" --build "${BUILD}"
    COMMAND_ERROR_IS_FATAL ANY
)

# Results of a previous run must not survive a run that fails early.
file(GLOB_RECURSE STALE "${BUILD}/*.gcda")
file(REMOVE ${STALE} "${BUILD}/greet_test.xml")
file(REMOVE_RECURSE "${BUILD}/coverage")
file(MAKE_DIRECTORY "${BUILD}/coverage")

# Failed tests are no error here: trlcdoc takes the results from the XML report.
execute_process(
    COMMAND "${CMAKE_CTEST_COMMAND}" --test-dir "${BUILD}" --output-on-failure
    RESULT_VARIABLE TEST_RESULT
)
if(NOT TEST_RESULT EQUAL 0)
    message(WARNING "Some tests failed, see ${BUILD}/greet_test.xml")
endif()

execute_process(
    COMMAND "${GCOVR}" --root "${ROOT}" --filter "${ROOT}/src/" --print-summary
            --html-details "${BUILD}/coverage/index.html" "${BUILD}"
    COMMAND_ERROR_IS_FATAL ANY
)
