"""Tests of the TRLC document conversion with pyTRLCConverter.

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

import shutil
from pathlib import Path

import pytest
from conftest import base_config, make_project, write_config

from trlcdoc.config import BUILTIN_DIR, load_config
from trlcdoc.convert import convert_document, convert_documents
from trlcdoc.testrun import run_tests
from trlcdoc.util import TrlcdocError

# Variables ********************************************************************

BUILTIN_CONVERTERS = ["req2rst.py", "req2markdown.py", "tc2rst.py", "tc2markdown.py",
                      "create_test_report_in_rst.py", "create_test_report_in_markdown.py", "translation.json"]

# Classes **********************************************************************

# Functions ********************************************************************


def _read_all(folder: Path, pattern: str) -> str:
    """Read all converted files of a folder, without the reStructuredText escape characters.

    Args:
        folder (Path): Conversion output folder.
        pattern (str): File name pattern.

    Returns:
        str: The concatenated file contents.
    """
    return "".join(file.read_text(encoding="utf-8") for file in sorted(folder.glob(pattern))).replace("\\", "")


@pytest.mark.parametrize("fmt, pattern", [("rst", "*.rst"), ("markdown", "*.md")])
def test_trlc_conversion(project: Path, fmt: str, pattern: str) -> None:
    """TRLC documents are converted per format, records of included documents only resolve references.

    Args:
        project (Path): Configuration file of the example project.
        fmt (str): Output format.
        pattern (str): Output file name pattern.
    """
    root = project.parent
    # A project converter, translation and render configuration instead of the built-in files.
    shutil.copytree(BUILTIN_DIR, root / "converters", ignore=shutil.ignore_patterns("__pycache__"))
    (root / "render.yaml").write_text("{}\n", encoding="utf-8")
    data = base_config()
    data["documents"][1].update({"converter": {"rst": "converters/req2rst.py",
                                               "markdown": "converters/req2markdown.py"},
                                 "translation": "converters/translation.json", "render_cfg": "render.yaml"})
    cfg = load_config(write_config(root, data))

    cmd = convert_document(cfg, cfg.document("sw_architecture"), fmt)
    assert f"--renderCfg={root / 'render.yaml'}" in cmd
    content = _read_all(cfg.convert_dir(fmt, "sw_architecture"), pattern)
    assert "sw_arch_hello" in content
    assert "The hello module returns the greeting." in content
    assert "The software shall greet." not in content


def test_builtin_converters(project: Path) -> None:
    """The built-in converters convert requirements, architecture, test cases and test results.

    Args:
        project (Path): Configuration file of the example project.
    """
    for name in BUILTIN_CONVERTERS:
        assert (BUILTIN_DIR / name).is_file()

    cfg = load_config(project)
    assert cfg.file_reference("builtin:req2rst.py") == BUILTIN_DIR / "req2rst.py"
    assert cfg.file_reference("converters/req2rst.py") == project.parent / "converters" / "req2rst.py"

    with pytest.raises(TrlcdocError, match="run the tests step first"):
        convert_documents(cfg, "rst")

    run_tests(cfg)
    for fmt, pattern in (("rst", "*.rst"), ("markdown", "*.md")):
        assert convert_documents(cfg, fmt) == 4
        assert "The software shall greet." in _read_all(cfg.convert_dir(fmt, "sw_requirements"), pattern)
        assert "sw_arch_hello" in _read_all(cfg.convert_dir(fmt, "sw_architecture"), pattern)
        assert "Call hello() and check the greeting." in _read_all(cfg.convert_dir(fmt, "sw_test"), pattern)
        assert "test_hello" in _read_all(cfg.convert_dir(fmt, "sw_test_results"), pattern)


def test_conversion_error(tmp_path: Path) -> None:
    """A TRLC error stops the conversion with a build error.

    Args:
        tmp_path (Path): pytest temporary folder.
    """
    cfg = load_config(make_project(tmp_path / "project"))
    arch = cfg.root / "trlc" / "swe-arch" / "swe-arch.trlc"
    arch.write_text(arch.read_text(encoding="utf-8").replace("sw_req_hello", "sw_req_unknown"), encoding="utf-8")
    with pytest.raises(TrlcdocError, match="Command failed"):
        convert_document(cfg, cfg.document("sw_architecture"), "rst")

    data = base_config()
    del data["documents"][0]["converter"]["markdown"]
    cfg = load_config(write_config(cfg.root, data))
    assert convert_document(cfg, cfg.document("sw_requirements"), "rst")
    assert "sw_requirements" not in [path.name for path in (cfg.output / "convert").glob("markdown/*")]

# Main *************************************************************************
