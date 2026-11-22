# Greeter - A trlcdoc Example for Rust with cargo-nextest

This example shows how [trlcdoc](https://github.com/nhjschulz/trlc-doc) builds the
project documentation of a Rust project from the configuration file,
[trlcdoc.yaml](trlcdoc.yaml). The project is a small program, `greet`, which greets
the user depending on the time of day. Its value is not the program, but the
documentation around it:

- requirements, architecture and test cases written in
  [TRLC](https://github.com/bmw-software-engineering/trlc),
- Rust code and unit tests that name the requirements and test cases they
  implement,
- test results, coverage and a [LOBSTER](https://github.com/bmw-software-engineering/lobster)
  tracing report that shows whether every requirement is tested.

`trlcdoc` turns all of this into one HTML site, with nothing but the configuration
and the project's own sources.

**Status:** work in progress. The tracing report doesn't include the Rust code
yet, see [Code tracing](#code-tracing).

## The generated site

| Page | Source | Created by |
| --- | --- | --- |
| About the Example | this README | Sphinx with MyST |
| SW-Requirements | [trlc/swe-req](trlc/swe-req) | pyTRLCConverter |
| SW-Architecture | [trlc/swe-arch](trlc/swe-arch), with PlantUML diagrams | pyTRLCConverter, PlantUML |
| SW-Tests | [trlc/swe-test](trlc/swe-test) | pyTRLCConverter |
| SW-Test Results | JUnit report of the unit tests in [src](src) | cargo-nextest, trlcdoc, pyTRLCConverter |
| SW-Tracing Report | all of the above | LOBSTER |
| Coverage Report | coverage of the unit test run | cargo-llvm-cov |
| License | [LICENSE](LICENSE) | trlcdoc |

## Prerequisites

- Python 3.10 or newer
- A Java runtime for PlantUML and [Graphviz](https://graphviz.org) for the diagrams
- Rust 1.85 or newer with cargo, installed with [rustup](https://rustup.rs)
- [cargo-nextest](https://nexte.st) for the JUnit report of the tests
- [cargo-llvm-cov](https://github.com/taiki-e/cargo-llvm-cov) and the rustup
  component `llvm-tools` for the coverage report

Install trlcdoc into a virtual environment, and the cargo tools with cargo:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install trlcdoc
cargo install --locked cargo-nextest cargo-llvm-cov
rustup component add llvm-tools
```

Java and Graphviz come from the system package manager, e.g.
`sudo apt install default-jre graphviz` on Debian and Ubuntu.

## Build the documentation

In this folder:

```bash
trlcdoc              # all steps, the site is written to build/trlcdoc/html
trlcdoc all show     # ... and open it in the web browser
```

trlcdoc finds `trlcdoc.yaml` in the current folder and runs its steps in this
order. Each step's configuration is in [trlcdoc.yaml](trlcdoc.yaml):

1. **check** validates the configuration and the files it refers to.
2. **plantuml** downloads the PlantUML jar into the build folder.
3. **tests** runs `cargo llvm-cov nextest --profile ci --html`. cargo-llvm-cov
   builds the crate with coverage and runs the unit tests with cargo-nextest,
   which writes the JUnit report. trlcdoc converts it into TRLC test result
   records.
4. **convert** turns the TRLC requirements, architecture, test cases and test
   results into reStructuredText with the built-in pyTRLCConverter converters.
5. **trace** extracts the trace items of every level, see below, and creates
   the LOBSTER tracing report.
6. **html** builds the Sphinx site.

The exit code is `0` if everything is fine, `1` if tests fail or requirements are
not traced, and `2` on errors. A step can also run alone, e.g. `trlcdoc tests trace`.

## Traceability

The tracing report checks these links:

| Level | Items from | Traces to |
| --- | --- | --- |
| SW Requirement | `SwReq` records in [trlc/swe-req](trlc/swe-req) | |
| SW Constraint | `SwConstraint` records in [trlc/swe-req](trlc/swe-req) | |
| SW Architecture | `SwArchSpec` records in [trlc/swe-arch](trlc/swe-arch) | SW Requirement, SW Constraint (`satisfies`) |
| SW Test Case | `SwTestCase` records in [trlc/swe-test](trlc/swe-test) | SW Requirement (`verifies`) |
| SW Test Result | test results of the `tests` step | SW Test Case (`lobster_trace!`) |

Every requirement needs an architecture item and a test case. Every test case
needs a test result.

### Unit tests

The unit tests are in the `tests` module of each source file, the usual place for
Rust unit tests. A test writes its test cases to its output with the
`lobster_trace!` macro of [src/main.rs](src/main.rs):

```rust
/// The application runs with a user name argument.
#[test]
fn cli() {
    // lobster-trace: SwTests.tc_cli
    lobster_trace!("SwTests.tc_cli");
    assert_eq!(run_with(&["Alice"]).code, ExitCode::SUCCESS);
}
```

The nextest profile `ci` in [.config/nextest.toml](.config/nextest.toml) keeps
the output of every test in the JUnit report, also of the passed ones. trlcdoc
finds the `lobster-trace: <test case>` lines with the pattern
`tests.link.output`, and writes one `SwTestCaseResult` record per test. A test
may record several test cases, so `tests.link.array` is set and the model
declares `relates SwTestCase [0 .. *]`.

The test results don't come from `cargo test`: it has no JUnit report in stable
Rust.

### Code tracing

The functions name the requirements they implement with a comment in their
body, the syntax of [lobster-rust](https://github.com/NewTec-GmbH/lobster-rust):

```rust
/// Selects the salutation for an hour of the day.
fn salutation(&self, hour: u32) -> &'static str {
    // lobster-trace: SwRequirements.sw_func_daytime_greeting_selection
    ...
}
```

The tests carry the same comment with their test case, for a level of test code.
`// lobster-exclude: <reason>` marks a function that traces to nothing.

These comments are not part of the tracing report yet: trlcdoc has no
lobster-rust extractor, and lobster-rust doesn't yet write source file paths
or separate tests from code. Once both are available, the levels `SW Code` and
`SW Test Code` will be added, like in the C and C++ examples.

## Project layout

```text
Cargo.toml              greeter crate with the greet program
.config/nextest.toml    cargo-nextest: JUnit report with the test output
trlcdoc.yaml            the documentation configuration
src/main.rs             program entry point and the lobster_trace! macro
src/app.rs              command line arguments and output, with tests
src/greeter.rs          greeting selection, with tests
src/environment.rs      local time and login name, with tests
trlc/model/             TRLC model: requirement, architecture and test types
trlc/swe-req/           software requirements
trlc/swe-arch/          software architecture with PlantUML diagrams
trlc/swe-test/          software test cases
target/, build/         all generated files (not in git)
```

## Build and run the program

```bash
cargo run -- Alice
cargo test
```

## License

The example is licensed under the BSD 3-Clause License, see [LICENSE](LICENSE).
