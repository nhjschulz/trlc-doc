"""Tests of the output folder handling: creation, clean step and delete protection.

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

from pathlib import Path

import pytest
from conftest import base_config, write_config

from trlcdoc import cli
from trlcdoc.util import MARKER_FILE, TrlcdocError, clean_dir, prepare_output, remove_output

# Variables ********************************************************************

# Classes **********************************************************************

# Functions ********************************************************************


def test_output_marker(tmp_path: Path) -> None:
    """A missing or empty output folder is created and marked as trlcdoc output.

    Args:
        tmp_path (Path): pytest temporary folder.
    """
    missing = tmp_path / "missing"
    assert clean_dir(missing / "html", missing) == missing / "html"
    assert (missing / MARKER_FILE).is_file()
    assert (missing / "html").is_dir()

    empty = tmp_path / "empty"
    empty.mkdir()
    prepare_output(empty)
    assert (empty / MARKER_FILE).is_file()


def test_clean(project: Path, capsys: pytest.CaptureFixture) -> None:
    """The clean step removes the output folder with all build artifacts.

    Args:
        project (Path): Configuration file of the example project.
        capsys (pytest.CaptureFixture): pytest output capture.
    """
    output = project.parent / "build" / "trlcdoc"
    (clean_dir(output / "html", output) / "index.html").write_text("site", encoding="utf-8")
    clean_dir(output / "trace", output)

    assert cli.main(["-c", str(project), "clean"]) == 0
    assert "Removing" in capsys.readouterr().out
    assert not output.exists()
    assert (project.parent / "trlc").is_dir()

    assert cli.main(["-c", str(project), "clean"]) == 0
    assert "Nothing to clean" in capsys.readouterr().out
    assert remove_output(output) is False


def test_delete_protection(project: Path, capsys: pytest.CaptureFixture) -> None:
    """Folders not created by trlcdoc are never deleted.

    Args:
        project (Path): Configuration file of the example project.
        capsys (pytest.CaptureFixture): pytest output capture.
    """
    root = project.parent
    data = base_config()
    data["paths"]["output"] = "tests"
    write_config(root, data)
    source = root / "tests" / "test_hello.py"
    content = source.read_text(encoding="utf-8")

    for step in ("clean", "tests", "convert"):
        assert cli.main(["-c", str(project), step]) == 2
        assert "is not a trlcdoc output folder" in capsys.readouterr().out
        assert source.read_text(encoding="utf-8") == content
        assert not (root / "tests" / MARKER_FILE).exists()

    output = root / "build"
    with pytest.raises(TrlcdocError, match="is not inside the output folder"):
        clean_dir(root / "trlc", output)
    with pytest.raises(TrlcdocError, match="is not inside the output folder"):
        clean_dir(output, output)
    assert (root / "trlc" / "model").is_dir()

# Main *************************************************************************
