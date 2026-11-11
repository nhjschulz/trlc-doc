"""Run the tests and convert the JUnit XML results into TRLC test result records.

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

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Tuple

from .config import Config
from .util import TrlcdocError, clean_dir, run_unchecked

# Variables ********************************************************************

RESULTS_FILE = "sw_test_result_report.trlc"

# pytest exit codes: 0 = all passed, 1 = some tests failed.
PYTEST_OK_CODES = (0, 1)

# Qualified TRLC record id 'Package.record' for the {id} placeholder of tests.link.output.
QUALIFIED_ID = r"(?P<id>[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*)"

# Unity test output line, e.g. 'test/test_a.c:12:test_a:INFO: lobster-trace: SwTests.tc_a'.
UNITY_OUTPUT = re.compile(r"^(?P<file>.+?):(?P<line>\d+):(?P<test>[^:\s]+):(?P<level>[A-Z]+):\s*(?P<message>.*)$")

# Classes **********************************************************************

# Functions ********************************************************************


def run_tests(cfg: Config) -> bool:
    # lobster-trace: SwRequirements.sw_req_test_run
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
    write_results(results, clean_dir(cfg.test_results_dir, cfg.output) / RESULTS_FILE, tests["link"])

    failed = [name for name, passed, _ in results if not passed]
    print(f"Tests: {len(results)} results, {len(failed)} failed.")
    for name in failed:
        print(f"  FAILED: {name}")
    return not failed


def read_junit(junit_file: Path, link: Dict[str, Any]) -> List[Tuple[str, bool, List[str]]]:
    # lobster-trace: SwRequirements.sw_req_test_results
    """Read the test results and link them to their TRLC test cases.

    Skipped tests have no result and are not part of the list.

    Args:
        junit_file (Path): JUnit XML file.
        link (Dict[str, Any]): The tests.link configuration.

    Returns:
        List[Tuple[str, bool, List[str]]]: (test name, passed, qualified test case ids) per test.

    Raises:
        TrlcdocError: If a test cannot be linked to a test case, or to several
        test cases while tests.link.array is not set.
    """
    results: List[Tuple[str, bool, List[str]]] = []
    unlinked: List[str] = []
    ambiguous: List[str] = []
    for suite in ET.parse(junit_file).getroot().iter("testsuite"):
        suite_ids = _suite_output_ids(suite, link)
        for testcase in suite.findall("testcase"):
            name = testcase.get("name", "")
            skipped = testcase.find("skipped") is not None
            if not skipped:
                passed = testcase.find("failure") is None and testcase.find("error") is None
                test_case_ids = _linked_test_cases(testcase, link, suite_ids.get(name, []))
                if not test_case_ids:
                    unlinked.append(name)
                elif len(test_case_ids) > 1 and not link.get("array", False):
                    ambiguous.append(name)
                else:
                    results.append((name, passed, test_case_ids))

    if unlinked:
        raise TrlcdocError(f"Tests without test case link ({_link_methods(link)}): {', '.join(unlinked)}")
    if ambiguous:
        raise TrlcdocError(
            f"Tests linked to several test cases, which needs tests.link.array: {', '.join(ambiguous)}")
    return results


def _link_methods(link: Dict[str, Any]) -> str:
    # lobster-trace: SwRequirements.sw_req_test_results
    """Describe the configured link methods for an error message.

    Args:
        link (Dict[str, Any]): The tests.link configuration.

    Returns:
        str: The link methods, e.g. "property 'lobster-trace', output 'lobster-trace: {id}'".
    """
    methods = [f"property '{link.get('property', 'lobster-trace')}'"]
    if "output" in link:
        methods.append(f"output '{link['output']}'")
    if "from" in link:
        methods.append(f"name pattern '{link['from']}'")
    return ", ".join(methods)


def _output_regex(link: Dict[str, Any]) -> Optional[Pattern[str]]:
    # lobster-trace: SwRequirements.sw_req_test_results
    """Compile the tests.link.output pattern.

    Args:
        link (Dict[str, Any]): The tests.link configuration.

    Returns:
        Optional[Pattern[str]]: Regular expression with the group 'id', None without output link.
    """
    result = None
    if "output" in link:
        result = re.compile(re.escape(link["output"]).replace(re.escape("{id}"), QUALIFIED_ID))
    return result


def _output_ids(lines: List[str], regex: Pattern[str]) -> List[str]:
    # lobster-trace: SwRequirements.sw_req_test_results
    """Find the test case ids in output lines.

    Args:
        lines (List[str]): Output lines.
        regex (Pattern[str]): Compiled tests.link.output pattern.

    Returns:
        List[str]: The test case ids in order of appearance.
    """
    return [match.group("id") for match in (regex.search(line) for line in lines) if match is not None]


def _system_out(element: ET.Element) -> List[str]:
    # lobster-trace: SwRequirements.sw_req_test_results
    """Get the lines of the system-out elements directly below an element.

    Args:
        element (ET.Element): JUnit testsuite or testcase element.

    Returns:
        List[str]: The output lines.
    """
    return [line.strip() for out in element.findall("system-out") for line in (out.text or "").splitlines()]


def _suite_output_ids(suite: ET.Element, link: Dict[str, Any]) -> Dict[str, List[str]]:
    # lobster-trace: SwRequirements.sw_req_test_results
    """Get the test case ids of the suite output per test.

    Only lines in Unity format '<file>:<line>:<test>:<level>: <message>' are used, the test name
    assigns them to the test.

    Args:
        suite (ET.Element): JUnit testsuite element.
        link (Dict[str, Any]): The tests.link configuration.

    Returns:
        Dict[str, List[str]]: Test case ids per test name, empty without output link.
    """
    result: Dict[str, List[str]] = {}
    regex = _output_regex(link)
    if regex is not None:
        for line in _system_out(suite):
            unity = UNITY_OUTPUT.match(line)
            if unity is not None:
                result.setdefault(unity.group("test"), []).extend(_output_ids([unity.group("message")], regex))
    return result


def _linked_test_cases(testcase: ET.Element, link: Dict[str, Any], suite_ids: List[str]) -> List[str]:
    # lobster-trace: SwRequirements.sw_req_test_results
    """Get the qualified TRLC test case ids of a JUnit test case.

    The link methods are tried in this order: property, test output, name pattern.

    Args:
        testcase (ET.Element): JUnit testcase element.
        link (Dict[str, Any]): The tests.link configuration.
        suite_ids (List[str]): Test case ids of this test in the suite output.

    Returns:
        List[str]: The test case ids without duplicates, empty if the test cannot be linked.
    """
    property_name = link.get("property", "lobster-trace")
    result = [prop.get("value", "") for prop in testcase.iter("property") if prop.get("name") == property_name]

    regex = _output_regex(link)
    if not result and regex is not None:
        result = _output_ids(_system_out(testcase), regex) + suite_ids

    if not result and "from" in link:
        # Remove pytest parametrization, e.g. test_foo[1-2] -> test_foo.
        name = testcase.get("name", "").split("[")[0]
        pattern = "^" + re.escape(link["from"]).replace(re.escape("{name}"), r"(?P<name>\w+)") + "$"
        match = re.match(pattern, name)
        if match is not None:
            result = [link["to"].format(name=match.group("name"))]
    return list(dict.fromkeys(result))


def _results_package(results: List[Tuple[str, bool, List[str]]]) -> str:
    # lobster-trace: SwRequirements.sw_req_test_results
    """Get the package of the linked test cases, which is the package of the result records.

    Args:
        results (List[Tuple[str, bool, List[str]]]): (test name, passed, qualified test case ids) per test.

    Returns:
        str: The package name.

    Raises:
        TrlcdocError: If there is no linked test case, a test case id is not qualified, or the
        test cases belong to several packages.
    """
    packages: Dict[str, List[str]] = {}
    unqualified: List[str] = []
    for name, _, test_case_ids in results:
        for test_case_id in test_case_ids:
            if "." in test_case_id:
                packages.setdefault(test_case_id.split(".")[0], []).append(name)
            else:
                unqualified.append(f"{name} ({test_case_id})")

    if unqualified:
        raise TrlcdocError(f"Tests linked to test case ids without package: {', '.join(unqualified)}")
    if not packages:
        raise TrlcdocError("No test linked to a test case, the package of the test results is unknown.")
    if len(packages) > 1:
        details = "; ".join(f"{package}: {', '.join(dict.fromkeys(names))}" for package, names in packages.items())
        raise TrlcdocError(f"Tests linked to test cases of several packages: {details}")
    return next(iter(packages))


def write_results(results: List[Tuple[str, bool, List[str]]], trlc_file: Path, link: Dict[str, Any]) -> Path:
    # lobster-trace: SwRequirements.sw_req_test_results
    """Write the test results as TRLC SwTestCaseResult records.

    The records are written into the package of the linked test cases.

    Args:
        results (List[Tuple[str, bool, List[str]]]): (test name, passed, qualified test case ids) per test.
        trlc_file (Path): TRLC file to write.
        link (Dict[str, Any]): The tests.link configuration. With 'array' the relates
            component is written as list, otherwise as single reference.

    Returns:
        Path: The written file.

    Raises:
        TrlcdocError: If the package of the test cases cannot be determined.
    """
    package = _results_package(results)
    used_ids: Dict[str, int] = {}
    with open(trlc_file, "w", encoding="utf-8") as file:
        file.write(f"package {package}\n\n")
        file.write('section "SW Test Results" {\n\n')
        for name, passed, test_case_ids in results:
            record_id = re.sub(r"\W", "_", name) + "_result"
            used_ids[record_id] = used_ids.get(record_id, 0) + 1
            if used_ids[record_id] > 1:
                record_id += f"_{used_ids[record_id]}"
            result = "PASSED" if passed else "FAILED"
            file.write(f"    SwTestCaseResult {record_id} {{\n")
            file.write(f'        name = "{name}"\n')
            file.write(f"        result = SwTestResult.{result}\n")
            relates = f"[{', '.join(test_case_ids)}]" if link.get("array", False) else test_case_ids[0]
            file.write(f"        relates = {relates}\n")
            file.write("    }\n\n")
        file.write("}\n")
    return trlc_file

# Main *************************************************************************
