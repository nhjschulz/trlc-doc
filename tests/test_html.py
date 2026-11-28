"""Tests of the HTML site, built once from an example project with every document type."""

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
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any

import pytest
import sphinx
from conftest import base_config, git_init, make_project, write_config

from trlcdoc import cli, html
from trlcdoc.config import load_config
from trlcdoc.html import _build_info, _link_settings
from trlcdoc.util import clean_dir, git_output

# Variables ********************************************************************

API_COMMAND = (
    "import pathlib; p = pathlib.Path('apidoc'); p.mkdir(exist_ok=True); "
    "(p / 'index.html').write_text('<p>API reference</p>')"
)

# Documents in addition to the TRLC levels and the tracing report, one per remaining type.
EXTRA_DOCUMENTS: list[dict[str, Any]] = [
    {"id": "coverage_report", "title": "Coverage Report", "type": "html", "source": "tests:coverage"},
    {"id": "manual", "type": "rst", "source": "docs/manual.rst"},
    # A configured title replaces the first heading 'Release Notes' as page title.
    {"id": "notes", "title": "Changes", "type": "markdown", "source": "docs/notes.md"},
    {"id": "license", "title": "License information", "type": "text", "source": "LICENSE"},
    {
        "id": "api",
        "title": "API Reference",
        "type": "command",
        "command": [sys.executable, "-c", API_COMMAND],
        "output": "apidoc",
    },
]

# Expected page titles in table of contents order.
TITLES = [
    "User Manual",
    "SW-Requirements",
    "SW-Architecture",
    "SW-Tests",
    "SW-Test Results",
    "Software Tracing Report",
    "Coverage Report",
    "Changes",
    "License information",
    "API Reference",
]

# Page headings, the Markdown page keeps its own heading.
HEADINGS = [*TITLES[:7], "Release Notes", *TITLES[8:]]

# Generated pages of the documents in table of contents order.
PAGES = [
    "manual.html",
    "sw_requirements/index.html",
    "sw_architecture/index.html",
    "sw_test/index.html",
    "sw_test_results/index.html",
    "sw_tracing_report.html",
    "coverage_report.html",
    "notes.html",
    "license.html",
    "api.html",
]

# Markdown page in the docs folder, with relative links and an image of the project.
NOTES_MD = """# Release Notes

First release.

See the [manual](manual.rst#user-manual), the [license](../LICENSE), the [requirements](../trlc/swe-req),
the [module](../hello.py), the [tests](../tests/) and the [web site](https://example.com).

![Logo](logo.png)
"""

# Project owned files of the customized site, placed in the docs folder.
CUSTOM_FILES = {
    "index.rst": (
        "Welcome\n=======\n\n.. image:: {project_root}/docs/logo.png\n\n"
        ".. toctree::\n   :caption: Chapters:\n\n"
        "   guide\n   placeholder\n   sw_requirements/index\n   license\n"
    ),
    "header.rst": ".. image:: {project_root}/docs/logo.png\n   :alt: Project Logo\n",
    "guide.rst": "Guide\n=====\n\n.. literalinclude:: {project_root}/LICENSE\n   :language: none\n",
    "placeholder.md": "# Placeholder\n\nWrite `{project_root}/docs/logo.png` for the logo.\n",
    "conf.py": (
        "html_title = 'Custom Title'\n\n\n"
        "def setup(app):\n"
        "    app.connect('builder-inited', lambda app: (PROJECT_ROOT / 'setup.txt').write_text('done'))\n"
    ),
    "logo.png": "",
}

# Classes **********************************************************************

# Functions ********************************************************************


