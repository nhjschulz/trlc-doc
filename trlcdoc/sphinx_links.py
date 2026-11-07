"""Sphinx extension resolving the relative links and images of Markdown pages against the project.

    A Markdown document is copied into the Sphinx source folder, so its relative
    links and images would point into that folder instead of the project. This
    extension resolves them against the location of the Markdown file in the project:

    - an image is taken from the project, Sphinx copies it into the site
    - a link to a file of a site page links to that page
    - a link to any other project file or folder links to the repository at the built commit
    - without a repository, such a link is shown as text with a warning

    Links to targets which do not exist in the project are left to MyST, which reports them.

    The settings are provided by trlcdoc in the configuration value 'trlcdoc_links'.

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
import posixpath
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from docutils import nodes
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.transforms import SphinxTransform
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util import logging

# Variables ********************************************************************

LOGGER = logging.getLogger(__name__)

# Name of the configuration value with the link settings written by trlcdoc.
CONFIG_NAME = "trlcdoc_links"

# Matches URLs with a scheme, e.g. https:, mailto: or data:.
URL_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")

# Classes **********************************************************************


class MarkdownImages(SphinxTransform):
    # lobster-trace: SwRequirements.sw_req_markdown_links
    """Take the relative images of Markdown pages from the project, while the page is read."""

    default_priority = 400

    def apply(self, **kwargs: Any) -> None:
        """Replace the image paths of a Markdown page by the paths of the project files.

        Args:
            **kwargs (Any): Unused transform arguments.
        """
        settings = self.config[CONFIG_NAME]
        source = settings.get("markdown_sources", {}).get(self.env.docname)
        if source is not None:
            page_dir = Path(self.env.srcdir) / posixpath.dirname(self.env.docname)
            for image in self.document.findall(nodes.image):
                project_path = _project_path(settings, source, image["uri"])
                project_file = Path(settings["root"]) / project_path if project_path is not None else None
                if project_file is not None and project_file.is_file() and not (page_dir / image["uri"]).exists():
                    image["uri"] = Path(os.path.relpath(project_file, page_dir)).as_posix()


class MarkdownLinks(SphinxPostTransform):
    # lobster-trace: SwRequirements.sw_req_markdown_links
    """Resolve the relative links of Markdown pages, which MyST could not resolve in the Sphinx source folder."""

    # Before the MyST reference resolver (9), which resolves the page links and reports the unresolved links.
    default_priority = 8

    def run(self, **kwargs: Any) -> None:
        """Replace the unresolved links to project files by page links, repository links or text.

        Args:
            **kwargs (Any): Unused transform arguments.
        """
        settings = self.config[CONFIG_NAME]
        source = settings.get("markdown_sources", {}).get(self.env.docname)
        if source is not None:
            for xref in list(self.document.findall(addnodes.pending_xref)):
                if xref.get("reftype") == "myst" and xref.get("refdomain") is None:
                    self._resolve(settings, source, xref)

    def _resolve(self, settings: Dict[str, Any], source: str, xref: addnodes.pending_xref) -> None:
        """Replace a link to a project file or folder, leave other links to MyST.

        Args:
            settings (Dict[str, Any]): The link settings.
            source (str): The Markdown file of the page, relative to the project root.
            xref (addnodes.pending_xref): The unresolved link.
        """
        target, _, anchor = xref["reftarget"].partition("#")
        project_path = _project_path(settings, source, target)
        if project_path is not None and (Path(settings["root"]) / project_path).exists():
            path = project_path.as_posix()
            page = settings.get("pages", {}).get(path)
            if page is not None:
                # A document link as MyST creates it for found documents, resolved by the MyST resolver.
                xref["refdomain"] = "doc"
                xref["reftarget"] = page
                xref["reftargetid"] = anchor or None
            elif settings.get("repository") and settings.get("commit"):
                kind = "tree" if (Path(settings["root"]) / project_path).is_dir() else "blob"
                fragment = f"#{anchor}" if anchor else ""
                uri = f"{settings['repository']}/{kind}/{settings['commit']}/{quote(path)}{fragment}"
                xref.replace_self(nodes.reference("", "", *_link_content(xref, target), internal=False,
                                                  refuri=uri))
            else:
                LOGGER.warning("Link to project file '%s' shown as text, no repository for the link.", path,
                               location=xref, type="trlcdoc", subtype="link")
                xref.replace_self(nodes.inline("", "", *_link_content(xref, target)))

# Functions ********************************************************************


def _link_content(xref: addnodes.pending_xref, target: str) -> List[nodes.Node]:
    # lobster-trace: SwRequirements.sw_req_markdown_links
    """Get the content of a link without the MyST cross-reference wrapper.

    Args:
        xref (addnodes.pending_xref): The link.
        target (str): The link target, the content of a link without text.

    Returns:
        List[nodes.Node]: The link text nodes.
    """
    content: List[nodes.Node] = [nodes.literal(target, target)]
    if xref.astext():
        content = []
        for child in xref.children:
            if isinstance(child, nodes.inline) and "xref" in child["classes"]:
                content.extend(child.children)
            else:
                content.append(child)
    return content


def _project_path(settings: Dict[str, Any], source: str, target: str) -> Optional[Path]:
    # lobster-trace: SwRequirements.sw_req_markdown_links
    """Resolve a relative link target of a Markdown file against its location in the project.

    Args:
        settings (Dict[str, Any]): The link settings.
        source (str): The Markdown file, relative to the project root.
        target (str): The link target, relative to the Markdown file.

    Returns:
        Optional[Path]: The target relative to the project root, or None for URLs, absolute
            paths and targets outside of the project.
    """
    result = None
    if target and not target.startswith("/") and URL_SCHEME.match(target) is None:
        path = posixpath.normpath(posixpath.join(posixpath.dirname(source), target))
        if path != ".." and not path.startswith("../") and settings.get("root"):
            result = Path(path)
    return result


def setup(app: Sphinx) -> Dict[str, Any]:
    # lobster-trace: SwRequirements.sw_req_markdown_links
    """Register the configuration value and the transforms.

    Args:
        app (Sphinx): The Sphinx application.

    Returns:
        Dict[str, Any]: The extension metadata.
    """
    app.add_config_value(CONFIG_NAME, {}, "env")
    app.add_transform(MarkdownImages)
    app.add_post_transform(MarkdownLinks)
    return {"parallel_read_safe": True, "parallel_write_safe": True}

# Main *************************************************************************
