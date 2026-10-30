"""Shared fixtures of the trlcdoc tests: a minimal TRLC example project and the PlantUML jar.

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

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

from trlcdoc.plantuml import DEFAULT_VERSION, DOWNLOAD_URL, _download

# Variables ********************************************************************

REPO_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = REPO_DIR / "trlc" / "model"

REQUIREMENT = """
    SwReq {name} {{
        description = "The software shall {text}."
        verification_criteria = "Check that it does."
        valid_status = AbstractRequirements.VALID_STATUS.valid
    }}
"""

REQ_TRLC = """package SwRequirements
import AbstractRequirements

section "Example Requirements" {{
{requirements}}}
"""

ARCH_TRLC = """package SwArch
import Generic
import SwRequirements

section "Example Architecture" {{

    SwArchSpec sw_arch_hello {{
        description = "The hello module returns the greeting."
        verification_criteria = "Call hello() and check the result."
        satisfies = [SwRequirements.sw_req_hello]
    }}
{diagram}}}
"""

DIAGRAM = """
    Generic.PlantUML sw_arch_hello_diagram {
        caption = "Hello Diagram"
        file_path = "img/hello.puml"
    }
"""

DIAGRAM_PUML = """@startuml hello
class "hello" as hello <<module>> {
    + hello(): str
}
@enduml
"""

TEST_TRLC = """package SwTests
import SwRequirements