@pytest.fixture(name="site", scope="module")
def fixture_site(tmp_path_factory: pytest.TempPathFactory, plantuml_jar: Path) -> dict[str, Any]:
    """Build the HTML site of the example project with 'trlcdoc all'. The project is a subfolder of its repository.

    Args:
        tmp_path_factory (pytest.TempPathFactory): pytest temporary folder factory.
        plantuml_jar (Path): The PlantUML jar.

    Returns:
        dict[str, Any]: Exit code, project root, HTML folder and commit id.
    """
    root = tmp_path_factory.mktemp("site") / "project"
    make_project(root, diagram=True)
    (root / "docs").mkdir()
    (root / "docs" / "manual.rst").write_text("User Manual\n===========\n\nRead the manual.\n", encoding="utf-8")
    (root / "docs" / "notes.md").write_text(NOTES_MD, encoding="utf-8")
    (root / "docs" / "logo.png").write_bytes(_sphinx_png())

    data = base_config()
    data["project"]["version"] = "1.2.3"
    # The project page comes first, to check that the configured order is kept.
    data["documents"] = [EXTRA_DOCUMENTS[1], *data["documents"], EXTRA_DOCUMENTS[0], *EXTRA_DOCUMENTS[2:]]
    config_file = write_config(root, data)
    commit = git_init(root.parent)

    # The repository has no tag, so git describe gives the short commit hash.
    short_commit = git_output(["rev-parse", "--short", "HEAD"], root)
    branch = git_output(["branch", "--show-current"], root)

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setenv("PLANTUML", str(plantuml_jar))
        exit_code = cli.main(["-c", str(config_file), "all"])

    return {
        "exit_code": exit_code,
        "root": root,
        "html": root / "build" / "trlcdoc" / "html",
        "commit": commit,
        "build_info": f"from {short_commit} on branch {branch}",
    }


def _sphinx_png() -> bytes:
    """Get a valid PNG image for Sphinx, the one of the Sphinx package.

    Returns:
        bytes: The image.
    """
    return next(Path(sphinx.__file__).parent.rglob("*.png")).read_bytes()


def _page(site: dict[str, Any], name: str) -> str:
    """Read a page of the site.

    Args:
        site (dict[str, Any]): The built site.
        name (str): Page path relative to the HTML folder.

    Returns:
        str: The page content.
    """
    return (site["html"] / name).read_text(encoding="utf-8")


def test_html_site(site: dict[str, Any]) -> None:
    """The site has a start page with the table of contents and one page per document.

    Args:
        site (dict[str, Any]): The built site.
    """
    assert site["exit_code"] == 0
    index = _page(site, "index.html")
    # The project version follows the name in the start page heading and the HTML title.
    assert "<h1>example 1.2.3 documentation" in index
    assert "&#8212; example 1.2.3 documentation</title>" in index
    assert "<span>example 1.2.3 documentation</span>" in index

    toc = re.findall(r'<li class="toctree-l1"><a class="reference internal" href="([^"]+)">([^<]+)</a>', index)
    assert [title for _, title in toc] == TITLES
    for href, _ in toc:
        assert (site["html"] / href).is_file()


def test_documents(site: dict[str, Any]) -> None:
    """The documents appear in the configured order, with their configured titles.

    Args:
        site (dict[str, Any]): The built site.
    """
    for page, heading in zip(PAGES, HEADINGS, strict=True):
        assert f"<h1>{heading}" in _page(site, page)

    # The configured title of a Markdown page is its navigation and browser title.
    assert '<link rel="next" title="Changes" href="notes.html" />' in _page(site, "coverage_report.html")
    assert "<title>Changes &#8212; example" in _page(site, "notes.html")
    # Without configured title, the first heading is the title.
    assert "<title>User Manual &#8212; example" in _page(site, "manual.html")

    # The next page link follows the configured order.
    assert '<link rel="next" title="SW-Requirements" href="sw_requirements/index.html" />' in _page(site, "manual.html")


