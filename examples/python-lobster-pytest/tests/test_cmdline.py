"""
Test cases to test the command line interface.

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

import sys

import pytest
from greeter.__main__ import main

# Functions ********************************************************************


def test_cli(record_property):
    # lobster-trace: SwTests.tc_cli
    """
    Test the command-line interface (CLI) argument handling of the `main` function.
    This test simulates passing a command-line argument to the program and verifies
    that the `main` function executes successfully with the provided input.
    """
    record_property("lobster-trace", "SwTests.tc_cli")

    sys.argv = ["greet", "Alice"]
    assert main() == 0


def test_stdout(record_property, capsys):
    # lobster-trace: SwTests.tc_cli_stdout
    """
    Test the command-line interface (CLI) output of the `main` function.
    """
    record_property("lobster-trace", "SwTests.tc_cli_stdout")

    sys.argv = ["greet", "Tom"]
    main()

    assert "Tom" in capsys.readouterr().out


def test_usage_help(record_property, capsys):
    # lobster-trace: SwTests.tc_cli_usage_help
    """
    Test the command-line interface (CLI) help message of the `main` function.
    """
    record_property("lobster-trace", "SwTests.tc_cli_usage_help")

    expected_help_output_lines = [
        "usage: greet [-h] [name]",
        "",
        "A python CLI tool to greet a user considering the time.",
        "",
        "positional arguments:",
        "  name        Specify a user name to greet, defaults to login name if unset.",
        "",
        "options:",
        "  -h, --help  show this help message and exit",
        "",
        "Copyright (c) 2025 NewTec GmbH",
        "",
    ]

    sys.argv = ["greet", "-h"]
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        main()

    assert expected_help_output_lines == capsys.readouterr().out.split("\n")
    assert pytest_wrapped_e.type is SystemExit
    assert pytest_wrapped_e.value.code == 0


def test_usage_error(record_property, capsys):
    # lobster-trace: SwTests.tc_cli_usage_error
    """
    Test the command-line interface (CLI) error handling of the `main` function.
    """
    record_property("lobster-trace", "SwTests.tc_cli_usage_error")

    reference = "usage: greet [-h] [name]\ngreet: error: unrecognized arguments: --unknown\n"

    sys.argv = ["greet", "--unknown"]
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        main()

    assert reference == capsys.readouterr().err
    assert pytest_wrapped_e.type is SystemExit
    assert pytest_wrapped_e.value.code == 2
