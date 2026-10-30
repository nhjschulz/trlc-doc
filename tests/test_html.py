"""Tests of the HTML site, built once from an example project with every document type.

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

import re
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest
from conftest import base_config, git_init, make_project, write_config

from trlcdoc import cli

# Variables ********************************************************************

API_COMMAND = ("import pathlib; p = pathlib.Path('apidoc'); p.mkdir(exist_ok=True); "
               "(p / 'index.html').write_text('<p>API reference</p>')")

# Documents in addition to the TRLC levels and the tracing report, one per remaining type.
EXTRA_DOCUMENTS: List[Dict[str, Any]] = [
    {"id": "coverage_report", "title": "Coverage Report", "type": "html", "source": "tests:coverage"},
    {"id": "manual", "type": "rst", "source": "docs/manual.rst"},
    {"id": "notes", "type": "markdown", "source": "docs/notes.md"},
    {"id": "license", "title": "License information", "type": "text", "source": "LICENSE"},
    {"id": "api", "title": "API Reference", "type": "command", "command": [sys.executable, "-c", API_COMMAND],
     "output": "apidoc"},
]

# Expected page titles in table of contents order.
TITLES = ["User Manual", "SW-Requirements", "SW-Architecture", "SW-Tests", "SW-Test Results",
          "Software Tracing Report", "Coverage Report", "Release Notes", "License information", "API Reference"]

# Generated pages of the documents in table of contents order.
PAGES = ["manual.html", "sw_requirements/index.html", "sw_architecture/index.html", "sw_test/index.html",
         "sw_test_results/index.html", "sw_tracing_report.html", "coverage_report.html", "notes.html",
         "license.html", "api.html"]

# Classes **********************************************************************

# Functions ********************************************************************


@pytest.fixture(name="site", scope="module")
def fixture_site(tmp_path_factory: pytest.TempPathFactory, plantuml_jar: Path) -> Dict[str, Any]:
    """Build the HTML site of the example project with 'trlcdoc all'.

    Args:
        tmp_path_factory (pytest.TempPathFactory): pytest temporary folder factory.
        plantuml_jar (Path): The PlantUML jar.

    Returns:
        Dict[str, Any]: Exit code, project root, HTML folder and commit id.
    """
    root = tmp_path_factory.mktemp("site") / "project"
    make_project(root, diagram=True)
    (root / "docs").mkdir()
    (root / "docs" / "manual.rst").write_text("User Manual\n===========\n\nRead the manual.\n", encoding="utf-8")
    (root / "docs" / "notes.md").write_text("# Release Notes\n\nFirst release.\n", encoding="utf-8")

    data = base_config()
    # The project page comes first, to check that the configured order is kept.
    data["documents"] = [EXTRA_DOCUMENTS[1], *data["documents"], EXTRA_DOCUMENTS[0], *EXTRA_DOCUMENTS[2:]]
    config_file = write_config(root, data)
    commit = git_init(root)

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setenv("PLANTUML", str(plantuml_jar))
        exit_code = cli.main(["-c", str(config_file), "all"])

    return {"exit_code": exit_code, "root": root, "html": root / "build" / "trlcdoc" / "html", "commit": commit}


def _page(site: Dict[str, Any], name: str) -> str:
    """Read a page of the site.

    Args:
        site (Dict[str, Any]): The built site.
        name (str): Page path relative to the HTML folder.

    Returns:
        str: The page content.
    """
    return (site["html"] / name).read_text(encoding="utf-8")


def test_html_site(site: Dict[str, Any]) -> None:
    """The site has a start page with the table of contents and one page per document.

    Args:
        site (Dict[str, Any]): The built site.
    """
    assert site["exit_code"] == 0
    index = _page(site, "index.html")
    assert "<h1>example documentation" in index

    toc = re.findall(r'<li class="toctree-l1"><a class="reference internal" href="([^"]+)">([^<]+)</a>', index)
    assert [title for _, title in toc] == TITLES
    for href, _ in toc:
        assert (site["html"] / href).is_file()


def test_documents(site: Dict[str, Any]) -> None:
    """The documents appear in the configured order, with their configured titles.

    Args:
        site (Dict[str, Any]): The built site.
    """
    for page, title in zip(PAGES, TITLES):
        assert f"<h1>{title}" in _page(site, page)

    # The next page link follows the configured order.
    assert '<link rel="next" title="SW-Requirements" href="sw_requirements/index.html" />' in _page(site, "manual.html")


def test_document_types(site: Dict[str, Any]) -> None:
    """Every document type is rendered into the site.

    Args:
        site (Dict[str, Any]): The built site.
    """
    assert "The software shall greet." in _page(site, "sw_requirements/index.html")
    architecture = _page(site, "sw_architecture/index.html")
    assert "The hello module returns the greeting." in architecture
    assert "Hello Diagram" in architecture
    assert list((site["html"] / "_images").glob("hello*"))
    assert "Call hello() and check the greeting." in _page(site, "sw_test/index.html")
    assert "test_hello" in _page(site, "sw_test_results/index.html")
    assert "sw_req_hello" in _page(site, "sw_tracing_report.html")

    assert '<iframe src="coverage_report/index.html"' in _page(site, "coverage_report.html")
    assert (site["html"] / "coverage_report" / "index.html").is_file()
    assert "Read the manual." in _page(site, "manual.html")
    assert "First release." in _page(site, "notes.html")
    assert "Example license text." in _page(site, "license.html")
    assert '<iframe src="api/index.html"' in _page(site, "api.html")
    assert "API reference" in _page(site, "api/index.html")


def test_html_version_info(site: Dict[str, Any]) -> None:
    """Every page shows the commit the documentation was built from.

    Args:
        site (Dict[str, Any]): The built site.
    """
    for page in ["index.html", *PAGES]:
        assert f"from commit {site['commit']}" in _page(site, page), page

# Main *************************************************************************
