"""Command line interface of trlcdoc."""

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

import argparse
import logging
from pathlib import Path

from . import __version__
from .config import Config, find_config, load_config
from .convert import convert_documents
from .html import build_html, show_html
from .log import TRACE, setup_logging
from .pages import check_toctrees
from .plantuml import provide_plantuml, stop_picoweb
from .testrun import run_tests
from .trace import build_trace_report
from .util import TrlcdocError, remove_output

# Variables ********************************************************************

# Steps in execution order. 'all' runs every step the configuration needs, except clean and show.
STEPS = ["clean", "check", "plantuml", "tests", "convert", "trace", "html", "show"]

COPYRIGHT = "Copyright (c) 2026 Norbert Schulz"
REPOSITORY = "https://github.com/nhjschulz/trlc-doc"
DESCRIPTION = """Build project documentation for TRLC/LOBSTER based projects: requirements, architecture,
tests, test results, tracing report and HTML site."""

# Exit code after Ctrl+C, as the shell reports a process ended by SIGINT.
EXIT_INTERRUPTED = 130

LOG = logging.getLogger(__name__)

# Classes **********************************************************************

# Functions ********************************************************************


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    # lobster-trace: SwRequirements.sw_req_cli
    # lobster-trace: SwRequirements.sw_req_cli_help
    # lobster-trace: SwRequirements.sw_req_cli_version
    # lobster-trace: SwRequirements.sw_req_steps
    # lobster-trace: SwRequirements.sw_req_config_file
    # lobster-trace: SwRequirements.sw_req_output_option
    # lobster-trace: SwRequirements.sw_req_verbose_output
    """Parse the command line arguments.

    Args:
        argv (list[str] | None): Arguments, defaults to sys.argv[1:].

    Returns:
        argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog="trlcdoc",
        description=DESCRIPTION,
        epilog=f"Version {__version__} - {COPYRIGHT} - GPL-3.0-or-later - see {REPOSITORY} for further information.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "steps", nargs="*", metavar="step", help=f"steps to run: {', '.join(STEPS)} or all (default: all)"
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}", help="show the trlcdoc version and exit"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="show decisions, tool details and timings, -vv also per-item details",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="project configuration (default: trlcdoc.yaml in the current folder or a parent)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="output folder, overrides paths.output of the configuration (relative to the current folder)",
    )
    parser.add_argument(
        "--online", action="store_true", help="link the tracing report to the repository instead of local files"
    )
    parser.add_argument(
        "--format",
        choices=["rst", "markdown"],
        default="rst",
        help="output format of the convert step (default: rst, needed for html)",
    )
    args = parser.parse_args(argv)

    args.steps = args.steps or ["all"]
    unknown = [step for step in args.steps if step not in (*STEPS, "all")]
    if unknown:
        parser.error(f"unknown step(s) {', '.join(unknown)}, choose from {', '.join(STEPS)}, all")
    return args


def _selected_steps(cfg: Config, requested: list[str]) -> list[str]:
    # lobster-trace: SwRequirements.sw_req_steps
    # lobster-trace: SwRequirements.sw_req_step_order
    # lobster-trace: SwRequirements.sw_req_verbose_output
    """Determine the steps to run, in execution order.

    Args:
        cfg (Config): Project configuration.
        requested (list[str]): Steps from the command line.

    Returns:
        list[str]: The steps to run.
    """
    selected = {step for step in STEPS if step in requested}
    if "all" in requested:
        selected.update(
            step
            for step in STEPS
            if step not in ("clean", "show")
            and not (step == "tests" and cfg.tests is None)
            and not (step == "trace" and cfg.trace is None)
        )
        if cfg.tests is None:
            LOG.debug("Step tests skipped: the configuration has no 'tests' section.")
        if cfg.trace is None:
            LOG.debug("Step trace skipped: the configuration has no 'trace' section.")
    # Converting and rendering need the PlantUML jar.
    if selected & {"convert", "html"} and "plantuml" not in selected:
        LOG.debug("Step plantuml added: convert and html need PlantUML.")
        selected.add("plantuml")
    steps = [step for step in STEPS if step in selected]
    LOG.debug("Steps: %s", ", ".join(steps))
    return steps


def _run_step(step: str, cfg: Config, args: argparse.Namespace) -> bool:
    # lobster-trace: SwRequirements.sw_req_steps
    # lobster-trace: SwRequirements.sw_req_clean
    # lobster-trace: SwRequirements.sw_req_show
    # lobster-trace: SwRequirements.sw_req_exit_code
    # lobster-trace: SwRequirements.sw_req_toctree_check
    """Run one step.

    Args:
        step (str): Step name.
        cfg (Config): Project configuration.
        args (argparse.Namespace): Command line arguments.

    Returns:
        bool: True if the step found no problems in the project content
        (failed tests, missing trace links, wrong table of contents). Build errors raise TrlcdocError.

    Raises:
        TrlcdocError: If the step cannot be completed.
    """
    ok = True
    LOG.info("\n===== trlcdoc %s =====", step)

    # _parse_args() accepts only the names in STEPS, so every step has a case.
    match step:
        case "clean":
            if remove_output(cfg.output):
                LOG.info("Removing %s", cfg.output)
            else:
                LOG.info("Nothing to clean in %s", cfg.output)

        case "check":
            LOG.info("Configuration %s is valid, output: %s", cfg.config_file, cfg.output)
            toctree_findings = check_toctrees(cfg)
            if toctree_findings:
                LOG.info("Table of contents of the project start page:")
                for finding in toctree_findings:
                    LOG.info("  %s", finding)
            ok = not toctree_findings

        case "plantuml":
            provide_plantuml(cfg)

        case "tests":
            if cfg.tests is None:
                raise TrlcdocError("The configuration has no 'tests' section.")
            ok = run_tests(cfg)

        case "convert":
            convert_documents(cfg, args.format)

        case "trace":
            if cfg.trace is None:
                raise TrlcdocError("The configuration has no 'trace' section.")
            ok = build_trace_report(cfg, args.online) == 0

        case "html":
            build_html(cfg)

        case "show":
            show_html(cfg)

    return ok


def main(argv: list[str] | None = None) -> int:
    # lobster-trace: SwRequirements.sw_req_cli
    # lobster-trace: SwRequirements.sw_req_config_validation
    # lobster-trace: SwRequirements.sw_req_exit_code
    # lobster-trace: SwRequirements.sw_req_output_option
    # lobster-trace: SwRequirements.sw_req_plantuml_picoweb
    # lobster-trace: SwRequirements.sw_req_verbose_output
    """Run the requested trlcdoc steps and stop the PlantUML picoweb server at the end.

    Args:
        argv (list[str] | None): Arguments, defaults to sys.argv[1:].

    Returns:
        int: 0 if all steps succeeded and the content has no findings,
        1 on findings (failed tests, missing trace links), 2 on build errors, 130 if interrupted.
    """
    args = _parse_args(argv)
    setup_logging(args.verbose)
    exit_code = 0
    try:
        config_file = args.config if args.config is not None else find_config(Path.cwd())
        cfg = load_config(config_file, args.output)
        LOG.debug("Configuration %s, project root %s, output %s", cfg.config_file, cfg.root, cfg.output)
        if LOG.isEnabledFor(TRACE):
            for doc in cfg.documents:
                LOG.log(TRACE, "Document %s: type %s, page %s", doc["id"], doc["type"], cfg.page_name(doc))
        findings: list[str] = []
        for step in _selected_steps(cfg, args.steps):
            if not _run_step(step, cfg, args):
                findings.append(step)
        if findings:
            LOG.info("\ntrlcdoc finished with findings in: %s", ", ".join(findings))
            exit_code = 1
        else:
            LOG.info("\ntrlcdoc finished successfully.")
    except TrlcdocError as err:
        LOG.error("\ntrlcdoc error: %s", err)
        exit_code = 2
    except KeyboardInterrupt:
        LOG.error("\ntrlcdoc interrupted")
        exit_code = EXIT_INTERRUPTED
    finally:
        stop_picoweb()
    return exit_code


# Main *************************************************************************
