"""Placeholders of project owned pages and the check of their tables of contents.

Project owned pages (html.index, html.page_header, rst and markdown documents) are copied into
the generated Sphinx folder at different depths. Their placeholders are replaced per page:

- {project_root}: the relative path from the page to the project root
- {page:<id>}: the page name of a document, relative to the page
- {documents}: the page names of the documents in configuration order, one per line, without
  the documents a toctree of a project page lists explicitly

With a project start page, the project owns the table of contents. The check compares its
toctree entries with the page names of the documents, which depend on the document type and
the format of the tracing report.

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

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .config import PAGE_PLACEHOLDER, Config

# Variables ********************************************************************

# Placeholder for the relative path from a page to the project root.
PROJECT_ROOT_PLACEHOLDER = "{project_root}"

# Placeholder for the page names of all documents, alone on its line. Its indentation is kept
# for every page name, so it can be used as content of a toctree.
DOCUMENTS_PLACEHOLDER = re.compile(r"^([ \t]*)\{documents\}[ \t]*(\r?)$", re.MULTILINE)

# Start of a reStructuredText toctree directive, with its indentation.
RST_TOCTREE = re.compile(r"^([ \t]*)\.\.[ \t]+toctree::")

# Start of a MyST toctree directive in Markdown: a code fence of backticks or colons.
MD_TOCTREE = re.compile(r"^[ \t]*(`{3,}|:{3,})\{toctree\}")

# Toctree entry with explicit title: 'Title <page>'.
TITLED_ENTRY = re.compile(r"^.*<([^<>]+)>$")

# Source suffixes Sphinx removes from toctree entries.
SOURCE_SUFFIXES = (".rst", ".md")

# Classes **********************************************************************

# Functions ********************************************************************


def replace_placeholders(cfg: Config, text: str, page_file: Path) -> str:
    # lobster-trace: SwRequirements.sw_req_html_customization
    # lobster-trace: SwRequirements.sw_req_page_placeholders
    """Replace the placeholders of a project owned page.

    The page names of documents and the project root are relative to the page, so the same
    file works in pages at different depths of the Sphinx folder. Unknown document ids are
    left unchanged, the configuration check reports them.

    {documents} leaves out the documents that a toctree of a project page lists explicitly,
    by {page:<id>} or by page name, so a page can list a document in a toctree of its own,
    e.g. the license in a separate section, without listing it twice.

    Args:
        cfg (Config): Project configuration.
        text (str): Page content with placeholders.
        page_file (Path): The page in the Sphinx source folder.

    Returns:
        str: The content with replaced placeholders.
    """
    page_dir = page_file.parent
    pages = {doc["id"]: _relative_page(cfg, cfg.page_name(doc), page_dir) for doc in cfg.documents}

    if DOCUMENTS_PLACEHOLDER.search(text):
        explicit = _toctree_entries_of_project_pages(cfg, with_documents=False)
        listed = {entry for _, entry in explicit}
        unlisted = [pages[doc["id"]] for doc in cfg.documents if cfg.page_name(doc) not in listed]

        def documents(match: re.Match) -> str:
            indent, line_end = match.group(1), match.group(2)
            return "\n".join(f"{indent}{page}{line_end}" for page in unlisted)

        text = DOCUMENTS_PLACEHOLDER.sub(documents, text)

    text = PAGE_PLACEHOLDER.sub(lambda match: pages.get(match.group(1), match.group(0)), text)
    return text.replace(PROJECT_ROOT_PLACEHOLDER, Path(os.path.relpath(cfg.root, page_dir)).as_posix())


def _relative_page(cfg: Config, page: str, page_dir: Path) -> str:
    # lobster-trace: SwRequirements.sw_req_page_placeholders
    """Get the name of a page relative to the folder of the page referring to it.

    Args:
        cfg (Config): Project configuration.
        page (str): Page name relative to the Sphinx source folder.
        page_dir (Path): Folder of the referring page in the Sphinx source folder.

    Returns:
        str: The relative page name, as used in toctree entries and :doc: references.
    """
    return Path(os.path.relpath(cfg.sphinx_dir / page, page_dir)).as_posix()


def toctree_entries(text: str, markdown: bool = False) -> List[str]:
    # lobster-trace: SwRequirements.sw_req_toctree_check
    """Get the page names listed in the toctrees of a page.

    Entries with explicit title ('Title <page>') give their page, a leading '/' and a source
    suffix are removed. 'self', URLs and glob patterns are no page names and are skipped.

    Args:
        text (str): Content of a reStructuredText or Markdown (MyST) page.
        markdown (bool): The page is Markdown, with MyST toctree directives in code fences.

    Returns:
        List[str]: The page names in the order of the page.
    """
    raw_entries = _md_toctree_lines(text) if markdown else _rst_toctree_lines(text)
    entries = []
    for entry in raw_entries:
        match = TITLED_ENTRY.match(entry)
        page = match.group(1).strip() if match else entry
        page = page.lstrip("/").removeprefix("./")
        for suffix in SOURCE_SUFFIXES:
            page = page.removesuffix(suffix)
        if page != "self" and "://" not in page and not any(char in page for char in "*?["):
            entries.append(page)
    return entries


def _rst_toctree_lines(text: str) -> List[str]:
    # lobster-trace: SwRequirements.sw_req_toctree_check
    """Get the content lines of the reStructuredText toctree directives, without their options.

    Args:
        text (str): Content of a reStructuredText page.

    Returns:
        List[str]: The stripped entry lines.
    """
    lines: List[str] = []
    directive_indent: Optional[int] = None
    for line in text.splitlines():
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        # A non-empty line not indented deeper than the directive ends its content.
        if directive_indent is not None and stripped and indent <= directive_indent:
            directive_indent = None
        if directive_indent is not None:
            if stripped and not stripped.startswith(":"):
                lines.append(stripped)
        else:
            match = RST_TOCTREE.match(line)
            if match:
                directive_indent = len(match.group(1).expandtabs())
    return lines


def _md_toctree_lines(text: str) -> List[str]:
    # lobster-trace: SwRequirements.sw_req_toctree_check
    """Get the content lines of the MyST toctree directives of a Markdown page, without their options.

    Args:
        text (str): Content of a Markdown page.

    Returns:
        List[str]: The stripped entry lines.
    """
    lines: List[str] = []
    fence: Optional[str] = None
    in_yaml_options = False
    for line in text.splitlines():
        stripped = line.strip()
        if fence is None:
            match = MD_TOCTREE.match(line)
            fence = match.group(1) if match else None
        elif stripped.startswith(fence) and stripped.strip(fence[0]) == "":
            fence = None
        elif stripped == "---":
            in_yaml_options = not in_yaml_options
        elif stripped and not in_yaml_options and not stripped.startswith(":"):
            lines.append(stripped)
    return lines


def check_toctrees(cfg: Config) -> List[str]:
    # lobster-trace: SwRequirements.sw_req_toctree_check
    """Check the tables of contents of a project start page against the page names of the documents.

    Without html.index, trlcdoc generates the table of contents itself and there is nothing to
    check. Otherwise the toctrees of html.index and of the rst and markdown documents are read,
    after replacing their placeholders, and checked for

    - entries which are no page, with a hint if a document has a similar page name
    - documents whose page is in no toctree

    Entries in folders that belong to no document, e.g. pages of Sphinx extensions like
    sphinx-autoapi, cannot be checked and are accepted.

    Args:
        cfg (Config): Project configuration.

    Returns:
        List[str]: Findings, empty if the tables of contents list every document correctly.
    """
    findings: List[str] = []
    if "index" in cfg.html:
        pages = {cfg.page_name(doc): doc for doc in cfg.documents}
        listed: Set[str] = set()
        for where, entry in _toctree_entries_of_project_pages(cfg):
            finding, page = _check_entry(cfg, pages, where, entry)
            # A wrong entry naming a document lists it, its finding already tells the fix.
            listed.add(page)
            if finding is not None:
                findings.append(finding)
        findings.extend(f"html.index: document '{doc['id']}' (page '{page}') is not in any toctree. "
                        f"Add {{page:{doc['id']}}} to a toctree." for page, doc in pages.items() if page not in listed)
    return findings


def _toctree_entries_of_project_pages(cfg: Config, with_documents: bool = True) -> List[Tuple[str, str]]:
    # lobster-trace: SwRequirements.sw_req_toctree_check
    # lobster-trace: SwRequirements.sw_req_page_placeholders
    """Get the toctree entries of html.index and the rst and markdown documents.

    The project pages are placed at the top of the Sphinx folder, so their entries are page
    names relative to the Sphinx folder.

    Args:
        cfg (Config): Project configuration.
        with_documents (bool): Include the entries of {documents}, False gives only the
            explicitly listed entries.

    Returns:
        List[Tuple[str, str]]: Configuration location of the page and the entry.
    """
    project_pages = []
    if "index" in cfg.html:
        project_pages.append(("html.index", cfg.path(cfg.html["index"]), "index.rst", True))
    project_pages.extend((f"documents[{doc['id']}]", cfg.path(doc["source"]),
                          doc["id"] + (".md" if doc["type"] == "markdown" else ".rst"), doc.get("placeholders", True))
                         for doc in cfg.documents if doc["type"] in ("rst", "markdown"))
    result = []
    for where, source, name, placeholders in project_pages:
        if source.is_file():
            text = source.read_text(encoding="utf-8")
            if not with_documents:
                text = DOCUMENTS_PLACEHOLDER.sub("", text)
            if placeholders:
                text = replace_placeholders(cfg, text, cfg.sphinx_dir / name)
            result.extend((where, entry) for entry in toctree_entries(text, name.endswith(".md")))
    return result


def _check_entry(cfg: Config, pages: Dict[str, Dict[str, Any]], where: str,
                 entry: str) -> Tuple[Optional[str], str]:
    # lobster-trace: SwRequirements.sw_req_toctree_check
    """Check one toctree entry against the page names of the documents.

    Args:
        cfg (Config): Project configuration.
        pages (Dict[str, Dict[str, Any]]): Document per page name.
        where (str): Configuration location of the page with the toctree.
        entry (str): The toctree entry, a page name relative to the Sphinx folder.

    Returns:
        Tuple[Optional[str], str]: A finding, or None if the entry is a page of a document or cannot be
        checked, and the page the entry means: the page of a document with a similar name, else the entry.
    """
    folder = entry.split("/", 1)[0]
    documents = {doc["id"]: doc for doc in cfg.documents}
    similar = [page for page in (f"{entry}/index", entry.removesuffix("/index")) if page in pages]
    finding: Optional[str] = None
    page = entry
    if entry in pages:
        finding = None
    elif similar:
        page = similar[0]
        doc = pages[page]
        finding = (f"{where}: toctree entry '{entry}' is no page. Document '{doc['id']}' is the page "
                   f"'{similar[0]}' ({_page_reason(cfg, doc)}). Write {{page:{doc['id']}}} to use its page name.")
    elif "/" not in entry or (folder in documents and not _has_subpages(cfg, documents[folder])):
        finding = f"{where}: toctree entry '{entry}' is no page of a document."
    return finding, page


def _has_subpages(cfg: Config, doc: Dict[str, Any]) -> bool:
    # lobster-trace: SwRequirements.sw_req_toctree_check
    """Check whether the folder of a document contains further pages besides its index page.

    Args:
        cfg (Config): Project configuration.
        doc (Dict[str, Any]): Document configuration.

    Returns:
        bool: True for the reStructuredText tracing report, which has a page per trace level.
    """
    return doc["type"] == "trace_report" and cfg.trace_report_format == "rst"


def _page_reason(cfg: Config, doc: Dict[str, Any]) -> str:
    # lobster-trace: SwRequirements.sw_req_toctree_check
    """Explain the page name of a document by its type.

    Args:
        cfg (Config): Project configuration.
        doc (Dict[str, Any]): Document configuration.

    Returns:
        str: The settings that determine the page name.
    """
    reason = f"type {doc['type']}"
    if doc["type"] == "trace_report":
        reason += f", trace.report: {cfg.trace_report_format}"
    return reason

# Main *************************************************************************
