"""Run the tests and convert the JUnit XML results into TRLC test result records.

    Author: Norbert Schulz (norbert.schulz@newtec.de)
"""

# *******************************************************************************
# Copyright (c) NewTec GmbH 2026   -   www.newtec.de
# *******************************************************************************

# Imports **********************************************************************

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import Config
from .util import TrlcdocError, clean_dir, run_unchecked

# Variables ********************************************************************

RESULTS_FILE = "sw_test_result_report.trlc"

# pytest exit codes: 0 = all passed, 1 = some tests failed.
PYTEST_OK_CODES = (0, 1)

# Classes **********************************************************************

# Functions ********************************************************************


def run_tests(cfg: Config) -> bool:
    """Run the tests and create the TRLC test result records.

    Args:
        cfg (Config): Project configuration with a tests section.

    Returns:
        bool: True if all tests passed.

    Raises:
        TrlcdocError: If the tests could not be executed.
    """
    tests = cfg.tests
    clean_dir(cfg.tests_dir, cfg.output)

    if tests["runner"] == "pytest":
        args = list(tests.get("args", []))
        cmd = [sys.executable, "-m", "pytest", *args,
               "-o", "junit_family=xunit1", f"--junitxml={cfg.junit_file}"]
        if any(arg.startswith("--cov") for arg in args):
            cmd.extend(["--cov-report=term", f"--cov-report=html:{cfg.coverage_dir}"])
        # Keep the coverage data file in the output folder instead of the project root.
        returncode = run_unchecked(cmd, cfg.root, {"COVERAGE_FILE": str(cfg.tests_dir / ".coverage")})
        if returncode not in PYTEST_OK_CODES:
            raise TrlcdocError(f"pytest could not run the tests (exit code {returncode}).")
    else:
        run_unchecked(tests["command"], cfg.root)

    if not cfg.junit_file.is_file():
        raise TrlcdocError(f"Test result file {cfg.junit_file} was not created.")

    results = read_junit(cfg.junit_file, tests["link"])
    write_results(results, clean_dir(cfg.test_results_dir, cfg.output) / RESULTS_FILE, tests["link"]["to"])

    failed = [name for name, passed, _ in results if not passed]
    print(f"Tests: {len(results)} results, {len(failed)} failed.")
    for name in failed:
        print(f"  FAILED: {name}")
    return not failed


def read_junit(junit_file: Path, link: Dict[str, Any]) -> List[Tuple[str, bool, str]]:
    """Read the test results and link them to their TRLC test cases.

    Skipped tests have no result and are not part of the list.

    Args:
        junit_file (Path): JUnit XML file.
        link (Dict[str, Any]): The tests.link configuration.

    Returns:
        List[Tuple[str, bool, str]]: (test name, passed, qualified test case id) per test.

    Raises:
        TrlcdocError: If a test cannot be linked to a test case.
    """
    results: List[Tuple[str, bool, str]] = []
    unlinked: List[str] = []
    for testcase in ET.parse(junit_file).getroot().iter("testcase"):
        name = testcase.get("name", "")
        skipped = testcase.find("skipped") is not None
        if not skipped:
            passed = testcase.find("failure") is None and testcase.find("error") is None
            test_case_id = _linked_test_case(testcase, link)
            if test_case_id is None:
                unlinked.append(name)
            else:
                results.append((name, passed, test_case_id))

    if unlinked:
        raise TrlcdocError(
            f"Tests not matching tests.link.from '{link['from']}' and without "
            f"'{link.get('property', 'lobster-trace')}' property: {', '.join(unlinked)}")
    return results


def _linked_test_case(testcase: ET.Element, link: Dict[str, Any]) -> Optional[str]:
    """Get the qualified TRLC test case id of a JUnit test case.

    Args:
        testcase (ET.Element): JUnit testcase element.
        link (Dict[str, Any]): The tests.link configuration.

    Returns:
        Optional[str]: The test case id, or None if the test cannot be linked.
    """
    property_name = link.get("property", "lobster-trace")
    result = None
    for prop in testcase.iter("property"):
        if prop.get("name") == property_name:
            result = prop.get("value")

    if result is None:
        # Remove pytest parametrization, e.g. test_foo[1-2] -> test_foo.
        name = testcase.get("name", "").split("[")[0]
        pattern = "^" + re.escape(link["from"]).replace(re.escape("{name}"), r"(?P<name>\w+)") + "$"
        match = re.match(pattern, name)
        if match is not None:
            result = link["to"].format(name=match.group("name"))
    return result


def write_results(results: List[Tuple[str, bool, str]], trlc_file: Path, to_pattern: str) -> Path:
    """Write the test results as TRLC SwTestCaseResult records.

    The records are written into the package of the test cases, taken from tests.link.to.

    Args:
        results (List[Tuple[str, bool, str]]): (test name, passed, qualified test case id) per test.
        trlc_file (Path): TRLC file to write.
        to_pattern (str): The tests.link.to pattern, e.g. 'SwTests.tc_{name}'.

    Returns:
        Path: The written file.
    """
    package = to_pattern.split(".")[0]
    used_ids: Dict[str, int] = {}
    with open(trlc_file, "w", encoding="utf-8") as file:
        file.write(f"package {package}\n\n")
        file.write('section "SW Test Results" {\n\n')
        for name, passed, test_case_id in results:
            record_id = re.sub(r"\W", "_", name) + "_result"
            used_ids[record_id] = used_ids.get(record_id, 0) + 1
            if used_ids[record_id] > 1:
                record_id += f"_{used_ids[record_id]}"
            result = "PASSED" if passed else "FAILED"
            file.write(f"    SwTestCaseResult {record_id} {{\n")
            file.write(f'        name = "{name}"\n')
            file.write(f"        result = SwTestResult.{result}\n")
            file.write(f"        relates = {test_case_id}\n")
            file.write("    }\n\n")
        file.write("}\n")
    return trlc_file

# Main *************************************************************************
