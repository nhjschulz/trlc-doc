"""Generate the Sphinx sources from the configured documents and build the HTML site."""

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
import platform
import re
import shutil
import subprocess
import webbrowser
from pathlib import Path
from typing import Any

from sphinx.cmd.build import build_main

from .config import PACKAGE_DIR, TRLC_DOCUMENT_TYPES, Config
from .pages import replace_placeholders
from .util import TrlcdocError, clean_dir, git_output, git_root, repository_url, run

# Variables ********************************************************************

SPHINX_TEMPLATE_DIR = PACKAGE_DIR / "sphinx"

# Included converter output gets this suffix, so Sphinx does not treat it as a document.
INCLUDE_SUFFIX = ".inc"

# Sphinx extensions of the reStructuredText tracing report: dropdown cards and the tracing policy diagram.
RST_TRACE_REPORT_EXTENSIONS = ["sphinx_design", "sphinx.ext.graphviz"]

# Underline character of the page titles. reStructuredText derives the heading level
# from the order the characters appear in a page. pyTRLCConverter underlines its
# levels with = # ~ ^ " + ', so '-' keeps the page title above the included content.
PAGE_TITLE_CHAR = "-"

# Classes **********************************************************************

# Functions ********************************************************************


def build_html(cfg: Config) -> Path:
    # lobster-trace: SwRequirements.sw_req_html_site
    """Generate the Sphinx source folder and build the HTML site.

    Args:
        cfg (Config): Project configuration.

    Returns:
        Path: The HTML output folder.

    Raises:
        TrlcdocError: If an input is missing or Sphinx reports an error.
    """
    src_dir = clean_dir(cfg.sphinx_dir, cfg.output)
    shutil.copy(SPHINX_TEMPLATE_DIR / "conf.py", src_dir / "conf.py")
    shutil.copytree(SPHINX_TEMPLATE_DIR / "_static", src_dir / "_static")

    pages: list[str] = []
    copy_dirs: list[dict[str, str]] = []
    for doc in cfg.documents:
        pages.append(_write_page(cfg, doc, src_dir, copy_dirs))

    _write_index(cfg, src_dir, pages)
    _write_sphinx_config(cfg, src_dir, copy_dirs)

    out_dir = clean_dir(cfg.html_dir, cfg.output)
    # The Sphinx doctree cache is kept out of the HTML site.
    doctrees_dir = clean_dir(cfg.output / "doctrees", cfg.output)
    print(f"Building HTML -> {out_dir}")
    if build_main(["-b", "html", "-q", "-d", str(doctrees_dir), str(src_dir), str(out_dir)]) != 0:
        raise TrlcdocError("Sphinx HTML build failed.")
    return out_dir


def show_html(cfg: Config) -> Path:
    # lobster-trace: SwRequirements.sw_req_show
    """Open the start page of the built HTML site in the web browser.

    Under WSL, the site opens in the Windows default browser (wslview or explorer.exe).
    Without Windows interop, and on all other systems, the Python webbrowser module
    selects the browser, which the BROWSER environment variable can override.

    Args:
        cfg (Config): Project configuration.

    Returns:
        Path: The opened start page.

    Raises:
        TrlcdocError: If the site is not built or no web browser is available.
    """
    index = cfg.html_dir / "index.html"
    if not index.is_file():
        raise TrlcdocError(f"No HTML site found at {index}, run the html step first.")

    print(f"Opening {index}")
    if not (_is_wsl() and _open_in_windows(index)):
        try:
            opened = webbrowser.get().open(index.as_uri())
        except webbrowser.Error:
            opened = False
        if not opened:
            raise TrlcdocError(
                f"No web browser found to open {index}. Set the BROWSER environment variable "
                "to the command of a web browser, or open the file manually."
            )
    return index


def _is_wsl() -> bool:
    # lobster-trace: SwRequirements.sw_req_show
    """Check whether trlcdoc runs in the Windows Subsystem for Linux.

    Returns:
        bool: True under WSL.
    """
    return "WSL_DISTRO_NAME" in os.environ or "microsoft" in platform.uname().release.lower()


def _open_in_windows(index: Path) -> bool:
    # lobster-trace: SwRequirements.sw_req_show
    """Open a file of the WSL file system in the Windows default browser.

    Args:
        index (Path): The page to open.

    Returns:
        bool: True if the page was handed to Windows, False without Windows interop.
    """
    cmd: list[str] | None = None
    wslview = shutil.which("wslview")
    explorer = shutil.which("explorer.exe")
    if wslview is not None:
        cmd = [wslview, str(index)]
    elif explorer is not None:
        windows_path = _windows_path(index)
        if windows_path is not None:
            cmd = [explorer, windows_path]

    if cmd is not None:
        # explorer.exe returns 1 also on success, so the exit code is not checked.
        subprocess.run(cmd, check=False)

    return cmd is not None


