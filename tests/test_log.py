"""Tests of the verbose output."""

# trlcdoc - A utility for producing project documentation from TRLC and LOBSTER contents.
# Copyright (c) 2026 - 2026 Norbert Schulz github@schulznorbert.de
#
# This file is part of trlcdoc program.
#
# The trlcdoc program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# The trlcdoc program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with pyTRLCConverter.
# If not, see <https://www.gnu.org/licenses/>.

# Imports **********************************************************************

import sys
from pathlib import Path

import pytest

from trlcdoc import cli, html
from trlcdoc.config import load_config
from trlcdoc.log import command_line, redact_env, redact_url, setup_logging
from trlcdoc.testrun import RESULTS_FILE
from trlcdoc.util import run_unchecked

# Variables ********************************************************************

# Classes **********************************************************************

# Functions ********************************************************************


def test_verbose_output(project: Path, capsys: pytest.CaptureFixture) -> None:
    """-v adds debug output, -vv trace output, the default output has neither, the results are the same.

    Args:
        project (Path): Configuration file of the example project.
        capsys (pytest.CaptureFixture): pytest output capture.
    """
    results_file = load_config(project).test_results_dir / RESULTS_FILE
    outputs: dict[str, str] = {}
    results: dict[str, str] = {}
    for options in ([], ["-v"], ["-vv"]):
        assert cli.main(["-c", str(project), *options, "tests"]) == 0
        captured = capsys.readouterr()
        assert captured.err == ""
        key = " ".join(options)
        outputs[key] = captured.out
        results[key] = results_file.read_text(encoding="utf-8")

    default = outputs[""]
    assert "===== trlcdoc tests =====" in default
    assert "  $ " in default
    assert "Tests: 1 results, 0 failed." in default
    assert "DEBUG:" not in default
    assert "TRACE:" not in default

    debug = outputs["-v"]
    assert "DEBUG: Steps: tests" in debug
    assert f"DEBUG: cwd: {project.parent}" in debug
    assert "DEBUG: env: COVERAGE_FILE=" in debug
    assert "DEBUG: exit code 0 after " in debug
    assert "TRACE:" not in debug

    trace = outputs["-vv"]
    assert "TRACE: environment: PATH=" in trace
    assert "TRACE: Test test_hello: passed, test cases SwTests.tc_hello" in trace

    # Verbose output doesn't change the results.
    assert results["-v"] == results[""] and results["-vv"] == results[""]


def test_verbose_secrets(project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    """Secrets of environment variables and URLs are not shown, also not at trace level.

    Args:
        project (Path): Configuration file of the example project.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.
        capsys (pytest.CaptureFixture): pytest output capture.
    """
    monkeypatch.setenv("MY_API_TOKEN", "s3cr3t-value")
    # A PlantUML server needs no Java.
    monkeypatch.setenv("PLANTUML", "https://jane:pa55word@plantuml.example.com/plantuml")
    assert cli.main(["-c", str(project), "-vv", "plantuml", "tests"]) == 0
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert "s3cr3t-value" not in output
    assert "pa55word" not in output
    assert "TRACE: environment: MY_API_TOKEN=***" in output
    assert "PlantUML: https://***@plantuml.example.com/plantuml" in output

    assert redact_url("https://plantuml.example.com/plantuml") == "https://plantuml.example.com/plantuml"
    assert redact_url("/usr/bin:/bin") == "/usr/bin:/bin"
    assert redact_env({"GITHUB_TOKEN": "x", "db_password": "y", "PATH": "/bin"}) == {
        "GITHUB_TOKEN": "***",
        "db_password": "***",
        "PATH": "/bin",
    }


def test_verbose_tools(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """The verbose output of a tool run, the shell quoting of commands and the Sphinx verbosity.

    Args:
        tmp_path (Path): pytest temporary folder.
        capsys (pytest.CaptureFixture): pytest output capture.
    """
    expected = 'tool "a b"' if sys.platform == "win32" else "tool 'a b'"
    assert command_line(["tool", "a b"]) == expected

    setup_logging(1)
    assert run_unchecked([sys.executable, "-c", "import sys; sys.stdin.read()"], tmp_path, stdin="abc") == 0
    out = capsys.readouterr().out
    assert "DEBUG: stdin: 3 characters" in out
    assert "DEBUG: exit code 0 after " in out

    if sys.platform != "win32":
        kill = "import os, signal; os.kill(os.getpid(), signal.SIGTERM)"
        assert run_unchecked([sys.executable, "-c", kill], tmp_path) < 0
        assert "(SIGTERM)" in capsys.readouterr().out

    for verbosity, option in ((0, ["-q"]), (1, []), (2, ["-v"]), (3, ["-v"])):
        setup_logging(verbosity)
        assert html._sphinx_verbosity() == option


def test_interrupted(project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    """Ctrl+C ends trlcdoc with a message and exit code 130 instead of a traceback.

    Args:
        project (Path): Configuration file of the example project.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.
        capsys (pytest.CaptureFixture): pytest output capture.
    """

    def interrupted_step(step: str, cfg: object, args: object) -> bool:
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "_run_step", interrupted_step)
    assert cli.main(["-c", str(project), "check"]) == 130
    assert "trlcdoc interrupted" in capsys.readouterr().err


# Main *************************************************************************
