"""Generate the Sphinx sources from the configured documents and build the HTML site.

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
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List

from sphinx.cmd.build import build_main

from .config import PACKAGE_DIR, TRLC_DOCUMENT_TYPES, Config
from .util import TrlcdocError, clean_dir, git_output, repository_url, run

# Variables ********************************************************************

SPHINX_TEMPLATE_DIR = PACKAGE_DIR / "sphinx"

# Included converter output gets this suffix, so Sphinx does not treat it as a document.
INCLUDE_SUFFIX = ".inc"

# Underline character of the page titles. reStructuredText derives the heading level
# from the order the characters appear in a page. pyTRLCConverter underlines its
# levels with = # ~ ^ " + ', so '-' keeps the page title above the included content.
PAGE_TITLE_CHAR = "-"

# Placeholder in project owned pages, replaced by the relative path from the page to the project root.
PROJECT_ROOT_PLACEHOLDER = "{project_root}"

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

    pages: List[str] = []
    copy_dirs: List[Dict[str, str]] = []
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


def _write_page(cfg: Config, doc: Dict[str, Any], src_dir: Path, copy_dirs: List[Dict[str, str]]) -> str:
    # lobster-trace: SwRequirements.sw_req_documents
    # lobster-trace: SwRequirements.sw_req_document_types
    """Write the Sphinx page of a document.

    Args:
        cfg (Config): Project configuration.
        doc (Dict[str, Any]): Document configuration.
        src_dir (Path): Sphinx source folder.
        copy_dirs (List[Dict[str, str]]): Collects HTML folders to copy into the site.

    Returns:
        str: Page name for the table of contents.

    Raises:
        TrlcdocError: If an input of the document is missing.
    """
    doc_type = doc["type"]
    page = doc["id"]
    page_file = src_dir / f"{page}.rst"

    if doc_type in TRLC_DOCUMENT_TYPES:
        page = _write_converted_page(cfg, doc, src_dir)
    elif doc_type == "trace_report":
        _require(cfg.trace_report_html, "run the trace step first")
        _write_generated(cfg, page_file, doc, f".. raw:: html\n   :file: {cfg.trace_report_html.as_posix()}\n")
    elif doc_type in ("html", "command"):
        if doc_type == "command":
            run(doc["command"], cfg.root)
        html_source = cfg.html_source(doc)
        _require(html_source / "index.html", "generate it first")
        copy_dirs.append({"source": str(html_source), "destination": doc["id"]})
        _write_generated(cfg, page_file, doc, ".. raw:: html\n\n"
                         f'    <iframe src="{doc["id"]}/index.html" width="100%" height="1024px"></iframe>\n')
    elif doc_type == "text":
        source = _require(cfg.path(doc["source"]), "check the source path")
        # Sphinx treats absolute include paths as relative to the source folder.
        relative = Path(os.path.relpath(source, src_dir)).as_posix()
        _write_generated(cfg, page_file, doc, f".. literalinclude:: {relative}\n   :language: none\n")
    else:
        source = _require(cfg.path(doc["source"]), "check the source path")
        page_file = page_file.with_suffix(".md" if doc_type == "markdown" else ".rst")
        _write_project_page(cfg, source, page_file)

    return page


def _project_root_text(cfg: Config, text: str, page_file: Path) -> str:
    # lobster-trace: SwRequirements.sw_req_html_customization
    """Replace the project root placeholder by the relative path from a page to the project root.

    Args:
        cfg (Config): Project configuration.
        text (str): Page content with placeholders.
        page_file (Path): The page in the Sphinx source folder.

    Returns:
        str: The content with replaced placeholders.
    """
    return text.replace(PROJECT_ROOT_PLACEHOLDER, Path(os.path.relpath(cfg.root, page_file.parent)).as_posix())


def _write_project_page(cfg: Config, source: Path, page_file: Path) -> Path:
    # lobster-trace: SwRequirements.sw_req_document_types
    # lobster-trace: SwRequirements.sw_req_html_customization
    """Write a project owned page into the Sphinx source folder.

    Args:
        cfg (Config): Project configuration.
        source (Path): The project page.
        page_file (Path): The page in the Sphinx source folder.

    Returns:
        Path: The written page.
    """
    page_file.write_text(_project_root_text(cfg, source.read_text(encoding="utf-8"), page_file), encoding="utf-8")
    return page_file


def _write_generated(cfg: Config, page_file: Path, doc: Dict[str, Any], body: str) -> Path:
    # lobster-trace: SwRequirements.sw_req_documents
    # lobster-trace: SwRequirements.sw_req_html_customization
    """Write a generated page: the page header, the title of the document and the body.

    Args:
        cfg (Config): Project configuration.
        page_file (Path): The page in the Sphinx source folder.
        doc (Dict[str, Any]): Document configuration, a page without title gets no heading.
        body (str): Page content below the title.

    Returns:
        Path: The written page.
    """
    content = ""
    if "page_header" in cfg.html:
        header = cfg.path(cfg.html["page_header"]).read_text(encoding="utf-8")
        content = _project_root_text(cfg, header, page_file).rstrip("\n") + "\n\n"
    if "title" in doc:
        content += _heading(doc["title"])
    page_file.write_text(content + body, encoding="utf-8")
    return page_file


def _write_converted_page(cfg: Config, doc: Dict[str, Any], src_dir: Path) -> str:
    # lobster-trace: SwRequirements.sw_req_documents
    # lobster-trace: SwRequirements.sw_req_document_types
    """Write the page of a converted TRLC document.

    The converter output and its images are placed into a folder per document,
    next to the page including them, so relative image references resolve.

    Args:
        cfg (Config): Project configuration.
        doc (Dict[str, Any]): Document of type trlc or test_results.
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
    return f"{doc['id']}/index"


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