def _windows_path(path: Path) -> str | None:
    # lobster-trace: SwRequirements.sw_req_show
    """Convert a WSL path into a Windows path with wslpath.

    Args:
        path (Path): Path in the WSL file system.

    Returns:
        str | None: The Windows path, or None if wslpath failed.
    """
    result = None
    try:
        proc = subprocess.run(["wslpath", "-w", str(path)], capture_output=True, text=True, check=False)
        if proc.returncode == 0 and proc.stdout.strip():
            result = proc.stdout.strip()
    except OSError:
        result = None

    return result


def _heading(title: str, char: str = PAGE_TITLE_CHAR) -> str:
    # lobster-trace: SwRequirements.sw_req_html_site
    """Create a reStructuredText heading.

    Args:
        title (str): Heading text.
        char (str): Underline character, defaults to the page title character.

    Returns:
        str: The heading with a trailing empty line.
    """
    return f"{title}\n{char * len(title)}\n\n"


def _write_page(cfg: Config, doc: dict[str, Any], src_dir: Path, copy_dirs: list[dict[str, str]]) -> str:
    # lobster-trace: SwRequirements.sw_req_documents
    # lobster-trace: SwRequirements.sw_req_document_types
    """Write the Sphinx page of a document.

    Args:
        cfg (Config): Project configuration.
        doc (dict[str, Any]): Document configuration.
        src_dir (Path): Sphinx source folder.
        copy_dirs (list[dict[str, str]]): Collects HTML folders to copy into the site.

    Returns:
        str: Page name for the table of contents.

    Raises:
        TrlcdocError: If an input of the document is missing.
    """
    doc_type = doc["type"]
    page_file = src_dir / f"{doc['id']}.rst"

    if doc_type in TRLC_DOCUMENT_TYPES:
        _write_converted_page(cfg, doc, src_dir)
    elif doc_type == "trace_report" and cfg.trace_report_format == "rst":
        _write_rst_trace_report(cfg, doc, src_dir)
    elif doc_type == "trace_report":
        _require(cfg.trace_report_html, "run the trace step first")
        _write_generated(cfg, page_file, doc, f".. raw:: html\n   :file: {cfg.trace_report_html.as_posix()}\n")
    elif doc_type in ("html", "command"):
        if doc_type == "command":
            run(doc["command"], cfg.root)
        html_source = cfg.html_source(doc)
        _require(html_source / "index.html", "generate it first")
        copy_dirs.append({"source": str(html_source), "destination": doc["id"]})
        _write_generated(
            cfg,
            page_file,
            doc,
            f'.. raw:: html\n\n    <iframe src="{doc["id"]}/index.html" width="100%" height="1024px"></iframe>\n',
        )
    elif doc_type == "text":
        source = _require(cfg.path(doc["source"]), "check the source path")
        # Sphinx treats absolute include paths as relative to the source folder.
        relative = Path(os.path.relpath(source, src_dir)).as_posix()
        _write_generated(cfg, page_file, doc, f".. literalinclude:: {relative}\n   :language: none\n")
    else:
        source = _require(cfg.path(doc["source"]), "check the source path")
        page_file = page_file.with_suffix(".md" if doc_type == "markdown" else ".rst")
        _write_project_page(cfg, source, page_file, doc.get("placeholders", True))

    return cfg.page_name(doc)


def _write_project_page(cfg: Config, source: Path, page_file: Path, placeholders: bool = True) -> Path:
    # lobster-trace: SwRequirements.sw_req_document_types
    # lobster-trace: SwRequirements.sw_req_html_customization
    """Write a project owned page into the Sphinx source folder.

    Args:
        cfg (Config): Project configuration.
        source (Path): The project page.
        page_file (Path): The page in the Sphinx source folder.
        placeholders (bool): Replace the placeholders, False copies the page unchanged.

    Returns:
        Path: The written page.
    """
    text = source.read_text(encoding="utf-8")
    if placeholders:
        text = replace_placeholders(cfg, text, page_file)
    page_file.write_text(text, encoding="utf-8")
    return page_file


