"""Tests of the LOBSTER tracing report.

"""

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
import os
import shutil
import sys
from pathlib import Path

import pytest
import yaml
from conftest import base_config, git_init, make_project, write_config

from trlcdoc import cli
from trlcdoc.config import load_config
from trlcdoc.testrun import run_tests
from trlcdoc.trace import build_trace_report
from trlcdoc.util import TrlcdocError

# Variables ********************************************************************

HELLO_C = """/**
 * @file hello.c
 * @brief Example module.
 */

/**
 * @brief Return the greeting.
 * @implements{SwRequirements.sw_req_hello}
 */
const char *hello(void)
{
    return "Hello";
}
"""

# Minimal Doxyfile with the aliases of lobster-doxygen; doxygen uses the defaults for all other settings.
DOXYFILE = """INPUT    = ../../src
ALIASES  = "implements{1}=@xrefitem implements \\"Implements\\" \\"Requirement Traceability\\" Requirement: \\1"
ALIASES += "justification{1}=@xrefitem justified \\"Justified\\" \\"Justification Overview\\" Justification: \\1"
QUIET    = YES
"""

# Classes **********************************************************************

# Functions ********************************************************************


def _report_items(cfg_file: Path) -> dict:
    """Read the tracing status of all items of the LOBSTER report.

    Args:
        cfg_file (Path): Configuration file of the project.

    Returns:
        dict: Tracing status per item tag.
    """
    report_file = load_config(cfg_file).trace_dir / "report.lobster"
    report = json.loads(report_file.read_text(encoding="utf-8"))
    return {item["tag"]: item for level in report["levels"] for item in level["items"]}


def test_trace_levels(project: Path) -> None:
    """The LOBSTER configuration is derived from the trace levels.

    Args:
        project (Path): Configuration file of the example project.
    """
    cfg = load_config(project)
    run_tests(cfg)
    build_trace_report(cfg, online=False)

    policy = (cfg.trace_dir / "lobster-report.conf").read_text(encoding="utf-8")
    assert 'requirements "SW Requirement" {' in policy
    assert 'requires: "SW Architecture";\n    requires: "SW Test Case";' in policy
    assert 'requirements "SW Test Result" {' in policy
    assert 'trace to: "SW Test Case";' in policy

    extract = yaml.safe_load((cfg.trace_dir / "sw_architecture.yaml").read_text(encoding="utf-8"))
    rule = extract["conversion-rules"][0]
    assert rule["package"] == "SwArch"
    assert rule["record-type"] == "SwArchSpec"
    assert rule["tags"] == ["satisfies"]
    assert str(cfg.root / "trlc" / "swe-req") in extract["inputs"]

    items = _report_items(project)
    assert set(items) == {"req SwRequirements.sw_req_hello", "req SwArch.sw_arch_hello",
                          "req SwTests.tc_hello", "req SwTests.test_hello_result"}
    assert items["req SwArch.sw_arch_hello"]["ref_up"] == ["req SwRequirements.sw_req_hello"]
    assert items["req SwTests.test_hello_result"]["text"] == "test_hello"


def test_trace_report(tmp_path: Path) -> None:
    """The HTML tracing report links to local files, or to the repository when online, also for a project in a
    subfolder of the repository.

    Args:
        tmp_path (Path): pytest temporary folder.
    """
    project = make_project(tmp_path / "project")
    cfg = load_config(project)
    run_tests(cfg)

    assert build_trace_report(cfg, online=False) == 0
    report = cfg.trace_report_html.read_text(encoding="utf-8")
    assert "sw_req_hello" in report
    assert "example/example" not in report

    commit = git_init(cfg.root)
    assert build_trace_report(cfg, online=True) == 0
    report = cfg.trace_report_html.read_text(encoding="utf-8")
    link = f"https://github.com/example/example/blob/{commit}/trlc/swe-req/swe-req.trlc"
    assert link in report

    # 'auto' derives the repository from the git origin remote.
    data = base_config()
    data["project"]["repository"] = "auto"
    cfg = load_config(write_config(cfg.root, data))
    assert build_trace_report(cfg, online=True) == 0
    assert link in cfg.trace_report_html.read_text(encoding="utf-8")

    # A project in a subfolder of the repository links to its files in the subfolder.
    project = make_project(tmp_path / "repo" / "examples" / "greeter")
    cfg = load_config(project)
    run_tests(cfg)
    commit = git_init(tmp_path / "repo")
    assert build_trace_report(cfg, online=True) == 0
    link = f"https://github.com/example/example/blob/{commit}/examples/greeter/trlc/swe-req/swe-req.trlc"
    assert link in cfg.trace_report_html.read_text(encoding="utf-8")



def test_trace_markdown(tmp_path: Path) -> None:
    """The descriptions of the tracing report are rendered as Markdown with "markdown: true".

    Args:
        tmp_path (Path): pytest temporary folder.
    """
    project = make_project(tmp_path / "project")
    req_file = project.parent / "trlc" / "swe-req" / "swe-req.trlc"
    req_file.write_text(req_file.read_text(encoding="utf-8").replace(
        'description = "The software shall greet."',
        "description =\n            '''\n            The software shall **greet** with\n"
        "            `hello()`.\n            '''"),
        encoding="utf-8")
    cfg = load_config(project)
    run_tests(cfg)

    # By default the description is plain text, with the source line breaks.
    assert build_trace_report(cfg, online=False) == 0
    report = cfg.trace_report_html.read_text(encoding="utf-8")
    assert "The software shall **greet** with<br>`hello()`." in report

    data = base_config()
    data["trace"]["markdown"] = True
    cfg = load_config(write_config(cfg.root, data))
    assert build_trace_report(cfg, online=False) == 0
    report = cfg.trace_report_html.read_text(encoding="utf-8")
    assert "The software shall <strong>greet</strong> with\n<code>hello()</code>.</p>" in report
    assert "**greet**" not in report


