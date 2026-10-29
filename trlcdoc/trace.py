"""Create the LOBSTER tracing report from the configured trace levels.

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

import json
import re
from pathlib import Path
from typing import Any, Dict, List

import yaml

from .config import Config
from .util import TrlcdocError, clean_dir, find_tool, git_output, run

# Variables ********************************************************************

# Classes **********************************************************************

# Functions ********************************************************************


def build_trace_report(cfg: Config, online: bool) -> int:
    """Extract the trace data of all levels and create the HTML tracing report.

    Args:
        cfg (Config): Project configuration with a trace section.
        online (bool): Link the report to the repository instead of local files.

    Returns:
        int: Number of items that are not traced as required.
    """
    trace_dir = clean_dir(cfg.trace_dir, cfg.output)
    sources: Dict[str, Path] = {}

    for level in cfg.trace["levels"]:
        out_file = trace_dir / f"{_slug(level['name'])}.lobster"
        if level.get("kind", "requirements") == "requirements":
            _extract_trlc(cfg, level, out_file)
        else:
            _extract_code(cfg, level, out_file)
        sources[level["name"]] = out_file

    policy_file = _write_policy(cfg, sources, trace_dir / "lobster-report.conf")
    report_file = trace_dir / "report.lobster"
    run([find_tool("lobster-report"), "--lobster-config", str(policy_file), "--out", str(report_file)], cfg.root)

    if online:
        _make_online(cfg, report_file)

    run([find_tool("lobster-html-report"), "--out", str(cfg.trace_report_html), str(report_file)], cfg.root)
    return _print_summary(report_file)


def _slug(name: str) -> str:
    """Convert a level name into a file name.

    Args:
        name (str): Level name, e.g. 'SW Requirement'.

    Returns:
        str: File name stem, e.g. 'sw_requirement'.
    """
    return re.sub(r"\W+", "_", name).strip("_").lower()


def _extract_trlc(cfg: Config, level: Dict[str, Any], out_file: Path) -> Path:
    """Extract a TRLC requirements level with lobster-trlc.

    Args:
        cfg (Config): Project configuration.
        level (Dict[str, Any]): Trace level of kind requirements.
        out_file (Path): LOBSTER output file.

    Returns:
        Path: The LOBSTER output file.
    """
    doc = cfg.document(level["document"])
    package, record_type = level["record_type"].split(".")
    inputs = [cfg.trlc_model, *cfg.trlc_sources(doc), *cfg.included_sources(doc)]
    rule: Dict[str, Any] = {
        "package": package,
        "record-type": record_type,
        "namespace": cfg.trace.get("namespace", "req"),
        "description-fields": level.get("description_fields", ["description"]),
    }
    if level.get("tags"):
        rule["tags"] = level["tags"]

    config_file = out_file.with_suffix(".yaml")
    with open(config_file, "w", encoding="utf-8") as file:
        yaml.safe_dump({"inputs": [str(path) for path in inputs], "conversion-rules": [rule]}, file, sort_keys=False)

    run([find_tool("lobster-trlc"), "--config", str(config_file), "--out", str(out_file)], cfg.root)
    return out_file


def _extract_code(cfg: Config, level: Dict[str, Any], out_file: Path) -> Path:
    """Extract an implementation level from source code.

    Args:
        cfg (Config): Project configuration.
        level (Dict[str, Any]): Trace level of kind implementation.
        out_file (Path): LOBSTER output file.

    Returns:
        Path: The LOBSTER output file.
    """
    sources = [str(cfg.path(source)) for source in level["sources"]]
    run([find_tool(level["extractor"]), "--out", str(out_file), *sources], cfg.root)
    return out_file


def _write_policy(cfg: Config, sources: Dict[str, Path], policy_file: Path) -> Path:
    """Write the lobster-report policy for the configured levels.

    Args:
        cfg (Config): Project configuration.
        sources (Dict[str, Path]): LOBSTER file per level name.
        policy_file (Path): Policy file to write.

    Returns:
        Path: The written policy file.
    """
    blocks: List[str] = []
    for level in cfg.trace["levels"]:
        lines = [f'{level.get("kind", "requirements")} "{level["name"]}" {{',
                 f'    source: "{sources[level["name"]].as_posix()}";']
        lines.extend(f'    trace to: "{target}";' for target in level.get("trace_to", []))
        lines.extend(f'    requires: "{target}";' for target in level.get("requires", []))
        lines.append("}")
        blocks.append("\n".join(lines))
    policy_file.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    return policy_file


def _repository_url(cfg: Config) -> str:
    """Get the repository URL for online links.

    Args:
        cfg (Config): Project configuration.

    Returns:
        str: HTTPS repository URL.

    Raises:
        TrlcdocError: If 'auto' is configured and git has no origin remote.
    """
    url = cfg.repository
    if url == "auto":
        url = git_output(["remote", "get-url", "origin"], cfg.root)
        if url is None:
            raise TrlcdocError("project.repository is 'auto', but 'git remote get-url origin' failed.")
        # git@github.com:owner/repo.git -> https://github.com/owner/repo.git
        url = re.sub(r"^git@([^:]+):", r"https://\1/", url)
    return url


def _make_online(cfg: Config, report_file: Path) -> Path:
    """Replace the local file references of the report by repository links.

    Args:
        cfg (Config): Project configuration.
        report_file (Path): LOBSTER report, updated in place.

    Returns:
        Path: The updated report file.

    Raises:
        TrlcdocError: If the commit id cannot be determined.
    """
    commit_id = git_output(["rev-parse", "HEAD"], cfg.root)
    if commit_id is None:
        raise TrlcdocError("Online report needs a git repository ('git rev-parse HEAD' failed).")

    online_cfg = report_file.with_name("online_report_config.yaml")
    with open(online_cfg, "w", encoding="utf-8") as file:
        yaml.safe_dump({"report": str(report_file), "commit_id": commit_id,
                        "repo_root": str(cfg.root), "base_url": _repository_url(cfg)}, file)

    online_report = report_file.with_suffix(".online")
    run([find_tool("lobster-online-report"), "--config", str(online_cfg), "--out", str(online_report)], cfg.root)
    online_report.replace(report_file)
    return report_file


def _print_summary(report_file: Path) -> int:
    """Print the number of items per level that are not traced as required.

    Args:
        report_file (Path): LOBSTER report.

    Returns:
        int: Total number of items that are not traced as required.
    """
    with open(report_file, encoding="utf-8") as file:
        report = json.load(file)

    total = 0
    print("Tracing:")
    for level in report["levels"]:
        missing = [item["tag"] for item in level["items"] if item.get("tracing_status") != "OK"]
        total += len(missing)
        print(f"  {level['name']}: {len(level['items'])} items, {len(missing)} not traced")
        for tag in missing:
            print(f"    {tag}")
    return total

# Main *************************************************************************