def test_document_types(site: dict[str, Any]) -> None:
    """Every document type is rendered into the site.

    Args:
        site (dict[str, Any]): The built site.
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


def test_html_customization(tmp_path: Path, plantuml_jar: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A project start page, page header, Sphinx configuration file, a page without placeholder replacement and a
    TRLC document without title.

    Args:
        tmp_path (Path): pytest temporary folder.
        plantuml_jar (Path): The PlantUML jar.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.
    """
    root = tmp_path / "project"
    make_project(root)
    (root / "docs").mkdir()
    for name, content in CUSTOM_FILES.items():
        (root / "docs" / name).write_text(content, encoding="utf-8")
    (root / "docs" / "logo.png").write_bytes(_sphinx_png())

    data = base_config()
    del data["tests"], data["trace"]
    sw_requirements = {key: value for key, value in data["documents"][0].items() if key != "title"}
    data["documents"] = [
        {"id": "guide", "type": "rst", "source": "docs/guide.rst"},
        {"id": "placeholder", "type": "markdown", "source": "docs/placeholder.md", "placeholders": False},
        sw_requirements,
        {"id": "license", "title": "License information", "type": "text", "source": "LICENSE"},
    ]
    data["html"] = {"index": "docs/index.rst", "page_header": "docs/header.rst", "conf": "docs/conf.py"}
    monkeypatch.setenv("PLANTUML", str(plantuml_jar))
    assert cli.main(["-c", str(write_config(root, data)), "all"]) == 0

    html = root / "build" / "trlcdoc" / "html"
    index = (html / "index.html").read_text(encoding="utf-8")
    toc = re.findall(r'<li class="toctree-l1"><a class="reference internal" href="([^"]+)">([^<]+)</a>', index)
    assert toc == [
        ("guide.html", "Guide"),
        ("placeholder.html", "Placeholder"),
        ("sw_requirements/index.html", "Example Requirements"),
        ("license.html", "License information"),
    ]
    assert '<img alt="_images/logo.png" src="_images/logo.png" />' in index

    # The page header is on the generated pages, with the path to the project root of each page.
    requirements = (html / "sw_requirements" / "index.html").read_text(encoding="utf-8")
    assert '<img alt="Project Logo" src="../_images/logo.png" />' in requirements
    assert "<h1>Example Requirements" in requirements
    assert '<img alt="Project Logo" src="_images/logo.png" />' in (html / "license.html").read_text(encoding="utf-8")
    guide = (html / "guide.html").read_text(encoding="utf-8")
    assert "Project Logo" not in guide
    assert "Example license text." in guide

    # A page with disabled placeholder replacement keeps the placeholder text.
    placeholder = (html / "placeholder.html").read_text(encoding="utf-8")
    assert "{project_root}/docs/logo.png" in placeholder

    # The project configuration file changes values and adds its setup.
    assert "<title>Guide &#8212; Custom Title</title>" in guide
    assert (root / "setup.txt").read_text(encoding="utf-8") == "done"
    assert not (html / ".doctrees").exists()


