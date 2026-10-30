"""Tests of the LOBSTER tracing report.

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
import yaml
from conftest import base_config, git_init, make_project, write_config

from trlcdoc import cli
from trlcdoc.config import load_config
from trlcdoc.testrun import run_tests
from trlcdoc.trace import build_trace_report

# Variables ********************************************************************

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
    """The HTML tracing report links to local files, or to the repository when online.

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

# Main *************************************************************************
