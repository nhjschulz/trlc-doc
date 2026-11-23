"""
Test cases to test the greeting functionality.

Author: Norbert Schulz (norbert.schulz@newtec.de)
"""
# BSD 3-Clause License
#
# Copyright (c) 2025, NewTec GmbH
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Imports **********************************************************************

from unittest.mock import patch

from freezegun import freeze_time
from greeter.greet import greet

# Functions ********************************************************************


def test_greet_nighttime_greeting(record_property):
    # lobster-trace: SwTests.tc_greet_night_time_greeting
    """
    Test the nighttime greeting functionality of the greet function.

    This test verifies that the greet function returns "Good night <name>!"
    when the time is between 19:00 and 04:59.
    """
    record_property("lobster-trace", "SwTests.tc_greet_night_time_greeting")

    for mock_hour in range(19, 24 + 5):
        for mock_minute in range(0, 60):
            mocked_time = f"2025-01-01 {mock_hour % 24:02}:{mock_minute:02}:00"
            with freeze_time(mocked_time):
                assert greet("Alice") == "Good night Alice!"


def test_greet_morning_greeting(record_property):
    # lobster-trace: SwTests.tc_greet_morning_time_greeting
    """
    Test the morning greeting functionality of the greet function.

    This test verifies that the greet function returns "Good morning <name>!"
    when the time is between 05:00 and 10:59.
    """
    record_property("lobster-trace", "SwTests.tc_greet_morning_time_greeting")

    for mock_hour in range(5, 11):
        for mock_minute in range(0, 60):
            mocked_time = f"2025-01-01 {mock_hour:02}:{mock_minute:02}:00"
            with freeze_time(mocked_time):
                assert greet("John") == "Good morning John!"


def test_greet_midday_greeting(record_property):
    # lobster-trace: SwTests.tc_greet_midday_time_greeting
    """
    Test the midday greeting functionality of the greet function.

    This test verifies that the greet function returns "Good midday <name>!"
    when the time is between 11:00 and 12:59.
    """
    record_property("lobster-trace", "SwTests.tc_greet_midday_time_greeting")

    for mock_hour in range(11, 13):
        for mock_minute in range(0, 60):
            mocked_time = f"2025-01-01 {mock_hour:02}:{mock_minute:02}:00"
            with freeze_time(mocked_time):
                assert greet("Paula") == "Good midday Paula!"


def test_greet_afternoon_greeting(record_property):
    # lobster-trace: SwTests.tc_greet_afternoon_time_greeting
    """
    Test the afternoon greeting functionality of the greet function.

    This test verifies that the greet function returns "Good afternoon <name>!"
    when the time is between 13:00 and 18:59.
    """
    record_property("lobster-trace", "SwTests.tc_greet_afternoon_time_greeting")

    for mock_hour in range(13, 18):
        for mock_minute in range(0, 60):
            mocked_time = f"2025-01-01 {mock_hour:02}:{mock_minute:02}:00"
            with freeze_time(mocked_time):
                assert greet("Peter") == "Good afternoon Peter!"


def test_greet_with_name(record_property):
    # lobster-trace: SwTests.tc_greet_user_name
    """
    Test the greet function with a provided name

    This test verifies that the greet function returns the correct greeting
    based on the provided name.
    """
    record_property("lobster-trace", "SwTests.tc_greet_user_name")

    assert greet("John").endswith("John!")


def test_greet_without_name(record_property):
    # lobster-trace: SwTests.tc_greet_default_name
    """
    Test the greet function without providing a name and with a mocked hour.

    This test verifies that the greet function returns the login name in the
    greeting when no name is provided.
    """
    record_property("lobster-trace", "SwTests.tc_greet_default_name")

    with patch("getpass.getuser", return_value="testuser"):
        assert greet(None).endswith("testuser!")