def test_trace_report_rst(tmp_path: Path, plantuml_jar: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The tracing report is included as site pages, one per trace level.

    Args:
        tmp_path (Path): pytest temporary folder.
        plantuml_jar (Path): The PlantUML jar.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.
    """
    root = tmp_path / "project"
    make_project(root)
    (root / "docs").mkdir()
    (root / "docs" / "header.rst").write_text(".. note:: Example page header\n", encoding="utf-8")
    data = base_config()
    data["trace"]["report"] = "rst"
    data["html"] = {"page_header": "docs/header.rst"}
    monkeypatch.setenv("PLANTUML", str(plantuml_jar))
    assert cli.main(["-c", str(write_config(root, data)), "all"]) == 0

    build = root / "build" / "trlcdoc"
    assert not (build / "trace" / "tracing_report.html").exists()
    report_dir = build / "html" / "sw_tracing_report"

    # The configured title replaces the LOBSTER title of the start page.
    start = (report_dir / "index.html").read_text(encoding="utf-8")
    assert "<h1>Software Tracing Report" in start
    assert "L.O.B.S.T.E.R." not in start
    assert "Coverage Summary" in start
    assert "Example page header" in start

    # A page per level, with the page header and the item cards.
    requirements = (report_dir / "sw_requirement.html").read_text(encoding="utf-8")
    assert "Example page header" in requirements
    assert 'id="lobster-item-' in requirements
    assert "SwRequirements.sw_req_hello" in requirements

    # The source links are relative and point to the project files.
    links = re.findall(r'href="([^"]*swe-req\.trlc)"', requirements)
    assert links
    for link in links:
        assert not Path(link).is_absolute()
        assert (report_dir / link).resolve() == (root / "trlc" / "swe-req" / "swe-req.trlc").resolve()

    # Test results link to their row on the site page, named by their record.
    results = (report_dir / "sw_test_result.html").read_text(encoding="utf-8")
    assert "sw_test_result_report.trlc" not in results
    links = re.findall(r'<a class="reference external" href="(\.\./sw_test_results/[^"]+)">([^<]+)</a>', results)
    assert links == [("../sw_test_results/index.html#sw_test_result_report.rst-test_hello_result", "test_hello_result")]
    page, anchor = links[0][0].split("#")
    assert f'<span id="{anchor}">' in (report_dir / page).read_text(encoding="utf-8")


def test_page_placeholders_site(tmp_path: Path, plantuml_jar: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A project start page with {documents} and pages linking with {page:<id>} work with both tracing report
    formats, without changes of the project pages.

    Args:
        tmp_path (Path): pytest temporary folder.
        plantuml_jar (Path): The PlantUML jar.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.
    """
    root = tmp_path / "project"
    make_project(root)
    (root / "docs").mkdir()
    (root / "docs" / "index.rst").write_text(
        "Example\n=======\n\n.. toctree::\n   :caption: Contents:\n\n   {documents}\n", encoding="utf-8"
    )
    (root / "docs" / "header.rst").write_text(
        "Back to :doc:`the requirements <{page:sw_requirements}>`.\n", encoding="utf-8"
    )
    (root / "docs" / "guide.rst").write_text(
        "Guide\n=====\n\nSee :doc:`the tracing report <{page:sw_tracing_report}>`.\n", encoding="utf-8"
    )
    data = base_config()
    data["documents"].append({"id": "guide", "type": "rst", "source": "docs/guide.rst"})
    data["html"] = {"index": "docs/index.rst", "page_header": "docs/header.rst"}
    monkeypatch.setenv("PLANTUML", str(plantuml_jar))
    html_dir = root / "build" / "trlcdoc" / "html"

    for report, tracing_page in (("rst", "sw_tracing_report/index.html"), ("html", "sw_tracing_report.html")):
        data["trace"]["report"] = report
        assert cli.main(["-c", str(write_config(root, data)), "clean", "all"]) == 0, report

        # {documents} lists every document in configuration order, with the page name of its format.
        index = (html_dir / "index.html").read_text(encoding="utf-8")
        toc = re.findall(r'<li class="toctree-l1"><a class="reference internal" href="([^"]+)">', index)
        assert toc == [
            "sw_requirements/index.html",
            "sw_architecture/index.html",
            "sw_test/index.html",
            "sw_test_results/index.html",
            tracing_page,
            "guide.html",
        ], report

        # {page:<id>} links from pages at different depths.
        guide = (html_dir / "guide.html").read_text(encoding="utf-8")
        assert f'href="{tracing_page}"' in guide, report
        tests = (html_dir / "sw_test" / "index.html").read_text(encoding="utf-8")
        assert 'href="../sw_requirements/index.html"' in tests, report


def test_html_version_info(site: dict[str, Any]) -> None:
    """Every page shows the git describe output and the branch the documentation was built from.

    Args:
        site (dict[str, Any]): The built site.
    """
    for page in ["index.html", *PAGES]:
        assert site["build_info"] in _page(site, page), page


def test_html_version_info_git_state(project: Path) -> None:
    """The version control state of the page footer for a project outside of git, with a tag,
    after a commit, with uncommitted changes and with a detached HEAD.

    Args:
        project (Path): Configuration file of the example project.
    """
    cfg = load_config(project)
    root = cfg.root
    assert _build_info(cfg) == ""

    git_init(root)
    branch = git_output(["branch", "--show-current"], root)
    _git(root, "tag", "V1.0.0")
    assert _build_info(cfg) == f" from V1.0.0 on branch {branch}"

    (root / "LICENSE").write_text("Changed license text.\n", encoding="utf-8")
    assert _build_info(cfg) == f" from V1.0.0-dirty on branch {branch}"

    _git(root, "commit", "-q", "-a", "-m", "Change the license")
    short_commit = git_output(["rev-parse", "--short", "HEAD"], root)
    assert _build_info(cfg) == f" from V1.0.0-1-g{short_commit} on branch {branch}"

    _git(root, "switch", "-q", "--detach", "V1.0.0")
    assert _build_info(cfg) == " from V1.0.0"


def _git(root: Path, *args: str) -> None:
    """Run a git command in a test repository.

    Args:
        root (Path): Repository root.
        *args (str): git arguments.
    """
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", *args],
        cwd=root,
        check=True,
        capture_output=True,
    )


def test_markdown_links(site: dict[str, Any]) -> None:
    """The relative links and images of a Markdown page are resolved against its location in the project.
    Links to the repository contain the path of the project in the repository.

    Args:
        site (dict[str, Any]): The built site.
    """
    notes = _page(site, "notes.html")
    blob = f"https://github.com/example/example/blob/{site['commit']}/project"
    tree = f"https://github.com/example/example/tree/{site['commit']}/project"
    links = re.findall(r'<a class="reference (internal|external)" href="([^"]+)">', notes)
    assert links == [
        ("internal", "manual.html#user-manual"),
        ("internal", "license.html"),
        ("internal", "sw_requirements/index.html"),
        ("external", f"{blob}/hello.py"),
        ("external", f"{tree}/tests"),
        ("external", "https://example.com"),
    ]
    assert '<img alt="Logo" src="_images/logo.png" />' in notes
    assert (site["html"] / "_images" / "logo.png").is_file()


