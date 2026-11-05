"""Tests of the trlcdoc command line interface: steps, their order and the exit codes.

    Author: Norbert Schulz (norbert.schulz@newtec.de)
"""

# trlcdoc - A utility for producing project documentation from TRLC and LOBSTER contents.
# Copyright (c) 2026 - 2026 NewTec GmbH
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

import subprocess
import sys
from pathlib import Path
from typing import List

import pytest
from conftest import base_config, make_project, write_config

from trlcdoc import cli
from trlcdoc.config import load_config
from trlcdoc.util import find_tool

# Variables ********************************************************************

# Classes **********************************************************************

# Functions ********************************************************************


def _record_steps(monkeypatch: pytest.MonkeyPatch) -> List[str]:
    """Replace the step execution by recording the executed step names.

    Args:
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.

    Returns:
        List[str]: The list the executed steps are appended to.
    """
    executed: List[str] = []
    monkeypatch.setattr(cli, "_run_step", lambda step, cfg, args: executed.append(step) is None)
    return executed


def test_cli(project: Path) -> None:
    """The functionality is available as console application.

    Args:
        project (Path): Configuration file of the example project.
    """
    for cmd in ([find_tool("trlcdoc")], [sys.executable, "-m", "trlcdoc"]):
        proc = subprocess.run([*cmd, "-c", str(project), "check"], capture_output=True, text=True, check=False)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "is valid" in proc.stdout


@pytest.mark.parametrize("option", ["-h", "--help"])
def test_cli_help(option: str, capsys: pytest.CaptureFixture) -> None:
    """The usage help is shown with -h and --help.

    Args:
        option (str): Help option.
        capsys (pytest.CaptureFixture): pytest output capture.
    """
    with pytest.raises(SystemExit) as exit_info:
        cli.main([option])
    out = capsys.readouterr().out
    assert exit_info.value.code == 0
    assert "usage: trlcdoc" in out
    for step in cli.STEPS:
        assert step in out


def test_steps(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Selected steps run, without selection all configured steps except clean run.

    Args:
        project (Path): Configuration file of the example project.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.
    """
    executed = _record_steps(monkeypatch)

    assert cli.main(["-c", str(project)]) == 0
    assert executed == ["check", "plantuml", "tests", "convert", "trace", "html"]

    executed.clear()
    assert cli.main(["-c", str(project), "check"]) == 0
    assert executed == ["check"]

    executed.clear()
    assert cli.main(["-c", str(project), "clean", "all"]) == 0
    assert executed[0] == "clean"

    # Steps without settings are skipped by 'all'.
    data = base_config()
    del data["tests"]
    del data["trace"]
    data["documents"] = [doc for doc in data["documents"] if doc["type"] == "trlc"]
    write_config(project.parent, data)
    executed.clear()
    assert cli.main(["-c", str(project)]) == 0
    assert executed == ["check", "plantuml", "convert", "html"]

    with pytest.raises(SystemExit) as exit_info:
        cli.main(["-c", str(project), "unknown"])
    assert exit_info.value.code == 2


def test_step_order(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Steps run in fixed order and the PlantUML step is added for convert and html.

    Args:
        project (Path): Configuration file of the example project.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.
    """
    # The step selection is checked directly, as main() only shows its effect.
    cfg = load_config(project)
    # pylint: disable=protected-access
    assert cli._selected_steps(cfg, ["html", "trace", "tests", "clean"]) == \
        ["clean", "plantuml", "tests", "trace", "html"]
    assert cli._selected_steps(cfg, ["convert"]) == ["plantuml", "convert"]
    assert cli._selected_steps(cfg, ["tests"]) == ["tests"]
    # pylint: enable=protected-access

    executed = _record_steps(monkeypatch)
    assert cli.main(["-c", str(project), "trace", "check"]) == 0
    assert executed == ["check", "trace"]


def test_exit_code(tmp_path: Path) -> None:
    """The exit code is 0 on success, 1 on findings and 2 on build errors.

    Args:
        tmp_path (Path): pytest temporary folder.
    """
    passing = make_project(tmp_path / "passing")
    assert cli.main(["-c", str(passing), "tests"]) == 0

    failing = make_project(tmp_path / "failing", failing=True)
    assert cli.main(["-c", str(failing), "tests"]) == 1

    assert cli.main(["-c", str(tmp_path / "missing.yaml"), "check"]) == 2

# Main *************************************************************************
