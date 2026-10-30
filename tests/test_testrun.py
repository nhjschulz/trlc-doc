"""Tests of the test runner and the conversion of the test results into TRLC records.

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

import sys
from pathlib import Path

import pytest
from conftest import base_config, make_project, write_config

from trlcdoc.config import load_config
from trlcdoc.testrun import RESULTS_FILE, read_junit, run_tests, write_results
from trlcdoc.util import TrlcdocError, find_tool, run_unchecked

# Variables ********************************************************************

LINK = {"property": "lobster-trace", "from": "test_{name}", "to": "SwTests.tc_{name}"}

JUNIT_XML = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest">
  <testcase classname="tests.test_a" name="test_passing"/>
  <testcase classname="tests.test_a" name="test_failing"><failure message="assert"/></testcase>
  <testcase classname="tests.test_a" name="test_error"><error message="exception"/></testcase>
  <testcase classname="tests.test_a" name="test_param[1-2]"/>
  <testcase classname="tests.test_a" name="test_skipped"><skipped message="skip"/></testcase>
  <testcase classname="tests.test_a" name="check_with_property">
    <properties><property name="lobster-trace" value="SwTests.tc_other"/></properties>
  </testcase>
  {unlinked}
</testsuite></testsuites>
"""

# Classes **********************************************************************

# Functions ********************************************************************


def test_test_run(tmp_path: Path) -> None:
    """The tests run with pytest and a coverage report, or with a configured command.

    Args:
        tmp_path (Path): pytest temporary folder.
    """
    cfg = load_config(make_project(tmp_path / "pytest"))
    assert run_tests(cfg) is True
    assert cfg.junit_file.is_file()
    assert (cfg.coverage_dir / "index.html").is_file()
    assert not (cfg.root / ".coverage").exists()

    failing = load_config(make_project(tmp_path / "failing", failing=True))
    assert run_tests(failing) is False

    root = tmp_path / "command"
    make_project(root)
    data = base_config()
    data["tests"] = {"runner": "command",
                     "command": [sys.executable, "-m", "pytest", "tests", "--junitxml=out/results.xml"],
                     "junit": "out/results.xml", "link": data["tests"]["link"]}
    cfg = load_config(write_config(root, data))
    assert cfg.junit_file == root / "out" / "results.xml"
    assert run_tests(cfg) is True
    assert "tc_hello" in (cfg.test_results_dir / RESULTS_FILE).read_text(encoding="utf-8")

    data["tests"]["command"] = [sys.executable, "-c", "pass"]
    data["tests"]["junit"] = "out/none.xml"
    with pytest.raises(TrlcdocError, match="was not created"):
        run_tests(load_config(write_config(root, data)))


def test_test_results(tmp_path: Path) -> None:
    """Test results are linked to their test cases and written as TRLC records.

    Args:
        tmp_path (Path): pytest temporary folder.
    """
    junit = tmp_path / "junit.xml"
    junit.write_text(JUNIT_XML.format(unlinked=""), encoding="utf-8")
    results = read_junit(junit, LINK)
    assert results == [
        ("test_passing", True, "SwTests.tc_passing"),
        ("test_failing", False, "SwTests.tc_failing"),
        ("test_error", False, "SwTests.tc_error"),
        ("test_param[1-2]", True, "SwTests.tc_param"),
        ("check_with_property", True, "SwTests.tc_other"),
    ]

    (tmp_path / "results").mkdir()
    trlc_file = write_results(results, tmp_path / "results" / RESULTS_FILE, LINK["to"])
    content = trlc_file.read_text(encoding="utf-8")
    assert content.startswith("package SwTests")
    assert "SwTestCaseResult test_param_1_2__result {" in content
    assert "result = SwTestResult.FAILED\n        relates = SwTests.tc_failing" in content
    assert "relates = SwTests.tc_other" in content

    # The records are valid TRLC with the test model.
    model = Path(__file__).resolve().parents[1] / "trlc" / "model"
    (tmp_path / "results" / "cases.trlc").write_text(
        "package SwTests\n" + "".join(f"SwTestCase tc_{name} {{ description = \"x\" verifies = [] }}\n"
                                      for name in ("passing", "failing", "error", "param", "other")),
        encoding="utf-8")
    assert run_unchecked([find_tool("trlc"), str(model), str(tmp_path / "results")], tmp_path) == 0

    junit.write_text(JUNIT_XML.format(unlinked='<testcase classname="x" name="check_unlinked"/>'),
                     encoding="utf-8")
    with pytest.raises(TrlcdocError, match="check_unlinked"):
        read_junit(junit, LINK)

# Main *************************************************************************
