"""Tests of the PlantUML provider.

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
import urllib.request
from pathlib import Path
from typing import List

import pytest
from conftest import base_config, write_config

from trlcdoc.config import load_config
from trlcdoc.plantuml import DEFAULT_VERSION, provide_plantuml
from trlcdoc.util import MARKER_FILE, TrlcdocError

# Variables ********************************************************************

# Classes **********************************************************************

# Functions ********************************************************************


def test_plantuml(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The PlantUML jar is taken from $PLANTUML, the configuration or downloaded, and exported in $PLANTUML.

    Args:
        project (Path): Configuration file of the example project.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.
    """
    root = project.parent
    downloads: List[str] = []

    def fake_download(url: str, target: str) -> None:
        downloads.append(url)
        Path(target).write_bytes(b"jar")

    monkeypatch.setattr(urllib.request, "urlretrieve", fake_download)

    # Download of the configured version into the output folder.
    monkeypatch.delenv("PLANTUML", raising=False)
    data = base_config()
    data["plantuml"] = {"version": "1.2023.1"}
    cfg = load_config(write_config(root, data))
    jar = provide_plantuml(cfg)
    assert jar == cfg.plantuml_dir / "plantuml-1.2023.1.jar"
    assert downloads == ["https://github.com/plantuml/plantuml/releases/download/v1.2023.1/plantuml-1.2023.1.jar"]
    assert os.environ["PLANTUML"] == str(jar)
    assert (cfg.output / MARKER_FILE).is_file()

    # An existing download is reused, the default version is used without configuration.
    monkeypatch.delenv("PLANTUML")
    assert provide_plantuml(cfg) == jar
    assert len(downloads) == 1
    monkeypatch.delenv("PLANTUML")
    cfg = load_config(write_config(root, base_config()))
    assert provide_plantuml(cfg).name == f"plantuml-{DEFAULT_VERSION}.jar"

    # A configured jar has precedence over the download.
    (root / "my-plantuml.jar").write_bytes(b"jar")
    data["plantuml"] = {"jar": "my-plantuml.jar"}
    monkeypatch.delenv("PLANTUML")
    assert provide_plantuml(load_config(write_config(root, data))) == root / "my-plantuml.jar"

    # The environment variable has precedence over the configured jar.
    env_jar = root / "env-plantuml.jar"
    env_jar.write_bytes(b"jar")
    monkeypatch.setenv("PLANTUML", str(env_jar))
    assert provide_plantuml(load_config(write_config(root, data))) == env_jar

    # A PlantUML server URL in the environment variable is kept, nothing is downloaded.
    monkeypatch.setenv("PLANTUML", "https://plantuml.example.com/plantuml")
    assert provide_plantuml(load_config(write_config(root, data))) == "https://plantuml.example.com/plantuml"
    assert os.environ["PLANTUML"] == "https://plantuml.example.com/plantuml"
    assert len(downloads) == 2

    # A configured jar that does not exist is an error.
    monkeypatch.delenv("PLANTUML")
    data["plantuml"] = {"jar": "missing.jar"}
    with pytest.raises(TrlcdocError, match="not found"):
        provide_plantuml(load_config(write_config(root, data)))

# Main *************************************************************************