def test_trace_findings(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Items with missing trace links are listed and reported as findings.

    Args:
        tmp_path (Path): pytest temporary folder.
        capsys (pytest.CaptureFixture): pytest output capture.
    """
    project = make_project(tmp_path / "project", untraced=True)
    cfg = load_config(project)
    run_tests(cfg)
    capsys.readouterr()

    assert build_trace_report(cfg, online=False) == 1
    out = capsys.readouterr().out
    assert "SW Requirement: 2 items, 1 not traced" in out
    assert "req SwRequirements.sw_req_untraced" in out
    assert _report_items(project)["req SwRequirements.sw_req_untraced"]["tracing_status"] == "MISSING"

    assert cli.main(["-c", str(project), "trace"]) == 1
    assert "finished with findings in: trace" in capsys.readouterr().out


def test_trace_justified(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Items justified in LOBSTER (lobster-exclude) count as traced, but are counted.

    Args:
        tmp_path (Path): pytest temporary folder.
        capsys (pytest.CaptureFixture): pytest output capture.
    """
    project = make_project(tmp_path / "project")
    (project.parent / "src").mkdir()
    (project.parent / "src" / "code.py").write_text(
        'def greet():\n'
        '    # lobster-trace: SwRequirements.sw_req_hello\n'
        '    return "Hello"\n'
        '\n\n'
        'def helper():\n'
        '    # lobster-exclude: Utility for other functions.\n'
        '    return 1\n',
        encoding="utf-8")
    data = base_config()
    data["trace"]["levels"].append({"name": "SW Code", "kind": "implementation",
                                    "extractor": "lobster-python", "sources": ["src"],
                                    "trace_to": ["SW Requirement"]})
    cfg = load_config(write_config(project.parent, data))
    run_tests(cfg)
    capsys.readouterr()

    assert build_trace_report(cfg, online=False) == 0
    out = capsys.readouterr().out
    assert "SW Code: 2 items, 0 not traced, 1 justified" in out
    assert "python code.helper" not in out
    assert _report_items(project)["python code.helper"]["tracing_status"] == "JUSTIFIED"


def test_trace_doxygen(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """C/C++ code is traced with doxygen and lobster-doxygen, configured by a Doxyfile.

    Args:
        tmp_path (Path): pytest temporary folder.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.
    """
    if shutil.which("doxygen") is None:
        pytest.skip("doxygen not found.")

    project = make_project(tmp_path / "project")
    root = project.parent
    (root / "src").mkdir()
    (root / "src" / "hello.c").write_text(HELLO_C, encoding="utf-8")
    doxyfile = root / "tools" / "doxygen" / "Doxyfile"
    doxyfile.parent.mkdir(parents=True)
    doxyfile.write_text(DOXYFILE, encoding="utf-8")

    data = base_config()
    data["trace"]["levels"][0]["requires"].append("SW Code")
    data["trace"]["levels"].append({"name": "SW Code", "kind": "implementation", "extractor": "lobster-doxygen",
                                    "doxyfile": "tools/doxygen/Doxyfile", "trace_to": ["SW Requirement"]})
    cfg = load_config(write_config(root, data))
    run_tests(cfg)

    assert build_trace_report(cfg, online=False) == 0
    code_items = [item for tag, item in _report_items(project).items() if tag.startswith("cpp ")]
    assert [item["name"] for item in code_items] == ["hello"]
    assert code_items[0]["tracing_status"] == "OK"
    assert code_items[0]["ref_up"] == ["req SwRequirements.sw_req_hello"]
    # The doxygen output goes into the trace folder, not next to the Doxyfile.
    assert sorted(path.name for path in doxyfile.parent.iterdir()) == ["Doxyfile"]
    assert (cfg.trace_dir / "sw_code-doxygen" / "xml" / "index.xml").is_file()

    # Without doxygen, only a project with a lobster-doxygen level fails.
    # Hide only doxygen. The LOBSTER tools stay reachable through the PATH, where Windows
    # without venv has them anyway; the interpreter folder may also contain doxygen.
    monkeypatch.setenv("PATH", os.pathsep.join([str(Path(sys.executable).parent), os.environ.get("PATH", "")]))
    monkeypatch.setattr(sys, "executable", str(tmp_path / "python"))
    which = shutil.which
    monkeypatch.setattr(shutil, "which", lambda name, *args, **kwargs:
                        None if Path(name).stem == "doxygen" else which(name, *args, **kwargs))
    with pytest.raises(TrlcdocError, match=r"Tool 'doxygen' not found\..*trace level 'SW Code'"):
        build_trace_report(cfg, online=False)
    cfg = load_config(write_config(root, base_config()))
    assert build_trace_report(cfg, online=False) == 0

# Main *************************************************************************
