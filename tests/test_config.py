"""Tests of the trlcdoc configuration: discovery, validation and project settings.

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

import json
from pathlib import Path

import pytest
from conftest import base_config, write_config

from trlcdoc import cli
from trlcdoc.config import PACKAGE_DIR, find_config, load_config
from trlcdoc.html import _write_sphinx_config
from trlcdoc.util import TrlcdocError

# Variables ********************************************************************

# Classes **********************************************************************

# Functions ********************************************************************


def _config_errors(root: Path, data: dict) -> str:
    """Write a configuration and get its validation errors.

    Args:
        root (Path): Project root.
        data (dict): Configuration data.

    Returns:
        str: The error message, empty if the configuration is valid.
    """
    message = ""
    try:
        load_config(write_config(root, data))
    except TrlcdocError as err:
        message = str(err)
    return message


def test_config_file(project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    """The configuration is trlcdoc.yaml of the current folder or a parent, or given on the command line.

    Args:
        project (Path): Configuration file of the example project.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.
        capsys (pytest.CaptureFixture): pytest output capture.
    """
    root = project.parent
    assert find_config(root) == project
    assert find_config(root / "trlc" / "swe-req") == project

    monkeypatch.chdir(root / "trlc" / "swe-req")
    assert cli.main(["check"]) == 0
    assert str(project) in capsys.readouterr().out

    other = root / "other.yaml"
    other.write_text(project.read_text(encoding="utf-8").replace("name: example", "name: other"),
                     encoding="utf-8")
    assert cli.main(["-c", str(other), "check"]) == 0
    assert str(other) in capsys.readouterr().out
    assert load_config(other).project["name"] == "other"

    assert cli.main(["-c", str(root / "missing.yaml"), "check"]) == 2
    assert "not found" in capsys.readouterr().out


def test_config_validation(project: Path, capsys: pytest.CaptureFixture) -> None:
    """Schema violations and invalid references are reported with their location before any step runs.

    Args:
        project (Path): Configuration file of the example project.
        capsys (pytest.CaptureFixture): pytest output capture.
    """
    root = project.parent

    data = base_config()
    data["documents"][0]["type"] = "pdf"
    del data["project"]["author"]
    errors = _config_errors(root, data)
    assert "does not match the schema" in errors
    assert "documents/0/type" in errors
    assert "project: 'author' is a required property" in errors

    data = base_config()
    data["documents"][1]["include"] = ["unknown"]
    data["documents"][2]["id"] = "sw_requirements"
    data["documents"][0]["converter"]["rst"] = "converters/missing.py"
    data["trace"]["levels"][1]["trace_to"] = ["Unknown Level"]
    errors = _config_errors(root, data)
    assert "has invalid settings" in errors
    assert "documents[sw_architecture].include: 'unknown'" in errors
    assert "documents: id 'sw_requirements' is used more than once" in errors
    assert "documents[sw_requirements].converter.rst: file 'converters/missing.py' not found" in errors
    assert "trace.levels[SW Architecture].trace_to: level 'Unknown Level' is not defined" in errors

    # No step runs with an invalid configuration.
    assert cli.main(["-c", str(project), "clean", "all"]) == 2
    assert "has invalid settings" in capsys.readouterr().out
    assert not (root / "build").exists()


def test_project_settings(project: Path) -> None:
    """The project metadata of the configuration is passed to the HTML site.

    Args:
        project (Path): Configuration file of the example project.
    """
    root = project.parent
    (root / "logo.png").write_bytes(b"")
    data = base_config()
    data["project"].update({"name": "Hello World", "author": "John Doe", "copyright": "2020, John Doe",
                            "logo": "logo.png"})
    cfg = load_config(write_config(root, data))
    assert cfg.repository == "https://github.com/example/example.git"

    settings = json.loads(_write_sphinx_config(cfg, root, []).read_text(encoding="utf-8"))
    assert settings["project"] == "Hello World"
    assert settings["author"] == "John Doe"
    assert settings["copyright"] == "2020, John Doe"
    assert settings["logo"] == str(root / "logo.png")

    del data["project"]["repository"]
    assert load_config(write_config(root, data)).repository == "auto"


def test_output_folder(project: Path) -> None:
    """Generated files go to the configurable output folder, which is checked for a safe location.

    Args:
        project (Path): Configuration file of the example project.
    """
    root = project.parent
    data = base_config()
    del data["paths"]["output"]
    cfg = load_config(write_config(root, data))
    assert cfg.output == root / "build" / "trlcdoc"
    for folder in (cfg.convert_dir("rst", "sw_requirements"), cfg.tests_dir, cfg.junit_file, cfg.trace_dir,
                   cfg.trace_report_html, cfg.sphinx_dir, cfg.html_dir, cfg.plantuml_dir):
        assert folder.is_relative_to(cfg.output)

    for output in (".", "..", str(PACKAGE_DIR / "out")):
        data["paths"]["output"] = output
        assert "paths.output: must not be" in _config_errors(root, data)

    data["paths"]["output"] = "out/docs"
    assert load_config(write_config(root, data)).output == root / "out" / "docs"

# Main *************************************************************************