def _write_index(cfg: Config, src_dir: Path, pages: List[str]) -> Path:
    # lobster-trace: SwRequirements.sw_req_html_site
    # lobster-trace: SwRequirements.sw_req_html_customization
    """Write the start page with the table of contents, or the project owned start page.

    Args:
        cfg (Config): Project configuration.
        src_dir (Path): Sphinx source folder.
        pages (List[str]): Page names in table of contents order.

    Returns:
        Path: The written index.rst.
    """
    index = src_dir / "index.rst"
    if "index" in cfg.html:
        _write_project_page(cfg, cfg.path(cfg.html["index"]), index)
    else:
        content = _heading(f"{cfg.project['name']} documentation", "=")
        content += ".. toctree::\n   :maxdepth: 1\n   :caption: Contents:\n\n"
        content += "".join(f"   {page}\n" for page in pages)
        _write_generated(cfg, index, {}, content)
    return index


def _write_sphinx_config(cfg: Config, src_dir: Path, copy_dirs: List[Dict[str, str]]) -> Path:
    # lobster-trace: SwRequirements.sw_req_project_settings
    # lobster-trace: SwRequirements.sw_req_html_customization
    """Write the project settings read by the generic conf.py.

    Args:
        cfg (Config): Project configuration.
        src_dir (Path): Sphinx source folder.
        copy_dirs (List[Dict[str, str]]): HTML folders to copy into the site.

    Returns:
        Path: The written settings file.
    """
    logo = cfg.project.get("logo")
    favicon = cfg.project.get("favicon")
    conf = cfg.html.get("conf")
    settings = {
        "project": cfg.project["name"],
        "author": cfg.project["author"],
        "copyright": cfg.project["copyright"],
        "logo": str(cfg.path(logo)) if logo else None,
        "favicon": str(cfg.path(favicon)) if favicon else None,
        "theme": cfg.html.get("theme", "haiku"),
        "extensions": cfg.html.get("extensions", []),
        "extra_conf": cfg.html.get("extra_conf", {}),
        "conf": str(cfg.path(conf)) if conf else None,
        "copy_dirs": copy_dirs,
        "project_root": str(cfg.root),
        "links": _link_settings(cfg),
        # Configured titles of project pages, which override the first heading of the file.
        "page_titles": {doc["id"]: doc["title"] for doc in cfg.documents
                        if doc["type"] in ("rst", "markdown") and "title" in doc},
    }
    settings_file = src_dir / "trlcdoc_settings.json"
    settings_file.write_text(json.dumps(settings, indent=4), encoding="utf-8")
    return settings_file


def _link_settings(cfg: Config) -> Dict[str, Any]:
    # lobster-trace: SwRequirements.sw_req_markdown_links
    """Collect the settings to resolve the relative links of Markdown pages against the project.

    Args:
        cfg (Config): Project configuration.

    Returns:
        Dict[str, Any]: The project root, the Markdown file of each Markdown page, the site page
            of each project file and folder shown in the site, and the repository and commit for
            links to other project files (None if not available).
    """
    pages: Dict[str, str] = {}
    markdown_sources: Dict[str, str] = {}
    for doc in cfg.documents:
        if "source" in doc and doc["type"] in ("trlc", "rst", "markdown", "text"):
            source = Path(os.path.relpath(cfg.path(doc["source"]), cfg.root)).as_posix()
            pages[source] = f"{doc['id']}/index" if doc["type"] == "trlc" else doc["id"]
            if doc["type"] == "markdown":
                markdown_sources[doc["id"]] = source

    commit = git_output(["rev-parse", "HEAD"], cfg.root)
    repository = None
    if commit is not None:
        try:
            repository = repository_url(cfg.repository, cfg.root)
        except TrlcdocError:
            repository = None
    return {"root": str(cfg.root), "markdown_sources": markdown_sources, "pages": pages,
            "repository": repository, "commit": commit}

# Main *************************************************************************
