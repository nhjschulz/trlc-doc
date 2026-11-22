//! The command line application: argument handling and output.

use std::ffi::OsString;
use std::io::Write;
use std::process::ExitCode;

use clap::Parser;
use clap::error::ErrorKind;

use crate::environment::Environment;
use crate::greeter::{Greeter, Thresholds};

/// Exit code for wrong command line arguments, as used by clap.
const USAGE_ERROR: u8 = 2;

/// A Rust CLI tool to greet a user considering the time.
#[derive(Parser, Debug)]
#[command(name = "greet", version, after_help = "Copyright (c) 2025 NewTec GmbH")]
struct Args {
    // lobster-trace: SwRequirements.sw_req_cli_user_name
    // lobster-trace: SwRequirements.sw_req_cli_help
    /// User name to greet, defaults to the login name.
    name: Option<String>,
}

/// Runs the application: greets the user, or shows the help or a usage error.
///
/// The output goes to `out`, errors to `err`.
pub fn run<I, T>(
    args: I,
    environment: &impl Environment,
    out: &mut impl Write,
    err: &mut impl Write,
) -> ExitCode
where
    I: IntoIterator<Item = T>,
    T: Into<OsString> + Clone,
{
    // lobster-trace: SwRequirements.sw_req_cli
    // lobster-trace: SwRequirements.sw_func_msg_output
    match Args::try_parse_from(args) {
        Ok(args) => {
            let greeter = Greeter::new(environment, Thresholds::DEFAULT);
            let greeting = greeter.greet(args.name.as_deref());
            exit_code(&writeln!(out, "{greeting}"), ExitCode::SUCCESS)
        }
        Err(error) => report_usage(&error, out, err),
    }
}

/// Shows the help or version, or the usage error of wrong arguments.
fn report_usage(error: &clap::Error, out: &mut impl Write, err: &mut impl Write) -> ExitCode {
    // lobster-trace: SwRequirements.sw_req_cli_help
    // lobster-trace: SwRequirements.sw_req_cli_usage_error
    match error.kind() {
        ErrorKind::DisplayHelp | ErrorKind::DisplayVersion => {
            exit_code(&write!(out, "{}", error.render()), ExitCode::SUCCESS)
        }
        _ => exit_code(
            &write!(err, "{}", error.render()),
            ExitCode::from(USAGE_ERROR),
        ),
    }
}

/// Gets the exit code: `code` if the output was written, otherwise failure.
fn exit_code(written: &std::io::Result<()>, code: ExitCode) -> ExitCode {
    // lobster-trace: SwRequirements.sw_func_msg_output
    match written {
        Ok(()) => code,
        Err(_) => ExitCode::FAILURE,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::greeter::tests::FakeEnvironment;
    use crate::lobster_trace;

    /// Output of a run.
    struct Output {
        code: ExitCode,
        out: String,
        err: String,
    }

    /// Runs the application at 8:00 with the given arguments after the program name.
    fn run_with(args: &[&str]) -> Output {
        // lobster-exclude: Test helper, the tests using it trace to their test cases.
        let environment = FakeEnvironment {
            hour: 8,
            login: "bob",
        };
        let (mut out, mut err) = (Vec::new(), Vec::new());
        let code = run(
            std::iter::once("greet").chain(args.iter().copied()),
            &environment,
            &mut out,
            &mut err,
        );
        Output {
            code,
            out: String::from_utf8(out).expect("UTF-8 output"),
            err: String::from_utf8(err).expect("UTF-8 errors"),
        }
    }

    /// The application runs with a user name argument.
    #[test]
    fn cli() {
        // lobster-trace: SwTests.tc_cli
        lobster_trace!("SwTests.tc_cli");
        assert_eq!(run_with(&["Alice"]).code, ExitCode::SUCCESS);
    }

    /// The greeting is written to the standard output.
    #[test]
    fn cli_stdout() {
        // lobster-trace: SwTests.tc_cli_stdout
        lobster_trace!("SwTests.tc_cli_stdout");
        let output = run_with(&["Alice"]);
        assert_eq!(output.out, "Good morning Alice!\n");
        assert_eq!(output.err, "");
    }

    /// `-h` and `--help` show the usage.
    #[test]
    fn cli_usage_help() {
        // lobster-trace: SwTests.tc_cli_usage_help
        lobster_trace!("SwTests.tc_cli_usage_help");
        for option in ["-h", "--help"] {
            let output = run_with(&[option]);
            assert_eq!(output.code, ExitCode::SUCCESS, "{option}");
            assert!(
                output.out.contains("Usage: greet [NAME]"),
                "{option}: {}",
                output.out
            );
        }
    }

    /// An unknown option and a second name are reported as usage error.
    #[test]
    fn cli_usage_error() {
        // lobster-trace: SwTests.tc_cli_usage_error
        lobster_trace!("SwTests.tc_cli_usage_error");
        for args in [&["--unknown"][..], &["Alice", "Bob"][..]] {
            let output = run_with(args);
            assert_eq!(output.code, ExitCode::from(USAGE_ERROR), "{args:?}");
            assert!(output.err.starts_with("error:"), "{args:?}: {}", output.err);
            assert_eq!(output.out, "", "{args:?}");
        }
    }
}
