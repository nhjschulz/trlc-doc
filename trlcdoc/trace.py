"""Create the LOBSTER tracing report from the configured trace levels."""

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

import json
import os
import re
from pathlib import Path
from typing import Any

import yaml

from .config import Config
from .util import TrlcdocError, clean_dir, find_graphviz, find_tool, git_output, git_root, repository_url, run

# Variables ********************************************************************

# LOBSTER tracing status of items that are traced as required. Justified items
# (e.g. marked with "lobster-exclude") count as covered in LOBSTER, too.
TRACED_STATUS = ("OK", "JUSTIFIED")

# Classes **********************************************************************

# Functions ********************************************************************


def build_trace_report(cfg: Config, online: bool) -> int:
    # lobster-trace: SwRequirements.sw_req_trace_report
    # lobster-trace: SwRequirements.sw_req_trace_findings
    # lobster-trace: SwRequirements.sw_req_external_tools
    """Extract the trace data of all levels and create the HTML tracing report.

    Args:
        cfg (Config): Project configuration with a trace section.
        online (bool): Link the report to the repository instead of local files.

    Returns:
        int: Number of items that are not traced as required.

    Raises:
        TrlcdocError: If Graphviz is missing, which the LOBSTER reports need for the tracing policy diagram.
    """
    # Without dot, the LOBSTER reports only warn and leave out the tracing policy diagram.
    find_graphviz("for the tracing policy diagram of the tracing report")
    trace_dir = clean_dir(cfg.trace_dir, cfg.output)
    sources: dict[str, Path] = {}

    for level in cfg.trace["levels"]:
        out_file = trace_dir / f"{_slug(level['name'])}.lobster"
        match level.get("kind", "requirements"):
            case "requirements":
                _extract_trlc(cfg, level, out_file)
            case "implementation":
                _extract_code(cfg, level, out_file)
        sources[level["name"]] = out_file

    policy_file = _write_policy(cfg, sources, trace_dir / "lobster-report.conf")
    report_file = trace_dir / "report.lobster"
    run([find_tool("lobster-report"), "--lobster-config", str(policy_file), "--out", str(report_file)], cfg.root)

    if online:
        _make_online(cfg, report_file)

    if cfg.trace_report_format == "rst":
        _write_rst_report(cfg, report_file)
    else:
        command = [find_tool("lobster-html-report"), "--out", str(cfg.trace_report_html)]
        if cfg.trace.get("markdown", False):
            command.append("--render-md")
        run([*command, str(report_file)], cfg.root)
    return _print_summary(report_file)


def _write_rst_report(cfg: Config, report_file: Path) -> Path:
    # lobster-trace: SwRequirements.sw_req_trace_report_rst
    """Create the tracing report as reStructuredText pages for the HTML site.

    The local file references are made relative to the project root and prefixed with the path from a report page
    back to the project root, so they work from the site. Repository links of an online report are kept.

    Args:
        cfg (Config): Project configuration.
        report_file (Path): LOBSTER report.

    Returns:
        Path: Folder with the report pages.
    """
    with open(report_file, encoding="utf-8") as file:
        report = json.load(file)
    for level in report["levels"]:
        for item in level["items"]:
            location = item.get("location", {})
            if location.get("kind") == "file" and Path(location["file"]).is_relative_to(cfg.root):
                location["file"] = Path(location["file"]).relative_to(cfg.root).as_posix()
    rst_input = report_file.with_name("report_rst.lobster")
    rst_input.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # The pages end up in a folder per document: <html>/<id>/<level>.html
    source_root = Path(os.path.relpath(cfg.root, cfg.html_dir / "document")).as_posix()
    run(
        [
            find_tool("lobster-rst-report"),
            "--out-dir",
            str(cfg.trace_report_rst),
            "--source-root",
            source_root,
            str(rst_input),
        ],
        cfg.root,
    )
    return cfg.trace_report_rst


def _slug(name: str) -> str:
    # lobster-trace: SwRequirements.sw_req_trace_levels
    """Convert a level name into a file name.

    Args:
        name (str): Level name, e.g. 'SW Requirement'.

    Returns:
        str: File name stem, e.g. 'sw_requirement'.
    """
    return re.sub(r"\W+", "_", name).strip("_").lower()


