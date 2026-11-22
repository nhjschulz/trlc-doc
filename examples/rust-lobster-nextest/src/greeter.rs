//! The greeting for the user, depending on the time of day.

use crate::environment::Environment;

/// Hours at which the greeting changes, each the first hour of its period.
#[derive(Clone, Copy, Debug)]
pub struct Thresholds {
    pub morning: u32,
    pub midday: u32,
    pub afternoon: u32,
    pub night: u32,
}

impl Thresholds {
    /// Morning from 5:00, midday from 11:00, afternoon from 13:00 and night from 19:00.
    pub const DEFAULT: Self = Self {
        morning: 5,
        midday: 11,
        afternoon: 13,
        night: 19,
    };
}

/// Greets a user depending on the local time of its environment.
pub struct Greeter<'a, E: Environment> {
    environment: &'a E,
    thresholds: Thresholds,
}

impl<'a, E: Environment> Greeter<'a, E> {
    /// Creates a greeter for an environment and the hours at which the greeting changes.
    pub fn new(environment: &'a E, thresholds: Thresholds) -> Self {
        // lobster-trace: SwRequirements.sw_func_daytime_greeting_selection
        Self {
            environment,
            thresholds,
        }
    }

    /// Gets the greeting for a user, e.g. "Good morning Alice!".
    ///
    /// Without a user name, or with an empty one, the login name is greeted.
    pub fn greet(&self, user_name: Option<&str>) -> String {
        // lobster-trace: SwRequirements.sw_req_cli_default_name
        // lobster-trace: SwRequirements.sw_func_morning_time_greeting
        // lobster-trace: SwRequirements.sw_func_midday_time_greeting
        // lobster-trace: SwRequirements.sw_func_afternoon_time_greeting
        // lobster-trace: SwRequirements.sw_func_night_time_greeting
        let name = match user_name {
            Some(name) if !name.is_empty() => name.to_owned(),
            _ => self.environment.login_name(),
        };
        format!("{} {name}!", self.salutation(self.environment.local_hour()))
    }

    /// Selects the salutation for an hour of the day.
    fn salutation(&self, hour: u32) -> &'static str {
        // lobster-trace: SwRequirements.sw_func_daytime_greeting_selection
        let thresholds = &self.thresholds;
        if (thresholds.morning..thresholds.midday).contains(&hour) {
            "Good morning"
        } else if (thresholds.midday..thresholds.afternoon).contains(&hour) {
            "Good midday"
        } else if (thresholds.afternoon..thresholds.night).contains(&hour) {
            "Good afternoon"
        } else {
            "Good night"
        }
    }
}

#[cfg(test)]
pub mod tests {
    use super::*;
    use crate::lobster_trace;

    /// An environment with a fixed hour and login name.
    pub struct FakeEnvironment {
        pub hour: u32,
        pub login: &'static str,
    }

    impl Environment for FakeEnvironment {
        fn local_hour(&self) -> u32 {
            self.hour
        }

        fn login_name(&self) -> String {
            self.login.to_owned()
        }
    }

    /// Gets the greeting for Alice at an hour.
    fn greet_alice_at(hour: u32) -> String {
        // lobster-exclude: Test helper, the tests using it trace to their test cases.
        let environment = FakeEnvironment { hour, login: "bob" };
        Greeter::new(&environment, Thresholds::DEFAULT).greet(Some("Alice"))
    }

    /// From 19:00 to 4:59 the greeting is "Good night".
    #[test]
    fn night_time_greeting() {
        // lobster-trace: SwTests.tc_greet_night_time_greeting
        lobster_trace!("SwTests.tc_greet_night_time_greeting");
        for hour in (19..24).chain(0..5) {
            assert_eq!(greet_alice_at(hour), "Good night Alice!", "hour {hour}");
        }
    }

    /// From 5:00 to 10:59 the greeting is "Good morning".
    #[test]
    fn morning_time_greeting() {
        // lobster-trace: SwTests.tc_greet_morning_time_greeting
        lobster_trace!("SwTests.tc_greet_morning_time_greeting");
        for hour in 5..11 {
            assert_eq!(greet_alice_at(hour), "Good morning Alice!", "hour {hour}");
        }
    }

    /// From 11:00 to 12:59 the greeting is "Good midday".
    #[test]
    fn midday_time_greeting() {
        // lobster-trace: SwTests.tc_greet_midday_time_greeting
        lobster_trace!("SwTests.tc_greet_midday_time_greeting");
        for hour in 11..13 {
            assert_eq!(greet_alice_at(hour), "Good midday Alice!", "hour {hour}");
        }
    }

    /// From 13:00 to 18:59 the greeting is "Good afternoon".
    #[test]
    fn afternoon_time_greeting() {
        // lobster-trace: SwTests.tc_greet_afternoon_time_greeting
        lobster_trace!("SwTests.tc_greet_afternoon_time_greeting");
        for hour in 13..19 {
            assert_eq!(greet_alice_at(hour), "Good afternoon Alice!", "hour {hour}");
        }
    }

    /// The greeting follows the hour of the environment.
    #[test]
    fn daytime_greeting_selection() {
        // lobster-trace: SwTests.tc_func_daytime_greeting_selection
        lobster_trace!("SwTests.tc_func_daytime_greeting_selection");
        assert_ne!(greet_alice_at(8), greet_alice_at(20));
    }

    /// A given user name is greeted.
    #[test]
    fn user_name() {
        // lobster-trace: SwTests.tc_greet_user_name
        lobster_trace!("SwTests.tc_greet_user_name");
        assert!(greet_alice_at(8).ends_with(" Alice!"));
    }

    /// Without a user name, or with an empty one, the login name is greeted.
    #[test]
    fn default_name() {
        // lobster-trace: SwTests.tc_greet_default_name
        lobster_trace!("SwTests.tc_greet_default_name");
        let environment = FakeEnvironment {
            hour: 8,
            login: "bob",
        };
        let greeter = Greeter::new(&environment, Thresholds::DEFAULT);
        assert_eq!(greeter.greet(None), "Good morning bob!");
        assert_eq!(greeter.greet(Some("")), "Good morning bob!");
    }
}
