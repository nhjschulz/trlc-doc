"""Tests of the PlantUML provider."""

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
import runpy
import shutil
import sys
import urllib.request
from pathlib import Path

import pytest
from conftest import base_config, write_config

from trlcdoc import convert, plantuml
from trlcdoc.config import load_config
from trlcdoc.html import SPHINX_TEMPLATE_DIR, _write_sphinx_config
from trlcdoc.plantuml import DEFAULT_VERSION, JAVA_HEADLESS, provide_plantuml
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
    downloads: list[str] = []

    def fake_download(url: str, target: str) -> None:
        downloads.append(url)
        Path(target).write_bytes(b"jar")

    monkeypatch.setattr(urllib.request, "urlretrieve", fake_download)
    # Java and Graphviz are checked by test_external_tools, here any host may run the test.
    monkeypatch.setattr(plantuml, "find_tool", lambda name, hint: name)
    monkeypatch.setattr(plantuml, "find_graphviz", lambda purpose: "dot")

    # Download of the configured version into the output folder. Setting PLANTUML before deleting it
    # lets monkeypatch restore it, provide_plantuml() exports the jar otherwise beyond this test.
    monkeypatch.setenv("PLANTUML", "")
    monkeypatch.delenv("PLANTUML")
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


def test_plantuml_headless(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """PlantUML runs headless: the Sphinx configuration of the html step passes the Java option on every system,
    the convert step passes it to pyTRLCConverter in JAVA_TOOL_OPTIONS on macOS, keeping options set by the user.

    Args:
        project (Path): Configuration file of the example project.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.
    """
    cfg = load_config(project)
    jar = cfg.root / "plantuml.jar"
    jar.write_bytes(b"jar")
    monkeypatch.setenv("PLANTUML", str(jar))

    # html step: the generated Sphinx configuration defines the PlantUML command.
    src_dir = cfg.root / "sphinx"
    src_dir.mkdir()
    shutil.copy(SPHINX_TEMPLATE_DIR / "conf.py", src_dir / "conf.py")
    _write_sphinx_config(cfg, src_dir, [])
    sphinx_conf = runpy.run_path(str(src_dir / "conf.py"))
    assert sphinx_conf["plantuml"] == ["java", JAVA_HEADLESS, "-jar", str(jar)]

    # convert step: the additional environment of the pyTRLCConverter call. The tool lookup is
    # skipped, as shutil.which doesn't work with a simulated platform.
    envs: list[dict[str, str] | None] = []
    monkeypatch.setattr(convert, "run", lambda cmd, cwd, env=None: envs.append(env) or 0)
    monkeypatch.setattr(convert, "find_tool", lambda name: name)
    doc = next(doc for doc in cfg.documents if doc["type"] == "trlc")
    monkeypatch.setenv("JAVA_TOOL_OPTIONS", "-Xmx1g")

    monkeypatch.setattr(sys, "platform", "darwin")
    convert.convert_document(cfg, doc, "rst")
    assert envs[-1] == {"JAVA_TOOL_OPTIONS": f"-Xmx1g {JAVA_HEADLESS}"}

    # The option is not added twice.
    monkeypatch.setenv("JAVA_TOOL_OPTIONS", JAVA_HEADLESS)
    convert.convert_document(cfg, doc, "rst")
    assert envs[-1] == {}

    # Linux gets the option from pyTRLCConverter, Windows needs none.
    for platform in ("linux", "win32"):
        monkeypatch.setattr(sys, "platform", platform)
        convert.convert_document(cfg, doc, "rst")
        assert envs[-1] == {}


# Main *************************************************************************
