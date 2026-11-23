# Greeter - A trlcdoc Example for C with CMake and Ceedling

This example shows how [trlcdoc](https://github.com/nhjschulz/trlc-doc) builds the
project documentation of a C project from the configuration file,
[trlcdoc.yaml](trlcdoc.yaml). The project is a small program, `greet`, which greets
the user depending on the time of day. Its value is not the program, but the
documentation around it:

- requirements, architecture and test cases written in
  [TRLC](https://github.com/bmw-software-engineering/trlc),
- C code and [Ceedling](https://www.throwtheswitch.org/ceedling) unit tests
  (Unity and CMock) that trace to them with doxygen tags,
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
| SW-Test Results | Ceedling JUnit report of [test](test) | trlcdoc, pyTRLCConverter |
| SW-Tracing Report | all of the above | LOBSTER |
| Coverage Report | gcov data of the test run | Ceedling gcov plugin with gcovr |
| License | [LICENSE](LICENSE) | trlcdoc |

## Prerequisites

- Python 3.10 or newer
- A Java runtime for PlantUML and [Graphviz](https://graphviz.org) for the diagrams
- [doxygen](https://www.doxygen.nl) for the code tracing and the detail design
- GCC, and CMake 3.20 or newer to build the program
- Ruby 3 and Ceedling 1.1.9 for the unit tests
- [gcovr](https://gcovr.com) for the coverage report

Install trlcdoc and gcovr into a virtual environment, and Ceedling as Ruby gem:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install "trlcdoc>=0.6.0" gcovr
gem install ceedling -v 1.1.9
```

Some systems install gems into the user's gem folder, e.g. `~/.local/share/gem/ruby/3.4.0`.
Add its `bin` folder to the `PATH` if `ceedling` is not found
(`gem environment` shows the folder as `USER INSTALLATION DIRECTORY`).

The other tools come from the system package manager:

```bash
# Debian, Ubuntu
sudo apt install build-essential cmake doxygen graphviz default-jre ruby

# macOS
brew install cmake doxygen graphviz openjdk ruby
```

On Windows, install the [MSYS2](https://www.msys2.org) UCRT64 toolchain and run
the commands in its UCRT64 shell:

```bash
pacman -S mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-cmake mingw-w64-ucrt-x86_64-ruby \
          mingw-w64-ucrt-x86_64-doxygen mingw-w64-ucrt-x86_64-graphviz
```

On Windows, RubyGems installs Ceedling as `ceedling.bat`, which trlcdoc can only
start through the command interpreter. Change the test command in
[trlcdoc.yaml](trlcdoc.yaml) to `[cmd, /c, ceedling, gcov:all]`.

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
3. **tests** runs `ceedling gcov:all`, configured by [project.yml](project.yml).
   Ceedling builds and runs the Unity tests with coverage and writes the JUnit
   and the gcovr coverage report. trlcdoc converts the JUnit report into TRLC
   test result records.
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
| SW Code | functions in [src](src) | SW Requirement (`@implements`) |
| SW Test Case | `SwTestCase` records in [trlc/swe-test](trlc/swe-test) | SW Requirement (`verifies`) |
| SW Test Code | Unity test functions in [test](test) | SW Test Case (`@implements`) |
| SW Test Result | test results of the `tests` step | SW Test Case (`LOBSTER_TRACE`) |

Every requirement needs an architecture item, code and a test case. Every test
case needs test code and a test result.

### C code

The code names the requirements it implements in its doxygen comments.
lobster-doxygen reads them from the doxygen XML output:

```c
/**
 * @brief The main entry point of the application.
 * ...
 * @implements{SwRequirements.sw_req_cli}
 */
extern int main(int argc, char** argv);
```

`@justification{reason}` marks a function that intentionally traces to nothing.
Every source file needs a `@file` comment, otherwise doxygen drops the tags of its
functions. The aliases for both tags are defined in the [Doxyfile](Doxyfile),
which serves the trace level `SW Code` and the detail design pages.

### Ceedling tests

A test traces twice to its test cases: its doxygen comment for the `SW Test Code`
level, and `LOBSTER_TRACE()` for the test result:

```c
/**
 * @brief Test CLI.
 * ...
 * @implements{SwTests.tc_cli}
 */
void test_App_cli(void)
{
    LOBSTER_TRACE("SwTests.tc_cli");
    ...
}
```

`LOBSTER_TRACE()` from [test/support/Lobster.h](test/support/Lobster.h) writes
`lobster-trace: <test case>` with Unity's `TEST_MESSAGE()`. Ceedling's JUnit
report keeps these lines in the output of the test suite, each with the name of
its test. trlcdoc finds them with the pattern `tests.link.output` and writes one
`SwTestCaseResult` record per test. A test may record several test cases, so
`tests.link.array` is set and the model declares `relates SwTestCase [0 .. *]`.
[test/Doxyfile](test/Doxyfile) reads the test functions and leaves out the test
support files.

## Project layout

```text
CMakeLists.txt          greet program
project.yml             Ceedling: unit tests, mocks, JUnit and coverage report
Doxyfile                doxygen: trace level SW Code and detail design
trlcdoc.yaml            the documentation configuration
doc/mainpage.md         start page of the detail design
src/                    C sources
test/                   Unity tests and the test Doxyfile
test/support/           LOBSTER_TRACE() macro and test stubs
trlc/model/             TRLC model: requirement, architecture and test types
trlc/swe-req/           software requirements
trlc/swe-arch/          software architecture with PlantUML diagrams
trlc/swe-test/          software test cases
build/                  all generated files (not in git)
```

## Build and run the program

The program is built with CMake, the unit tests with Ceedling:

```bash
cmake -B build/cmake
cmake --build build/cmake
build/cmake/greet Alice

ceedling test:all
```

## License

The example is licensed under the BSD 3-Clause License, see [LICENSE](LICENSE).
