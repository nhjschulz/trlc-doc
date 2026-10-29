"""Command line interface of trlcdoc.

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

import argparse
from pathlib import Path
from typing import List, Optional

from .config import Config, find_config, load_config
from .convert import convert_documents
from .html import build_html
from .plantuml import provide_plantuml
from .testrun import run_tests
from .trace import build_trace_report
from .util import TrlcdocError, remove_output

# Variables ********************************************************************

# Steps in execution order. 'all' runs every step the configuration needs, except clean.
STEPS = ["clean", "check", "plantuml", "tests", "convert", "trace", "html"]

# Classes **********************************************************************

# Functions ********************************************************************


def _parse_args(argv: Optional[List[str]]) -> argparse.Namespace:
    """Parse the command line arguments.

    Args:
        argv (Optional[List[str]]): Arguments, defaults to sys.argv[1:].

    Returns:
        argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog="trlcdoc",
        description="Build the TRLC based project documentation: requirements, architecture, "
                    "tests, test results, tracing report and HTML site.")
    parser.add_argument("steps", nargs="*", metavar="step",
                        help=f"steps to run: {', '.join(STEPS)} or all (default: all)")
    parser.add_argument("-c", "--config", type=Path,
                        help="project configuration (default: trlcdoc.yaml in the current folder or a parent)")
    parser.add_argument("--online", action="store_true",
                        help="link the tracing report to the repository instead of local files")
    parser.add_argument("--format", choices=["rst", "markdown"], default="rst",
                        help="output format of the convert step (default: rst, needed for html)")
    args = parser.parse_args(argv)

    args.steps = args.steps or ["all"]
    unknown = [step for step in args.steps if step not in (*STEPS, "all")]
    if unknown:
        parser.error(f"unknown step(s) {', '.join(unknown)}, choose from {', '.join(STEPS)}, all")
    return args


def _selected_steps(cfg: Config, requested: List[str]) -> List[str]:
    """Determine the steps to run, in execution order.

    Args:
        cfg (Config): Project configuration.
        requested (List[str]): Steps from the command line.

    Returns:
        List[str]: The steps to run.
    """
    selected = {step for step in STEPS if step in requested}
    if "all" in requested:
        selected.update(step for step in STEPS
                        if step != "clean"
                        and not (step == "tests" and cfg.tests is None)
                        and not (step == "trace" and cfg.trace is None))
    # Converting and rendering need the PlantUML jar.
    if selected & {"convert", "html"}:
        selected.add("plantuml")
    return [step for step in STEPS if step in selected]


def _run_step(step: str, cfg: Config, args: argparse.Namespace) -> bool:
    """Run one step.

    Args:
        step (str): Step name.
        cfg (Config): Project configuration.
        args (argparse.Namespace): Command line arguments.

    Returns:
        bool: True if the step found no problems in the project content
        (failed tests, missing trace links). Build errors raise TrlcdocError.

    Raises:
        TrlcdocError: If the step cannot be completed.
    """
    ok = True
    print(f"\n===== trlcdoc {step} =====", flush=True)
    if step == "clean":
        print(f"Removing {cfg.output}" if remove_output(cfg.output) else f"Nothing to clean in {cfg.output}")
    elif step == "check":
        print(f"Configuration {cfg.config_file} is valid, output: {cfg.output}")
    elif step == "plantuml":
        provide_plantuml(cfg)
    elif step == "tests":
        if cfg.tests is None:
            raise TrlcdocError("The configuration has no 'tests' section.")
        ok = run_tests(cfg)
    elif step == "convert":
        convert_documents(cfg, args.format)
    elif step == "trace":
        if cfg.trace is None:
            raise TrlcdocError("The configuration has no 'trace' section.")
        ok = build_trace_report(cfg, args.online) == 0
    else:
        build_html(cfg)
    return ok


def main(argv: Optional[List[str]] = None) -> int:
    """Run the requested trlcdoc steps.

    Args:
        argv (Optional[List[str]]): Arguments, defaults to sys.argv[1:].

    Returns:
        int: 0 if all steps succeeded and the content has no findings,
        1 on findings (failed tests, missing trace links), 2 on build errors.
    """
    args = _parse_args(argv)
    exit_code = 0
    try:
        cfg = load_config(args.config if args.config is not None else find_config(Path.cwd()))
        findings: List[str] = []
        for step in _selected_steps(cfg, args.steps):
            if not _run_step(step, cfg, args):
                findings.append(step)
        if findings:
            print(f"\ntrlcdoc finished with findings in: {', '.join(findings)}")
            exit_code = 1
        else:
            print("\ntrlcdoc finished successfully.")
    except TrlcdocError as err:
        print(f"\ntrlcdoc error: {err}")
        exit_code = 2
    return exit_code

# Main *************************************************************************