section "Example Tests" {

    SwTestCase tc_hello {
        description = "Call hello() and check the greeting."
        verifies = [SwRequirements.sw_req_hello]
    }
}
"""

HELLO_PY = '''"""Example module."""


def hello() -> str:
    """Return the greeting."""
    return "Hello"
'''

TEST_HELLO_PY = '''"""Example test."""
from hello import hello


def test_hello():
    """Test the greeting."""
    assert hello() == "{expected}"
'''

PYTEST_INI = """[pytest]
pythonpath = .
addopts = -p no:cacheprovider
"""

# Classes **********************************************************************

# Functions ********************************************************************


def base_config() -> Dict[str, Any]:
    """Get the configuration of the example project with all TRLC levels.

    Returns:
        Dict[str, Any]: The configuration data.
    """
    return {
        "project": {"name": "example", "author": "Jane Doe", "copyright": "2026, Jane Doe",
                    "repository": "https://github.com/example/example.git"},
        "paths": {"trlc_model": "trlc/model", "output": "build/trlcdoc"},
        "documents": [
            {"id": "sw_requirements", "title": "SW-Requirements", "type": "trlc", "source": "trlc/swe-req",
             "converter": {"rst": "builtin:req2rst.py", "markdown": "builtin:req2markdown.py"},
             "translation": "builtin:translation.json"},
            {"id": "sw_architecture", "title": "SW-Architecture", "type": "trlc", "source": "trlc/swe-arch",
             "include": ["sw_requirements"],
             "converter": {"rst": "builtin:req2rst.py", "markdown": "builtin:req2markdown.py"},
             "translation": "builtin:translation.json"},
            {"id": "sw_test", "title": "SW-Tests", "type": "trlc", "source": "trlc/swe-test",
             "include": ["sw_requirements"],
             "converter": {"rst": "builtin:tc2rst.py", "markdown": "builtin:tc2markdown.py"},
             "translation": "builtin:translation.json"},
            {"id": "sw_test_results", "title": "SW-Test Results", "type": "test_results", "include": ["sw_test"],
             "converter": {"rst": "builtin:create_test_report_in_rst.py",
                           "markdown": "builtin:create_test_report_in_markdown.py"}},
            {"id": "sw_tracing_report", "title": "Software Tracing Report", "type": "trace_report"},
        ],
        "tests": {"runner": "pytest", "args": ["tests", "--cov=hello"],
                  "link": {"from": "test_{name}", "to": "SwTests.tc_{name}"}},
        "trace": {"levels": [
            {"name": "SW Requirement", "document": "sw_requirements", "record_type": "SwRequirements.SwReq",
             "requires": ["SW Architecture", "SW Test Case"]},
            {"name": "SW Architecture", "document": "sw_architecture", "record_type": "SwArch.SwArchSpec",
             "tags": ["satisfies"], "trace_to": ["SW Requirement"]},
            {"name": "SW Test Case", "document": "sw_test", "record_type": "SwTests.SwTestCase",
             "tags": ["verifies"], "trace_to": ["SW Requirement"], "requires": ["SW Test Result"]},
            {"name": "SW Test Result", "document": "sw_test_results", "record_type": "SwTests.SwTestCaseResult",
             "tags": ["relates"], "description_fields": ["name"], "trace_to": ["SW Test Case"]},
        ]},
    }


def write_config(root: Path, data: Dict[str, Any]) -> Path:
    """Write a trlcdoc configuration file into a project.

    Args:
        root (Path): Project root.
        data (Dict[str, Any]): Configuration data.

    Returns:
        Path: The configuration file.
    """
    config_file = root / "trlcdoc.yaml"
    config_file.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return config_file


def make_project(root: Path, untraced: bool = False, failing: bool = False, diagram: bool = False) -> Path:
    """Create the example project: TRLC model and records, a Python module and its test.

    Args:
        root (Path): Project root, created if needed.
        untraced (bool): Add a requirement without architecture and test case.
        failing (bool): Make the test fail.
        diagram (bool): Add a PlantUML diagram to the architecture (needs Java).

    Returns:
        Path: The configuration file, with the base configuration.
    """
    shutil.copytree(MODEL_DIR, root / "trlc" / "model")
    requirements = REQUIREMENT.format(name="sw_req_hello", text="greet")
    if untraced:
        requirements += REQUIREMENT.format(name="sw_req_untraced", text="do more")

    files = {
        "trlc/swe-req/swe-req.trlc": REQ_TRLC.format(requirements=requirements),
        "trlc/swe-arch/swe-arch.trlc": ARCH_TRLC.format(diagram=DIAGRAM if diagram else ""),
        "trlc/swe-test/swe-test.trlc": TEST_TRLC,
        "hello.py": HELLO_PY,
        "tests/test_hello.py": TEST_HELLO_PY.format(expected="Bye" if failing else "Hello"),
        "pytest.ini": PYTEST_INI,
        "LICENSE": "Example license text.\n",
    }
    if diagram:
        files["trlc/swe-arch/img/hello.puml"] = DIAGRAM_PUML

    for name, content in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(content, encoding="utf-8")
    return write_config(root, base_config())


def git_init(root: Path) -> str:
    """Make a project a git repository with one commit and an origin remote.

    Args:
        root (Path): Project root.

    Returns:
        str: The commit id.
    """
    def git(*args: str) -> str:
        proc = subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com", *args],
                              cwd=root, check=True, capture_output=True, text=True)
        return proc.stdout.strip()

    git("init", "-q")
    git("add", "-A")
    git("commit", "-q", "-m", "Initial commit")
    git("remote", "add", "origin", "git@github.com:example/example.git")
    return git("rev-parse", "HEAD")


@pytest.fixture(name="project")
def fixture_project(tmp_path: Path) -> Path:
    """Example project without findings.

    Args:
        tmp_path (Path): pytest temporary folder.

    Returns:
        Path: The configuration file.
    """
    return make_project(tmp_path / "project")


@pytest.fixture(name="plantuml_jar", scope="session")
def fixture_plantuml_jar(request: pytest.FixtureRequest) -> Path:
    """PlantUML jar for rendering diagrams, from $PLANTUML or downloaded once into the pytest cache.

    Args:
        request (pytest.FixtureRequest): pytest request.

    Returns:
        Path: The plantuml.jar file.
    """
    if shutil.which("java") is None:
        pytest.skip("Java runtime not found, needed by PlantUML.")

    env_jar = os.environ.get("PLANTUML")
    jar = Path(env_jar) if env_jar else Path()
    if not jar.is_file():
        jar = request.config.cache.mkdir("plantuml") / f"plantuml-{DEFAULT_VERSION}.jar"
        if not jar.is_file():
            _download(DOWNLOAD_URL.format(version=DEFAULT_VERSION), jar)
    return jar

# Main *************************************************************************
