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

import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest
from conftest import MODEL_DIR, base_config, make_project, write_config

from trlcdoc.config import load_config
from trlcdoc.testrun import RESULTS_FILE, read_junit, run_tests, write_results
from trlcdoc.util import TrlcdocError, find_tool, run_unchecked

# Variables ********************************************************************

LINK = {"property": "lobster-trace", "from": "test_{name}", "to": "SwTests.tc_{name}"}

TWO_CASES = """<testcase classname="tests.test_a" name="check_two_cases">
    <properties>
      <property name="lobster-trace" value="SwTests.tc_passing"/>
      <property name="lobster-trace" value="SwTests.tc_other"/>
    </properties>
  </testcase>"""

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
  {extra}
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
    junit.write_text(JUNIT_XML.format(extra=""), encoding="utf-8")
    results = read_junit(junit, LINK)
    assert results == [
        ("test_passing", True, ["SwTests.tc_passing"]),
        ("test_failing", False, ["SwTests.tc_failing"]),
        ("test_error", False, ["SwTests.tc_error"]),
        ("test_param[1-2]", True, ["SwTests.tc_param"]),
        ("check_with_property", True, ["SwTests.tc_other"]),
    ]

    content = _write_valid_results(tmp_path / "single", results, LINK, "relates SwTestCase")
    assert content.startswith("package SwTests")
    assert "SwTestCaseResult test_param_1_2__result {" in content
    assert "result = SwTestResult.FAILED\n        relates = SwTests.tc_failing" in content
    assert "relates = SwTests.tc_other" in content

    # A test linked to several test cases needs a relates array.
    junit.write_text(JUNIT_XML.format(extra=TWO_CASES), encoding="utf-8")
    with pytest.raises(TrlcdocError, match="check_two_cases"):
        read_junit(junit, LINK)
    array_link = {**LINK, "array": True}
    results = read_junit(junit, array_link)
    assert results[-1] == ("check_two_cases", True, ["SwTests.tc_passing", "SwTests.tc_other"])
    content = _write_valid_results(tmp_path / "array", results, array_link, "relates SwTestCase [1 .. *]")
    assert "relates = [SwTests.tc_failing]" in content
    assert "relates = [SwTests.tc_passing, SwTests.tc_other]" in content

    junit.write_text(JUNIT_XML.format(extra='<testcase classname="x" name="check_unlinked"/>'),
                     encoding="utf-8")
    with pytest.raises(TrlcdocError, match="check_unlinked"):
        read_junit(junit, LINK)


def _write_valid_results(folder: Path, results: List[Tuple[str, bool, List[str]]], link: Dict[str, Any],
                         relates: str) -> str:
    """Write the test results and check that they are valid TRLC with the test model.

    Args:
        folder (Path): Folder for the model and the records, created.
        results (List[Tuple[str, bool, List[str]]]): Test results from read_junit().
        link (Dict[str, Any]): The tests.link configuration.
        relates (str): Declaration of the relates component in the model.

    Returns:
        str: The written test result records.
    """
    shutil.copytree(MODEL_DIR, folder / "model")
    model_file = folder / "model" / "swe-test.rsl"
    model_file.write_text(model_file.read_text(encoding="utf-8").replace("relates SwTestCase", relates),
                          encoding="utf-8")
    (folder / "results").mkdir()
    (folder / "results" / "cases.trlc").write_text(
        "package SwTests\n" + "".join(f"SwTestCase tc_{name} {{ description = \"x\" verifies = [] }}\n"
                                      for name in ("passing", "failing", "error", "param", "other")),
        encoding="utf-8")
    content = write_results(results, folder / "results" / RESULTS_FILE, link).read_text(encoding="utf-8")
    assert run_unchecked([find_tool("trlc"), str(folder / "model"), str(folder / "results")], folder) == 0
    return content

# Main *************************************************************************
