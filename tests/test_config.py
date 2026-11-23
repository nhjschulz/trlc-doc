"""Tests of the trlcdoc configuration: discovery, validation and project settings."""

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
    other.write_text(project.read_text(encoding="utf-8").replace("name: example", "name: other"), encoding="utf-8")
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
    # pyTRLCConverter options belong into the pytrlcconverter block of the document.
    data["documents"][1]["translation"] = "builtin:translation.json"
    errors = _config_errors(root, data)
    assert "does not match the schema" in errors
    assert "documents/0/type" in errors
    assert "project: 'author' is a required property" in errors
    assert "documents/1: 'translation' is not one of" in errors

    data = base_config()
    data["documents"][1]["include"] = ["unknown"]
    data["documents"][2]["id"] = "sw_requirements"
    data["documents"][0]["pytrlcconverter"]["converter"]["rst"] = "converters/missing.py"
    data["documents"][0]["pytrlcconverter"]["render_cfg"] = "missing.json"
    data["trace"]["levels"][1]["trace_to"] = ["Unknown Level"]
    data["html"] = {"index": "docs/index.rst", "page_header": "docs/header.rst", "conf": "docs/conf.py"}
    data["project"].update({"logo": "docs/logo.pngx", "favicon": "docs/favicon.ico"})
    data["trace"]["levels"].append(
        {"name": "SW Code", "kind": "implementation", "extractor": "lobster-doxygen", "doxyfile": "tools/Doxyfile"}
    )
    errors = _config_errors(root, data)
    assert "has invalid settings" in errors
    assert "documents[sw_architecture].include: 'unknown'" in errors
    assert "documents: id 'sw_requirements' is used more than once" in errors
    assert "documents[sw_requirements].pytrlcconverter.converter.rst: file 'converters/missing.py' not found" in errors
    assert "documents[sw_requirements].pytrlcconverter.render_cfg: file 'missing.json' not found" in errors
    assert "trace.levels[SW Architecture].trace_to: level 'Unknown Level' is not defined" in errors
    for key, value in data["html"].items():
        assert f"html.{key}: file '{value}' not found" in errors
    for key in ("logo", "favicon"):
        assert f"project.{key}: file '{data['project'][key]}' not found" in errors
    assert "trace.levels[SW Code].doxyfile: file 'tools/Doxyfile' not found" in errors

    # No step runs with an invalid configuration.
    assert cli.main(["-c", str(project), "clean", "all"]) == 2
    assert "has invalid settings" in capsys.readouterr().out
    assert not (root / "build").exists()

    # Errors start with file and line of their entry, a missing key with the line of its parent.
    # fmt: off
    lines = ["project:",                                 # 1
             "  name: example",                          # 2
             "  author: Jane Doe",                       # 3
             "  copyright: '2026, Jane Doe'",            # 4
             "  logo: docs/logo.pngx",                   # 5
             "paths:",                                   # 6
             "  trlc_model: trlc/model",                 # 7
             "documents:",                               # 8
             "  - id: sw_requirements",                  # 9
             "    type: trlc",                           # 10
             "    title: SW Requirements",               # 11
             "    source: trlc/swe-req",                 # 12
             "    pytrlcconverter:",                     # 13
             "      converter:",                         # 14
             "        rst: builtin:req2rst.py",          # 15
             "  - id: sw_architecture",                  # 16
             "    type: trlc",                           # 17
             "    title: SW Architecture",               # 18
             "    source: trlc/swe-arch",                # 19
             "    include: [sw_requirements, unknown]",  # 20
             "    pytrlcconverter:",                     # 21
             "      converter:",                         # 22
             "        rst: converters/missing.py",       # 23
             "  - id: sw_requirements",                  # 24
             "    type: trlc",                           # 25
             "    title: SW Requirements",               # 26
             "    source: trlc/swe-req",                 # 27
             "    pytrlcconverter:",                     # 28
             "      converter:",                         # 29
             "        rst: builtin:req2rst.py"]          # 30
    # fmt: on
    project.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert cli.main(["-c", str(project), "check"]) == 2
    out = capsys.readouterr().out.splitlines()
    assert out[-4:] == [
        f"  {project}:5: project.logo: file 'docs/logo.pngx' not found.",
        f"  {project}:20: documents[sw_architecture].include: 'unknown' is no document of type trlc or test_results.",
        f"  {project}:23: documents[sw_architecture].pytrlcconverter.converter.rst: "
        "file 'converters/missing.py' not found.",
        f"  {project}:24: documents: id 'sw_requirements' is used more than once.",
    ]

    lines[2] = "  authors: Jane Doe"
    lines[18] = "    sorce: trlc/swe-arch"
    lines[24] = "    type: pdf"
    project.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert cli.main(["-c", str(project), "check"]) == 2
    out = capsys.readouterr().out
    assert f"\n  {project}:1: project: 'author' is a required property" in out
    assert f"\n  {project}:3: project: Additional properties are not allowed ('authors' was unexpected)" in out
    assert f"\n  {project}:25: documents/2/type: 'pdf' is not one of" in out
    assert f"\n  {project}:19: documents/1: 'sorce' is not one of" in out

    # A file that is no valid YAML is reported with the position of the error.
    project.write_text("project:\n  name: x\n   author: y\n", encoding="utf-8")
    assert cli.main(["-c", str(project), "check"]) == 2
    out = capsys.readouterr().out
    assert "is no valid YAML: mapping values are not allowed here" in out
    assert "line 3, column 10" in out
    assert "Traceback" not in out

    # tests.link needs the property, the output pattern, or the name pattern with 'from' and 'to'.
    data = base_config()
    for link, valid in (
        ({"property": "lobster-tracing"}, True),
        ({"output": "lobster-trace: {id}"}, True),
        ({"output": "lobster-trace: {id}", "from": "test_{name}", "to": "SwTests.tc_{name}"}, True),
        ({"from": "test_{name}", "to": "SwTests.tc_{name}"}, True),
        ({}, False),
        ({"output": "lobster-trace"}, False),
        ({"output": "lobster-trace: {id}", "from": "test_{name}"}, False),
        ({"to": "SwTests.tc_{name}"}, False),
    ):
        data["tests"]["link"] = link
        assert (_config_errors(root, data) == "") is valid, link
    assert "tests/link" in _config_errors(root, data)

    # lobster-python scans sources, lobster-doxygen takes the sources from a Doxyfile.
    (root / "Doxyfile").write_text("INPUT = src\n", encoding="utf-8")
    for extractor, keys, valid in (
        ("lobster-python", ("sources",), True),
        ("lobster-python", ("doxyfile",), False),
        ("lobster-python", ("sources", "doxyfile"), False),
        ("lobster-doxygen", ("doxyfile",), True),
        ("lobster-doxygen", ("sources",), False),
        ("lobster-doxygen", ("sources", "doxyfile"), False),
    ):
        data = base_config()
        level = {"name": "SW Code", "kind": "implementation", "extractor": extractor}
        level.update({key: {"sources": ["src"], "doxyfile": "Doxyfile"}[key] for key in keys})
        data["trace"]["levels"].append(level)
        assert (_config_errors(root, data) == "") is valid, (extractor, keys)