def test_markdown_links_as_text(
    tmp_path: Path, plantuml_jar: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    """Without repository, a link to a project file of a Markdown page is shown as text with a warning.

    Args:
        tmp_path (Path): pytest temporary folder, not a git repository.
        plantuml_jar (Path): The PlantUML jar.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.
        capfd (pytest.CaptureFixture[str]): pytest output capture.
    """
    root = tmp_path / "project"
    make_project(root)
    (root / "docs").mkdir()
    (root / "docs" / "readme.md").write_text("# Readme\n\nSee [the module](../hello.py).\n", encoding="utf-8")

    data = base_config()
    del data["tests"], data["trace"]
    data["documents"] = [{"id": "readme", "type": "markdown", "source": "docs/readme.md"}]
    monkeypatch.setenv("PLANTUML", str(plantuml_jar))
    assert cli.main(["-c", str(write_config(root, data)), "all"]) == 0

    readme = (root / "build" / "trlcdoc" / "html" / "readme.html").read_text(encoding="utf-8")
    assert "<p>See <span>the module</span>.</p>" in readme
    assert "hello.py" not in readme
    assert "Link to project file 'hello.py' shown as text" in capfd.readouterr().err

    # In the repository root, the links to the repository start with the project files.
    git_init(root)
    assert _link_settings(load_config(root / "trlcdoc.yaml"))["repository_path"] == "."


class _Browser:  # pylint: disable=too-few-public-methods
    """Web browser stub, which records the opened URLs."""

    def __init__(self) -> None:
        self.urls: list[str] = []

    def open(self, url: str) -> bool:
        """Record the URL.

        Args:
            url (str): The opened URL.

        Returns:
            bool: Always True, the page was opened.
        """
        self.urls.append(url)
        return True


def test_show(project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """The show step opens the start page of the site, in the Windows browser under WSL.

    Args:
        project (Path): Configuration file of the example project.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.
        capsys (pytest.CaptureFixture[str]): pytest output capture.
    """
    # pylint: disable=protected-access
    assert "show" not in cli._selected_steps(load_config(project), ["all"])
    # pylint: enable=protected-access

    browser = _Browser()
    monkeypatch.setattr(webbrowser, "get", lambda: browser)
    monkeypatch.setattr(html, "_is_wsl", lambda: False)

    # Without site.
    assert cli.main(["-c", str(project), "show"]) == 2
    assert "run the html step first" in capsys.readouterr().out
    assert not browser.urls

    output = project.parent / "build" / "trlcdoc"
    index = clean_dir(output / "html", output) / "index.html"
    index.write_text("site", encoding="utf-8")

    # Linux and Windows: the webbrowser module opens the page.
    assert cli.main(["-c", str(project), "show"]) == 0
    assert browser.urls == [index.as_uri()]
    assert f"Opening {index}" in capsys.readouterr().out

    # Without web browser.
    def no_browser() -> Any:
        raise webbrowser.Error("could not locate runnable browser")

    monkeypatch.setattr(webbrowser, "get", no_browser)
    assert cli.main(["-c", str(project), "show"]) == 2
    assert "No web browser found" in capsys.readouterr().out

    # WSL: explorer.exe opens the Windows path of the page, also if it returns 1.
    commands: list[list[str]] = []

    def run(cmd: list[str], **_: Any) -> Any:
        commands.append(cmd)
        stdout = "\\\\wsl.localhost\\distro\\index.html\n" if cmd[0] == "wslpath" else ""
        return type("Proc", (), {"returncode": 0 if cmd[0] == "wslpath" else 1, "stdout": stdout})

    monkeypatch.setattr(html, "_is_wsl", lambda: True)
    monkeypatch.setattr(html.subprocess, "run", run)
    monkeypatch.setattr(html.shutil, "which", lambda name: f"/win/{name}" if name == "explorer.exe" else None)
    assert cli.main(["-c", str(project), "show"]) == 0
    assert commands == [["wslpath", "-w", str(index)], ["/win/explorer.exe", "\\\\wsl.localhost\\distro\\index.html"]]

    # WSL with wslview.
    commands.clear()
    monkeypatch.setattr(html.shutil, "which", lambda name: f"/usr/bin/{name}" if name == "wslview" else None)
    assert cli.main(["-c", str(project), "show"]) == 0
    assert commands == [["/usr/bin/wslview", str(index)]]

    # WSL without Windows interop: fallback to the webbrowser module, here without browser.
    commands.clear()
    monkeypatch.setattr(html.shutil, "which", lambda name: None)
    assert cli.main(["-c", str(project), "show"]) == 2
    assert not commands


# Main *************************************************************************
