//! Access to the system: local time and login name.
//!
//! The greeter uses the [`Environment`] trait, so the tests can replace the
//! system by fixed values.

use chrono::{Local, Timelike};

/// The system information the greeter depends on.
pub trait Environment {
    /// Hour of the local system time, 0 to 23.
    fn local_hour(&self) -> u32;

    /// Login name of the user.
    fn login_name(&self) -> String;
}

/// The environment of the running process.
pub struct SystemEnvironment;

impl SystemEnvironment {
    /// Gets the hour of the local system time.
    fn system_hour() -> u32 {
        // lobster-trace: SwRequirements.sw_func_daytime_greeting_selection
        Local::now().hour()
    }

    /// Gets the login name from the environment, `USER` on Linux and macOS, `USERNAME` on Windows.
    fn system_login_name() -> String {
        // lobster-trace: SwRequirements.sw_req_cli_default_name
        ["USER", "USERNAME"]
            .iter()
            .find_map(|name| std::env::var(name).ok().filter(|value| !value.is_empty()))
            .unwrap_or_else(|| String::from("unknown user"))
    }
}

impl Environment for SystemEnvironment {
    fn local_hour(&self) -> u32 {
        Self::system_hour()
    }

    fn login_name(&self) -> String {
        Self::system_login_name()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::lobster_trace;

    /// The system provides a valid hour and a login name.
    #[test]
    fn system_environment() {
        // lobster-trace: SwTests.tc_func_daytime_greeting_selection
        // lobster-trace: SwTests.tc_greet_default_name
        lobster_trace!("SwTests.tc_func_daytime_greeting_selection");
        lobster_trace!("SwTests.tc_greet_default_name");

        assert!(SystemEnvironment.local_hour() < 24);
        assert_ne!(SystemEnvironment.login_name(), "");
    }
}
