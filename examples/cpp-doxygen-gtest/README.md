# Greeter - A trlcdoc Example for C++ with CMake and googletest

This example shows how [trlcdoc](https://github.com/nhjschulz/trlc-doc) builds the
project documentation of a C++ project from the configuration file,
[trlcdoc.yaml](trlcdoc.yaml). The project is a small program, `greet`, which greets
the user depending on the time of day. Its value is not the program, but the
documentation around it:

- requirements, architecture and test cases written in
  [TRLC](https://github.com/bmw-software-engineering/trlc),
- C++ code and googletest tests that trace to them with doxygen tags,
- test results, coverage and a [LOBSTER](https://github.com/bmw-software-engineering/lobster)
  tracing report that shows whether every requirement is implemented and tested.

`trlcdoc` turns all of this into one HTML site, with nothing but the configuration
and the project's own sources.

## The generated site

| Page | Source | Created by |
| --- | --- | --- |
| About the Example | this README | Sphinx with MyST |
| SW-Requirements | [trlc/swe-req](trlc/swe-req) | pyTRLCConverter |
| SW-Architecture | [trlc/swe-arch](trlc/swe-arch), with PlantUML diagrams | pyTRLCConverter, PlantUML |
| SW-Detail Design | comments in [src](src) | doxygen, configured by [Doxyfile](Doxyfile) |
| SW-Tests | [trlc/swe-test](trlc/swe-test) | pyTRLCConverter |
| SW-Test Results | googletest XML report of [test](test) | trlcdoc, pyTRLCConverter |
| SW-Tracing Report | all of the above | LOBSTER |
| Coverage Report | gcov data of the test run | gcovr |
| License | [LICENSE](LICENSE) | trlcdoc |

## Prerequisites

- Python 3.10 or newer
- A Java runtime for PlantUML and [Graphviz](https://graphviz.org) for the diagrams
- [doxygen](https://www.doxygen.nl) for the code tracing and the detail design
- CMake 3.20 or newer and a C++17 compiler, GCC or Clang
- [gcovr](https://gcovr.com) for the coverage report
- googletest with googlemock, optional: without an installed googletest, CMake
  downloads it

Install trlcdoc and gcovr into a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install trlcdoc gcovr
```

The example needs a trlcdoc release newer than 0.5.0, which links googletest
results by their test property alone. The other tools come from the system package manager:

```bash
# Debian, Ubuntu
sudo apt install build-essential cmake doxygen graphviz default-jre libgtest-dev libgmock-dev

# macOS
brew install cmake doxygen graphviz openjdk googletest
```

On Windows, install the [MSYS2](https://www.msys2.org) UCRT64 toolchain and run
the commands in its UCRT64 shell:

```bash
pacman -S mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-cmake mingw-w64-ucrt-x86_64-gtest \
          mingw-w64-ucrt-x86_64-doxygen mingw-w64-ucrt-x86_64-graphviz
```

## Build the documentation

In this folder:

```bash
trlcdoc              # all steps, the site is written to build/trlcdoc/html
trlcdoc all show     # ... and open it in the web browser
trlcdoc --online     # tracing report with links to the repository instead of local files
```

trlcdoc finds `trlcdoc.yaml` in the current folder and runs its steps in this
order. Each step's configuration is in [trlcdoc.yaml](trlcdoc.yaml):

1. **check** validates the configuration and the files it refers to.
2. **plantuml** downloads the PlantUML jar into the build folder.
3. **tests** runs [tools/run_tests.cmake](tools/run_tests.cmake), which builds the
   project with coverage, runs the googletest tests and creates the coverage report.
   trlcdoc converts the googletest XML report into TRLC test result records.
4. **convert** turns the TRLC requirements, architecture, test cases and test
   results into reStructuredText with the built-in pyTRLCConverter converters.
5. **trace** extracts the trace items of every level, see below, and creates
   the LOBSTER tracing report.
6. **html** runs doxygen for the detail design and builds the Sphinx site.

The exit code is `0` if everything is fine, `1` if tests fail or requirements are
not traced, and `2` on errors. A step can also run alone, e.g. `trlcdoc tests trace`.

## Traceability

The tracing report checks these links:

| Level | Items from | Traces to |
| --- | --- | --- |
| SW Requirement | `SwReq` records in [trlc/swe-req](trlc/swe-req) | |
| SW Constraint | `SwConstraint` records in [trlc/swe-req](trlc/swe-req) | |
| SW Architecture | `SwArchSpec` records in [trlc/swe-arch](trlc/swe-arch) | SW Requirement, SW Constraint (`satisfies`) |
| SW Code | functions and classes in [src](src) | SW Requirement (`@implements`) |
| SW Test Case | `SwTestCase` records in [trlc/swe-test](trlc/swe-test) | SW Requirement (`verifies`) |
| SW Test Code | googletest tests in [test](test) | SW Test Case (`@implements`) |
| SW Test Result | test results of the `tests` step | SW Test Case (`LOBSTER_TRACE`) |

Every requirement needs an architecture item, code and a test case. Every test
case needs test code and a test result.

### C++ code

The code names the requirements it implements in its doxygen comments.
lobster-doxygen reads them from the doxygen XML output:

```cpp
/**
 * @brief Greet the given user dependent on the current time.
 * ...
 * @implements{SwRequirements.sw_req_cli_default_name}
 * @implements{SwRequirements.sw_func_morning_time_greeting}
 * ...
 */
std::string greet(const char* userName);
```

`@justification{reason}` marks an item that intentionally traces to nothing.
Every source file needs a `@file` comment, otherwise doxygen drops the tags of its
functions. The aliases for both tags are defined in the [Doxyfile](Doxyfile),
which serves the trace level `SW Code` and the detail design pages.

### googletest tests

A test traces twice to its test case: its doxygen comment for the `SW Test Code`
level, and `LOBSTER_TRACE()` for the test result:

```cpp
/**
 * @brief Test morning time greeting.
 *
 * @implements{SwTests.tc_greet_morning_time_greeting}
 */
TEST(TSGreet, MorningTimeGreeting)
{
    LOBSTER_TRACE("SwTests.tc_greet_morning_time_greeting");
    ...
}
```

`LOBSTER_TRACE()` from [test/lobster_gtest.h](test/lobster_gtest.h) records the
test case as test property `lobster-tracing`, which googletest writes into its XML
report. trlcdoc links each result by this property (`tests.link.property`) and
writes it as `SwTestCaseResult` record. [test/Doxyfile](test/Doxyfile) turns each
`TEST(suite, name)` into a function for doxygen, so the tags of its comment belong
to the test.

The test command must write the googletest report with `--gtest_output=xml`, see
[CMakeLists.txt](CMakeLists.txt). The JUnit report of `ctest --output-junit` does
not contain the test properties.

## Project layout

```text
CMakeLists.txt          greet program and greet_test googletest program
Doxyfile                doxygen: trace level SW Code and detail design
trlcdoc.yaml            the documentation configuration
doc/mainpage.md         start page of the detail design
src/                    C++ sources
test/                   googletest tests, mocks and the test Doxyfile
tools/run_tests.cmake   test command of trlcdoc: build, test, coverage
trlc/model/             TRLC model: requirement, architecture and test types
trlc/swe-req/           software requirements
trlc/swe-arch/          software architecture with PlantUML diagrams
trlc/swe-test/          software test cases
build/                  all generated files (not in git)
```

## Build and run the program

The program itself is built with CMake as usual:

```bash
cmake -B build/cmake
cmake --build build/cmake
ctest --test-dir build/cmake --output-on-failure
build/cmake/greet Alice
```

## License

The example is licensed under the BSD 3-Clause License, see [LICENSE](LICENSE).
[test/lobster_gtest.h](test/lobster_gtest.h) is public domain, taken from
[LOBSTER](https://github.com/bmw-software-engineering/lobster/blob/main/support/gtest/include/lobster_gtest.h).
