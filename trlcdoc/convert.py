"""Convert the TRLC documents with pyTRLCConverter.

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

from typing import Any, Dict, List

from .config import TRLC_DOCUMENT_TYPES, Config
from .util import TrlcdocError, clean_dir, find_tool, run

# Variables ********************************************************************

# Classes **********************************************************************

# Functions ********************************************************************


def convert_documents(cfg: Config, fmt: str) -> int:
    """Convert all TRLC documents into the given format.

    Args:
        cfg (Config): Project configuration.
        fmt (str): Output format, rst or markdown.

    Returns:
        int: Number of converted documents.
    """
    converted = 0
    for doc in cfg.documents:
        if doc["type"] in TRLC_DOCUMENT_TYPES:
            if fmt in doc["converter"]:
                convert_document(cfg, doc, fmt)
                converted += 1
            else:
                print(f"Skipping {doc['id']}: no {fmt} converter configured.")
    return converted


def convert_document(cfg: Config, doc: Dict[str, Any], fmt: str) -> List[str]:
    """Convert one TRLC document.

    Args:
        cfg (Config): Project configuration.
        doc (Dict[str, Any]): Document of type trlc or test_results.
        fmt (str): Output format, rst or markdown.

    Returns:
        List[str]: The executed command.

    Raises:
        TrlcdocError: If the test results are missing or the conversion fails.
    """
    sources = cfg.trlc_sources(doc)
    if doc["type"] == "test_results" and not any(cfg.test_results_dir.glob("*.trlc")):
        raise TrlcdocError(f"No test results in {cfg.test_results_dir}, run the tests step first.")

    out_dir = clean_dir(cfg.convert_dir(fmt, doc["id"]), cfg.output)
    print(f"Converting {doc['id']} -> {out_dir}")

    cmd = [find_tool("pyTRLCConverter")]
    cmd.extend(f"--source={source}" for source in sources)
    cmd.append(f"--include={cfg.trlc_model}")
    for source in cfg.included_sources(doc):
        cmd.extend([f"--include={source}", f"--exclude={source}"])
    cmd.extend([f"--out={out_dir}", f"--project={cfg.file_reference(doc['converter'][fmt])}"])
    if "translation" in doc:
        cmd.append(f"--translation={cfg.file_reference(doc['translation'])}")
    if "render_cfg" in doc:
        cmd.append(f"--renderCfg={cfg.file_reference(doc['render_cfg'])}")
    cmd.append(fmt)

    run(cmd, cfg.root)
    return cmd

# Main *************************************************************************
