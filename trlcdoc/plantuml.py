"""Provide the PlantUML jar, replacing the get_plantuml.sh/.bat scripts.

    Author: Norbert Schulz (norbert.schulz@newtec.de)
"""

# *******************************************************************************
# Copyright (c) NewTec GmbH 2026   -   www.newtec.de
# *******************************************************************************

# Imports **********************************************************************

import os
import urllib.request
from pathlib import Path

from .config import Config
from .util import TrlcdocError, prepare_output

# Variables ********************************************************************

DEFAULT_VERSION = "1.2024.8"
DOWNLOAD_URL = "https://github.com/plantuml/plantuml/releases/download/v{version}/plantuml-{version}.jar"

# Classes **********************************************************************

# Functions ********************************************************************


def provide_plantuml(cfg: Config) -> Path:
    """Locate or download plantuml.jar and export it in the PLANTUML environment variable.

    The PLANTUML environment variable has precedence over the configured jar,
    which has precedence over a download of the configured version.

    Args:
        cfg (Config): Project configuration.

    Returns:
        Path: The plantuml.jar file.

    Raises:
        TrlcdocError: If the jar is missing and cannot be downloaded.
    """
    env_jar = os.environ.get("PLANTUML")
    cfg_jar = cfg.plantuml.get("jar")
    version = cfg.plantuml.get("version", DEFAULT_VERSION)

    if env_jar and Path(env_jar).is_file():
        jar = Path(env_jar).resolve()
    elif cfg_jar:
        jar = cfg.path(cfg_jar)
    else:
        jar = cfg.plantuml_dir / f"plantuml-{version}.jar"
        if not jar.is_file():
            prepare_output(cfg.output)
            _download(DOWNLOAD_URL.format(version=version), jar)

    if not jar.is_file():
        raise TrlcdocError(f"PlantUML jar {jar} not found.")

    os.environ["PLANTUML"] = str(jar)
    print(f"PlantUML: {jar}")
    return jar


def _download(url: str, target: Path) -> Path:
    """Download a file.

    Args:
        url (str): Source URL.
        target (Path): Destination file.

    Returns:
        Path: The downloaded file.

    Raises:
        TrlcdocError: If the download fails.
    """
    print(f"Downloading {url}")
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".part")
    try:
        urllib.request.urlretrieve(url, partial)
        partial.replace(target)
    except OSError as err:
        partial.unlink(missing_ok=True)
        raise TrlcdocError(f"Download of {url} failed: {err}") from err
    return target

# Main *************************************************************************
