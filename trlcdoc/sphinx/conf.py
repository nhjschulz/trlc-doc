"""Generic Sphinx configuration of trlcdoc.

    All project specific values are read from trlcdoc_settings.json, which
    trlcdoc writes next to this file from the project configuration.

    Author: Norbert Schulz (norbert.schulz@newtec.de)
"""

# *******************************************************************************
# Copyright (c) NewTec GmbH 2026   -   www.newtec.de
# *******************************************************************************

# Imports **********************************************************************

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from sphinx.errors import ConfigError

# pylint: disable=invalid-name,redefined-builtin

# Variables ********************************************************************

_SETTINGS = json.loads((Path(__file__).parent / "trlcdoc_settings.json").read_text(encoding="utf-8"))

project = _SETTINGS["project"]
copyright = _SETTINGS["copyright"]
author = _SETTINGS["author"]

extensions = [
    'myst_parser',              # https://www.sphinx-doc.org/en/master/usage/markdown.html
    'sphinxcontrib.plantuml',   # https://github.com/sphinx-contrib/plantuml
    *_SETTINGS["extensions"]
]

templates_path = ['_templates']
exclude_patterns = []
source_suffix = ['.rst', '.md']

rst_prolog = """
.. include:: <s5defs.txt>

"""

myst_heading_anchors = 6

html_theme = _SETTINGS["theme"]
html_static_path = ['_static']
if html_theme == 'haiku':
    html_style = 'custom.css'
if _SETTINGS["logo"]:
    html_logo = _SETTINGS["logo"]
if _SETTINGS["favicon"]:
    html_favicon = _SETTINGS["favicon"]
html_last_updated_fmt = '%b %d, %Y'

# PlantUML is provided by trlcdoc in the PLANTUML environment variable,
# either as path to plantuml.jar or as server URL.
_PLANTUML_ENV = os.getenv('PLANTUML')
if _PLANTUML_ENV is None:
    raise ConfigError("The environment variable PLANTUML is not defined.")
if urlparse(_PLANTUML_ENV).scheme in ['http', 'https']:
    plantuml = [_PLANTUML_ENV]
elif os.path.isfile(_PLANTUML_ENV):
    plantuml = ['java', '-jar', _PLANTUML_ENV]
else:
    raise ConfigError(f"The environment variable PLANTUML points to a not existing file {_PLANTUML_ENV}.")

# Project specific additional configuration values.
globals().update(_SETTINGS["extra_conf"])

# Classes **********************************************************************

# Functions ********************************************************************


def setup(app: Any) -> None:
    """Register the trlcdoc build hooks.

    Args:
        app (Any): The Sphinx application.
    """
    app.connect('builder-inited', _copy_dirs)


def _copy_dirs(app: Any) -> None:
    """Copy the configured HTML folders, e.g. the coverage report, into the site.

    Args:
        app (Any): The Sphinx application.
    """
    for entry in _SETTINGS["copy_dirs"]:
        shutil.copytree(entry["source"], os.path.join(app.outdir, entry["destination"]), dirs_exist_ok=True)


def _git_commit_info() -> str:
    """Get the commit the documentation was built from.

    Returns:
        str: ' from commit <hash>', or an empty string outside of a git repository.
    """
    result = ""
    try:
        proc = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=_SETTINGS["project_root"],
                              capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            result = f" from commit {proc.stdout.strip()}"
    except OSError:
        result = ""
    return result

# Main *************************************************************************

html_last_updated_fmt += _git_commit_info()