def _write_generated(cfg: Config, page_file: Path, doc: dict[str, Any], body: str) -> Path:
    # lobster-trace: SwRequirements.sw_req_documents
    # lobster-trace: SwRequirements.sw_req_html_customization
    """Write a generated page: the page header, the title of the document and the body.

    Args:
        cfg (Config): Project configuration.
        page_file (Path): The page in the Sphinx source folder.
        doc (dict[str, Any]): Document configuration, a page without title gets no heading.
        body (str): Page content below the title.

    Returns:
        Path: The written page.
    """
    content = _page_header(cfg, page_file)
    if "title" in doc:
        content += _heading(doc["title"])
    page_file.write_text(content + body, encoding="utf-8")
    return page_file


def _page_header(cfg: Config, page_file: Path) -> str:
    # lobster-trace: SwRequirements.sw_req_html_customization
    """Get the configured page header for a generated page.

    Args:
        cfg (Config): Project configuration.
        page_file (Path): The page in the Sphinx source folder.

    Returns:
        str: The page header followed by a blank line, or an empty string without page header.
    """
    if "page_header" not in cfg.html:
        return ""
    header = cfg.path(cfg.html["page_header"]).read_text(encoding="utf-8")
    return replace_placeholders(cfg, header, page_file).rstrip("\n") + "\n\n"


def _write_rst_trace_report(cfg: Config, doc: dict[str, Any], src_dir: Path) -> str:
    # lobster-trace: SwRequirements.sw_req_trace_report_rst
    """Write the reStructuredText tracing report as a folder of pages.

    The LOBSTER start page is included below the configured title, the level pages get the page header.

    Args:
        cfg (Config): Project configuration.
        doc (dict[str, Any]): Document of type trace_report.
        src_dir (Path): Sphinx source folder.

    Returns:
        str: Page name for the table of contents.
    """
    _require(cfg.trace_report_rst / "index.rst", "run the trace step first")
    page_dir = src_dir / doc["id"]
    shutil.copytree(cfg.trace_report_rst, page_dir)

    for page_file in page_dir.glob("*.rst"):
        if page_file.name != "index.rst":
            page_file.write_text(_page_header(cfg, page_file) + page_file.read_text(encoding="utf-8"), encoding="utf-8")

    # The configured title replaces the LOBSTER title, a heading with over- and underline.
    start = (page_dir / "index.rst").read_text(encoding="utf-8")
    start = re.sub(r"\A(#+)\n.+\n\1\n+", "", start)
    include = page_dir / ("report" + INCLUDE_SUFFIX)
    include.write_text(start, encoding="utf-8")
    _write_generated(cfg, page_dir / "index.rst", doc, f".. include:: {include.name}\n")
    return cfg.page_name(doc)


def _write_converted_page(cfg: Config, doc: dict[str, Any], src_dir: Path) -> str:
    # lobster-trace: SwRequirements.sw_req_documents
    # lobster-trace: SwRequirements.sw_req_document_types
    """Write the page of a converted TRLC document.

    The converter output and its images are placed into a folder per document,
    next to the page including them, so relative image references resolve.

    Args:
        cfg (Config): Project configuration.
        doc (dict[str, Any]): Document of type trlc or test_results.
        src_dir (Path): Sphinx source folder.

    Returns:
        str: Page name for the table of contents.

    Raises:
        TrlcdocError: If the converted document is missing.
    """
    converted = cfg.convert_dir("rst", doc["id"])
    rst_files = sorted(converted.glob("*.rst"))
    if not rst_files:
        raise TrlcdocError(f"No converted files in {converted}, run the convert step first.")

    page_dir = src_dir / doc["id"]
    shutil.copytree(converted, page_dir)
    content = ""
    for rst_file in rst_files:
        include = (page_dir / rst_file.name).rename(page_dir / (rst_file.stem + INCLUDE_SUFFIX))
        content += f".. include:: {include.name}\n\n"
    _write_generated(cfg, page_dir / "index.rst", doc, content)
    return cfg.page_name(doc)


def _require(path: Path, hint: str) -> Path:
    # lobster-trace: SwRequirements.sw_req_document_types
    """Ensure an input file exists.

    Args:
        path (Path): The required file.
        hint (str): What to do if it is missing.

    Returns:
        Path: The file.

    Raises:
        TrlcdocError: If the file is missing.
    """
    if not path.exists():
        raise TrlcdocError(f"{path} not found, {hint}.")
    return path


def _write_index(cfg: Config, src_dir: Path, pages: list[str]) -> Path:
    # lobster-trace: SwRequirements.sw_req_html_site
    # lobster-trace: SwRequirements.sw_req_html_customization
    """Write the start page with the table of contents, or the project owned start page.

    Args:
        cfg (Config): Project configuration.
        src_dir (Path): Sphinx source folder.
        pages (list[str]): Page names in table of contents order.

    Returns:
        Path: The written index.rst.
    """
    index = src_dir / "index.rst"
    if "index" in cfg.html:
        _write_project_page(cfg, cfg.path(cfg.html["index"]), index)
    else:
        content = _heading(f"{_project_title(cfg)} documentation", "=")
        content += ".. toctree::\n   :maxdepth: 1\n   :caption: Contents:\n\n"
        content += "".join(f"   {page}\n" for page in pages)
        _write_generated(cfg, index, {}, content)
    return index