def _extract_trlc(cfg: Config, level: dict[str, Any], out_file: Path) -> Path:
    # lobster-trace: SwRequirements.sw_req_trace_levels
    """Extract a TRLC requirements level with lobster-trlc.

    Args:
        cfg (Config): Project configuration.
        level (dict[str, Any]): Trace level of kind requirements.
        out_file (Path): LOBSTER output file.

    Returns:
        Path: The LOBSTER output file.
    """
    doc = cfg.document(level["document"])
    package, record_type = level["record_type"].split(".")
    inputs = [cfg.trlc_model, *cfg.trlc_sources(doc), *cfg.included_sources(doc)]
    rule: dict[str, Any] = {
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


def _extract_code(cfg: Config, level: dict[str, Any], out_file: Path) -> Path:
    # lobster-trace: SwRequirements.sw_req_trace_levels
    # lobster-trace: SwRequirements.sw_req_trace_doxygen
    """Extract an implementation level from source code.

    Args:
        cfg (Config): Project configuration.
        level (dict[str, Any]): Trace level of kind implementation.
        out_file (Path): LOBSTER output file.

    Returns:
        Path: The LOBSTER output file.
    """
    if level["extractor"] == "lobster-doxygen":
        return _extract_doxygen(cfg, level, out_file)
    sources = [str(cfg.path(source)) for source in level["sources"]]
    run([find_tool(level["extractor"]), "--out", str(out_file), *sources], cfg.root)
    return out_file


def _extract_doxygen(cfg: Config, level: dict[str, Any], out_file: Path) -> Path:
    # lobster-trace: SwRequirements.sw_req_trace_doxygen
    """Extract an implementation level from C/C++ sources with doxygen and lobster-doxygen.

    Doxygen runs in the folder of the configured Doxyfile, so its relative paths keep
    working. The Doxyfile is included unchanged and followed by settings that write
    only the XML output into the trace folder.

    Args:
        cfg (Config): Project configuration.
        level (dict[str, Any]): Trace level of kind implementation with a doxyfile.
        out_file (Path): LOBSTER output file.

    Returns:
        Path: The LOBSTER output file.
    """
    doxygen = find_tool(
        "doxygen",
        f"It is needed by the lobster-doxygen extractor of trace level '{level['name']}', see https://www.doxygen.nl.",
    )
    doxyfile = cfg.path(level["doxyfile"])
    doxygen_dir = out_file.with_name(f"{out_file.stem}-doxygen")
    settings = [
        f'@INCLUDE = "{doxyfile.as_posix()}"',
        f'OUTPUT_DIRECTORY = "{doxygen_dir.as_posix()}"',
        "GENERATE_XML = YES",
        "XML_OUTPUT = xml",
        "GENERATE_HTML = NO",
        "GENERATE_LATEX = NO",
        "GENERATE_RTF = NO",
        "GENERATE_MAN = NO",
        "GENERATE_DOCBOOK = NO",
    ]
    run([doxygen, "-"], doxyfile.parent, stdin="\n".join(settings) + "\n")
    run([find_tool("lobster-doxygen"), "-o", str(out_file), str(doxygen_dir / "xml")], cfg.root)
    return _absolute_locations(out_file, doxyfile.parent)


def _absolute_locations(lobster_file: Path, base: Path) -> Path:
    # lobster-trace: SwRequirements.sw_req_trace_doxygen
    """Make the relative file locations of a LOBSTER file absolute.

    Doxygen strips the folder it runs in from the file paths (STRIP_FROM_PATH), so lobster-doxygen
    writes them relative to the folder of the Doxyfile. The report links need them absolute, like
    the locations of the other levels.

    See also: https://github.com/NewTec-GmbH/lobster-doxygen/issues/68

    Args:
        lobster_file (Path): LOBSTER file, updated in place.
        base (Path): Folder the relative paths refer to.

    Returns:
        Path: The updated LOBSTER file.
    """
    data = json.loads(lobster_file.read_text(encoding="utf-8"))
    for item in data.get("data", []):
        location = item.get("location", {})
        if location.get("kind") == "file" and not Path(location["file"]).is_absolute():
            location["file"] = str((base / location["file"]).resolve())
    lobster_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return lobster_file


def _write_policy(cfg: Config, sources: dict[str, Path], policy_file: Path) -> Path:
    # lobster-trace: SwRequirements.sw_req_trace_levels
    """Write the lobster-report policy for the configured levels.

    Args:
        cfg (Config): Project configuration.
        sources (dict[str, Path]): LOBSTER file per level name.
        policy_file (Path): Policy file to write.

    Returns:
        Path: The written policy file.
    """
    blocks: list[str] = []
    for level in cfg.trace["levels"]:
        lines = [
            f'{level.get("kind", "requirements")} "{level["name"]}" {{',
            f'    source: "{sources[level["name"]].as_posix()}";',
        ]
        lines.extend(f'    trace to: "{target}";' for target in level.get("trace_to", []))
        lines.extend(f'    requires: "{target}";' for target in level.get("requires", []))
        lines.append("}")
        blocks.append("\n".join(lines))
    policy_file.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    return policy_file


def _make_online(cfg: Config, report_file: Path) -> Path:
    # lobster-trace: SwRequirements.sw_req_trace_report
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
    repo_root = git_root(cfg.root)
    if commit_id is None or repo_root is None:
        raise TrlcdocError("Online report needs a git repository ('git rev-parse HEAD' failed).")

    online_cfg = report_file.with_name("online_report_config.yaml")
    with open(online_cfg, "w", encoding="utf-8") as file:
        yaml.safe_dump(
            {
                "report": str(report_file),
                "commit_id": commit_id,
                "repo_root": str(repo_root),
                "base_url": repository_url(cfg.repository, cfg.root),
            },
            file,
        )

    online_report = report_file.with_suffix(".online")
    run([find_tool("lobster-online-report"), "--config", str(online_cfg), "--out", str(online_report)], cfg.root)
    online_report.replace(report_file)
    return report_file


def _print_summary(report_file: Path) -> int:
    # lobster-trace: SwRequirements.sw_req_trace_findings
    """Print the number of items per level that are not traced as required.

    Items that LOBSTER reports as justified (e.g. by a "lobster-exclude" comment)
    count as traced, like in the coverage of the LOBSTER report.

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
        missing = [item["tag"] for item in level["items"] if item.get("tracing_status") not in TRACED_STATUS]
        justified = sum(item.get("tracing_status") == "JUSTIFIED" for item in level["items"])
        total += len(missing)
        line = f"  {level['name']}: {len(level['items'])} items, {len(missing)} not traced"
        if justified:
            line += f", {justified} justified"
        print(line)
        for tag in missing:
            print(f"    {tag}")
    return total


# Main *************************************************************************
