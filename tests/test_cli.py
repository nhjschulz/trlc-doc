"""Tests of the trlcdoc command line interface: steps, their order and the exit codes."""

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

import subprocess
import sys
from pathlib import Path

import pytest
from conftest import base_config, make_project, write_config

from trlcdoc import __version__, cli
from trlcdoc.config import PACKAGE_DIR, load_config
from trlcdoc.util import clean_dir, find_tool

# Variables ********************************************************************

# Classes **********************************************************************

# Functions ********************************************************************


def _record_steps(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Replace the step execution by recording the executed step names.

    Args:
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.

    Returns:
        list[str]: The list the executed steps are appended to.
    """
    executed: list[str] = []
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
    assert cli.COPYRIGHT in out
    assert cli.REPOSITORY in out


@pytest.mark.parametrize("option", ["-v", "--version"])
def test_cli_version(option: str, capsys: pytest.CaptureFixture) -> None:
    """The version is shown with -v and --version.

    Args:
        option (str): Version option.
        capsys (pytest.CaptureFixture): pytest output capture.
    """
    with pytest.raises(SystemExit) as exit_info:
        cli.main([option])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out == f"trlcdoc {__version__}\n"


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
    assert cli._selected_steps(cfg, ["html", "trace", "tests", "clean"]) == [
        "clean",
        "plantuml",
        "tests",
        "trace",
        "html",
    ]
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


def test_external_tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    """A step stops with a build error if Java or Graphviz is missing.

    Args:
        tmp_path (Path): pytest temporary folder.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.
        capsys (pytest.CaptureFixture): pytest output capture.
    """
    root = tmp_path / "project"
    project = make_project(root)
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    monkeypatch.setenv("PATH", str(empty_dir))

    # A PlantUML jar needs Java, checked before Graphviz.
    jar = tmp_path / "plantuml.jar"
    jar.write_bytes(b"jar")
    monkeypatch.setenv("PLANTUML", str(jar))
    assert cli.main(["-c", str(project), "plantuml"]) == 2
    assert "Tool 'java' not found" in capsys.readouterr().out

    # A PlantUML server needs neither Java nor Graphviz.
    monkeypatch.setenv("PLANTUML", "https://plantuml.example.com/plantuml")
    assert cli.main(["-c", str(project), "plantuml"]) == 0
    capsys.readouterr()

    # The tracing policy diagram needs Graphviz.
    assert cli.main(["-c", str(project), "trace"]) == 2
    assert "Tool 'dot' not found. Graphviz is needed for the tracing policy diagram" in capsys.readouterr().out

    # The reStructuredText tracing report adds sphinx.ext.graphviz to the site.
    data = base_config()
    data["trace"]["report"] = "rst"
    assert cli.main(["-c", str(write_config(root, data)), "html"]) == 2
    assert "Graphviz is needed by the Sphinx extension sphinx.ext.graphviz" in capsys.readouterr().out


def test_output_option(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    """The --output option replaces paths.output and is checked like it.

    Args:
        tmp_path (Path): pytest temporary folder.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.
        capsys (pytest.CaptureFixture): pytest output capture.
    """
    root = tmp_path / "project"
    project = make_project(root)
    configured = root / "build" / "trlcdoc"
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    monkeypatch.chdir(work_dir)

    # A relative folder is relative to the current folder, not to the project root.
    for option in ("-o", "--output"):
        assert cli.main(["-c", str(project), option, "out", "check"]) == 0
        assert f"output: {work_dir / 'out'}" in capsys.readouterr().out
    assert load_config(project, tmp_path / "abs").output == tmp_path / "abs"

    # The generated files go to the given folder, the configured one is not created.
    assert cli.main(["-c", str(project), "--output", "out", "tests"]) == 0
    assert load_config(project, Path("out")).junit_file.is_file()
    assert not configured.exists()

    # The clean step removes the given folder only.
    clean_dir(configured / "html", configured)
    assert cli.main(["-c", str(project), "--output", "out", "clean"]) == 0
    assert not (work_dir / "out").exists()
    assert (configured / "html").is_dir()

    # Forbidden locations are errors, a forbidden paths.output is ignored.
    for output, error in (
        (root, "must not be the project root or one of its parents"),
        (tmp_path, "must not be the project root or one of its parents"),
        (PACKAGE_DIR / "out", "must not be inside the trlcdoc package folder"),
    ):
        assert cli.main(["-c", str(project), "--output", str(output), "check"]) == 2
        assert f"--output {output.resolve()}: {error}" in capsys.readouterr().out

    data = base_config()
    data["paths"]["output"] = "."
    assert cli.main(["-c", str(write_config(root, data)), "--output", "out", "check"]) == 0
    assert cli.main(["-c", str(project), "check"]) == 2
    assert "paths.output: must not be the project root" in capsys.readouterr().out


# Main *************************************************************************
