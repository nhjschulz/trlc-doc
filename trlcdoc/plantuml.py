"""Provide the PlantUML jar, replacing the get_plantuml.sh/.bat scripts."""

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
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from .config import Config
from .util import TrlcdocError, find_graphviz, find_tool, prepare_output

# Variables ********************************************************************

DEFAULT_VERSION = "1.2024.8"
DOWNLOAD_URL = "https://github.com/plantuml/plantuml/releases/download/v{version}/plantuml-{version}.jar"

# Java option that keeps PlantUML from starting the graphical user interface support of the system.
JAVA_HEADLESS = "-Djava.awt.headless=true"

# Classes **********************************************************************

# Functions ********************************************************************


def provide_plantuml(cfg: Config) -> Path | str:
    # lobster-trace: SwRequirements.sw_req_plantuml
    # lobster-trace: SwRequirements.sw_req_external_tools
    """Locate or download plantuml.jar and export it in the PLANTUML environment variable.

    The PLANTUML environment variable, a jar or a PlantUML server URL, has precedence
    over the configured jar, which has precedence over a download of the configured version.
    A jar needs Java and Graphviz, which are checked before anything is downloaded.

    Args:
        cfg (Config): Project configuration.

    Returns:
        Path | str: The plantuml.jar file, or the PlantUML server URL.

    Raises:
        TrlcdocError: If the jar is missing and cannot be downloaded, or Java or Graphviz is missing.
    """
    env_jar = os.environ.get("PLANTUML", "")
    cfg_jar = cfg.plantuml.get("jar")
    version = cfg.plantuml.get("version", DEFAULT_VERSION)

    server = urlparse(env_jar).scheme in ("http", "https")
    if not server:
        find_tool("java", "A Java runtime is needed to run the PlantUML jar, or set PLANTUML to a PlantUML server URL.")
        find_graphviz("by PlantUML for all diagrams except sequence diagrams")

    if server:
        jar = env_jar
    elif env_jar and Path(env_jar).is_file():
        jar = Path(env_jar).resolve()
    elif cfg_jar:
        jar = cfg.path(cfg_jar)
    else:
        jar = cfg.plantuml_dir / f"plantuml-{version}.jar"
        if not jar.is_file():
            prepare_output(cfg.output)
            _download(DOWNLOAD_URL.format(version=version), jar)

    if isinstance(jar, Path) and not jar.is_file():
        raise TrlcdocError(f"PlantUML jar {jar} not found.")

    os.environ["PLANTUML"] = str(jar)
    print(f"PlantUML: {jar}")
    return jar


def java_headless_env() -> dict[str, str]:
    # lobster-trace: SwRequirements.sw_req_plantuml
    """Get the environment that makes Java run PlantUML headless in the converters.

    pyTRLCConverter starts PlantUML with the headless option only on Linux. Windows needs none,
    but on macOS each diagram would start the graphical user interface support of Java (Dock icon).
    Java reads additional options from JAVA_TOOL_OPTIONS. It reports them on stderr, which
    pyTRLCConverter logs as error, so they are only set on macOS.

    see also: https://github.com/NewTec-GmbH/pyTRLCConverter/issues/180

    Returns:
        dict[str, str]: Additional environment variables for the converters, empty except on macOS.
    """
    env: dict[str, str] = {}
    options = os.environ.get("JAVA_TOOL_OPTIONS", "")
    if sys.platform == "darwin" and JAVA_HEADLESS not in options.split():
        env["JAVA_TOOL_OPTIONS"] = f"{options} {JAVA_HEADLESS}".strip()
    return env


def _download(url: str, target: Path) -> Path:
    # lobster-trace: SwRequirements.sw_req_plantuml
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