def test_project_settings(project: Path) -> None:
    """The project metadata of the configuration is passed to the HTML site.

    Args:
        project (Path): Configuration file of the example project.
    """
    root = project.parent
    (root / "logo.png").write_bytes(b"")
    data = base_config()
    data["project"].update(
        {
            "name": "Hello World",
            "version": "1.2.3",
            "author": "John Doe",
            "copyright": "2020, John Doe",
            "logo": "logo.png",
        }
    )
    cfg = load_config(write_config(root, data))
    assert cfg.repository == "https://github.com/example/example.git"

    settings = json.loads(_write_sphinx_config(cfg, root, []).read_text(encoding="utf-8"))
    assert settings["project"] == "Hello World"
    assert settings["version"] == "1.2.3"
    assert settings["author"] == "John Doe"
    assert settings["copyright"] == "2020, John Doe"
    assert settings["logo"] == str(root / "logo.png")

    del data["project"]["repository"], data["project"]["version"]
    cfg = load_config(write_config(root, data))
    assert cfg.repository == "auto"
    assert json.loads(_write_sphinx_config(cfg, root, []).read_text(encoding="utf-8"))["version"] is None


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
    for folder in (
        cfg.convert_dir("rst", "sw_requirements"),
        cfg.tests_dir,
        cfg.junit_file,
        cfg.trace_dir,
        cfg.trace_report_html,
        cfg.sphinx_dir,
        cfg.html_dir,
        cfg.plantuml_dir,
    ):
        assert folder.is_relative_to(cfg.output)

    for output in (".", "..", str(PACKAGE_DIR / "out")):
        data["paths"]["output"] = output
        assert "paths.output: must not be" in _config_errors(root, data)

    data["paths"]["output"] = "out/docs"
    assert load_config(write_config(root, data)).output == root / "out" / "docs"


# Main *************************************************************************
