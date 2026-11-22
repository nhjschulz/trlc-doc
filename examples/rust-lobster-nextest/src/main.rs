//! Greeter - greets the user depending on the time of day.
//!
//! The program is the trlcdoc example for Rust: requirements, architecture and
//! test cases are TRLC records, and each function names the requirements it
//! implements with a `// lobster-trace:` comment.

mod app;
mod environment;
mod greeter;

use std::io;
use std::process::ExitCode;

use environment::SystemEnvironment;

/// Writes a test case id to the test output, where trlcdoc links the test result to it.
#[cfg(test)]
macro_rules! lobster_trace {
    ($id:literal) => {
        println!(concat!("lobster-trace: ", $id))
    };
}
#[cfg(test)]
pub(crate) use lobster_trace;

/// Program entry point: runs the application with the process arguments and console.
fn main() -> ExitCode {
    // lobster-trace: SwRequirements.sw_req_cli
    app::run(
        std::env::args_os(),
        &SystemEnvironment,
        &mut io::stdout(),
        &mut io::stderr(),
    )
}