def _project_title(cfg: Config) -> str:
    # lobster-trace: SwRequirements.sw_req_project_settings
    """Get the project name, followed by the project version if configured.

    Args:
        cfg (Config): Project configuration.

    Returns:
        str: Name and version of the project.
    """
    return " ".join(filter(None, [cfg.project["name"], cfg.project.get("version")]))


def _write_sphinx_config(cfg: Config, src_dir: Path, copy_dirs: list[dict[str, str]]) -> Path:
    # lobster-trace: SwRequirements.sw_req_project_settings
    # lobster-trace: SwRequirements.sw_req_html_customization
    """Write the project settings read by the generic conf.py.

    Args:
        cfg (Config): Project configuration.
        src_dir (Path): Sphinx source folder.
        copy_dirs (list[dict[str, str]]): HTML folders to copy into the site.

    Returns:
        Path: The written settings file.
    """
    logo = cfg.project.get("logo")
    favicon = cfg.project.get("favicon")
    conf = cfg.html.get("conf")
    settings = {
        "project": cfg.project["name"],
        "version": cfg.project.get("version"),
        "author": cfg.project["author"],
        "copyright": cfg.project["copyright"],
        "logo": str(cfg.path(logo)) if logo else None,
        "favicon": str(cfg.path(favicon)) if favicon else None,
        "theme": cfg.html.get("theme", "haiku"),
        "extensions": _extensions(cfg),
        "extra_conf": cfg.html.get("extra_conf", {}),
        "conf": str(cfg.path(conf)) if conf else None,
        "copy_dirs": copy_dirs,
        "project_root": str(cfg.root),
        "links": _link_settings(cfg),
        # Configured titles of project pages, which override the first heading of the file.
        "page_titles": {
            doc["id"]: doc["title"] for doc in cfg.documents if doc["type"] in ("rst", "markdown") and "title" in doc
        },
    }
    settings_file = src_dir / "trlcdoc_settings.json"
    settings_file.write_text(json.dumps(settings, indent=4), encoding="utf-8")
    return settings_file


def _extensions(cfg: Config) -> list[str]:
    # lobster-trace: SwRequirements.sw_req_trace_report_rst
    """Get the configured Sphinx extensions, plus the ones the reStructuredText tracing report needs.

    Args:
        cfg (Config): Project configuration.

    Returns:
        list[str]: Sphinx extensions in addition to the default ones.
    """
    extensions = list(cfg.html.get("extensions", []))
    if cfg.trace_report_format == "rst" and any(doc["type"] == "trace_report" for doc in cfg.documents):
        extensions += [ext for ext in RST_TRACE_REPORT_EXTENSIONS if ext not in extensions]
    return extensions


def _link_settings(cfg: Config) -> dict[str, Any]:
    # lobster-trace: SwRequirements.sw_req_markdown_links
    """Collect the settings to resolve the relative links of Markdown pages against the project.

    Args:
        cfg (Config): Project configuration.

    Returns:
        dict[str, Any]: The project root, the Markdown file of each Markdown page, the site page
            of each project file and folder shown in the site, and the repository, the path of the
            project root in the repository and the commit for links to other project files
            (repository and commit None if not available).
    """
    pages: dict[str, str] = {}
    markdown_sources: dict[str, str] = {}
    for doc in cfg.documents:
        if "source" in doc and doc["type"] in ("trlc", "rst", "markdown", "text"):
            source = Path(os.path.relpath(cfg.path(doc["source"]), cfg.root)).as_posix()
            pages[source] = cfg.page_name(doc)
            if doc["type"] == "markdown":
                markdown_sources[doc["id"]] = source

    commit = git_output(["rev-parse", "HEAD"], cfg.root)
    repo_root = git_root(cfg.root)
    repository = None
    repository_path = "."
    if commit is not None and repo_root is not None:
        try:
            repository = repository_url(cfg.repository, cfg.root)
        except TrlcdocError:
            repository = None
        # The project may be a subfolder of the repository.
        repository_path = Path(os.path.relpath(cfg.root, repo_root)).as_posix()
    return {
        "root": str(cfg.root),
        "markdown_sources": markdown_sources,
        "pages": pages,
        "repository": repository,
        "repository_path": repository_path,
        "commit": commit,
    }


# Main *************************************************************************
