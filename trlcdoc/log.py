"""Console output of trlcdoc: logging setup, verbosity levels and redaction of secrets.

All trlcdoc modules log with logging.getLogger(__name__), below the 'trlcdoc' logger configured here.
INFO is the default output, DEBUG (-v) adds decisions and tool details, TRACE (-vv) adds per-item details.
"""

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

import logging
import re
import shlex
import subprocess
import sys
from urllib.parse import urlsplit, urlunsplit

# Variables ********************************************************************

# Level below DEBUG for per-item details, e.g. every rewritten link.
TRACE = 5
logging.addLevelName(TRACE, "TRACE")

# Logger of the trlcdoc package, parent of the module loggers.
LOGGER_NAME = "trlcdoc"

# Log level per number of -v options.
VERBOSITY_LEVELS = [logging.INFO, logging.DEBUG, TRACE]

# Environment variables whose values are never logged.
SECRET_NAME = re.compile(r"TOKEN|SECRET|PASSWORD|KEY|CREDENTIAL", re.IGNORECASE)
REDACTED = "***"

# Classes **********************************************************************


class ConsoleHandler(logging.Handler):
    # lobster-trace: SwRequirements.sw_req_verbose_output
    """Write INFO and below to stdout, WARNING and above to stderr.

    The stream is looked up for every message instead of once, so output redirected later,
    e.g. by pytest, receives the messages. Every message is flushed, so it appears before
    the output of a tool started next.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Write a message to its stream.

        Args:
            record (logging.LogRecord): The message.
        """
        try:
            stream = sys.stderr if record.levelno >= logging.WARNING else sys.stdout
            stream.write(self.format(record) + "\n")
            stream.flush()
        except Exception:
            # The logging module's way to report a failing handler, as logging.StreamHandler does.
            self.handleError(record)


class LevelFormatter(logging.Formatter):
    # lobster-trace: SwRequirements.sw_req_verbose_output
    """Format a message unchanged, and prefix debug and trace messages with their level name.

    The default output keeps its plain text, the verbose lines are recognizable.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format a message.

        Args:
            record (logging.LogRecord): The message.

        Returns:
            str: The message, with 'DEBUG: ' or 'TRACE: ' in front for verbose messages.
        """
        message = record.getMessage()
        if record.levelno < logging.INFO:
            message = f"{record.levelname}: {message}"
        return message


# Functions ********************************************************************


def setup_logging(verbosity: int = 0) -> None:
    # lobster-trace: SwRequirements.sw_req_verbose_output
    """Configure the trlcdoc logger for the console.

    It can be called again, e.g. for each run in the tests: the handler is replaced, not added.

    Args:
        verbosity (int): Number of -v options: 0 for the default output, 1 for DEBUG, 2 or more for TRACE.
    """
    logger = logging.getLogger(LOGGER_NAME)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
    handler = ConsoleHandler()
    handler.setFormatter(LevelFormatter())
    logger.addHandler(handler)
    logger.setLevel(VERBOSITY_LEVELS[min(verbosity, len(VERBOSITY_LEVELS) - 1)])
    # Applications using the root logger, e.g. Sphinx, would print the messages a second time.
    logger.propagate = False


def redact_url(text: str) -> str:
    # lobster-trace: SwRequirements.sw_req_verbose_output
    """Replace the user and password of a URL, e.g. of a PlantUML server.

    Args:
        text (str): A URL or any other text.

    Returns:
        str: The text, with ``***`` instead of the user info if it is a URL with one.
    """
    parts = urlsplit(text)
    if "@" not in parts.netloc:
        return text
    host = parts.netloc.rsplit("@", 1)[1]
    return urlunsplit(parts._replace(netloc=f"{REDACTED}@{host}"))


def redact_env(env: dict[str, str]) -> dict[str, str]:
    # lobster-trace: SwRequirements.sw_req_verbose_output
    """Replace the secrets of environment variables.

    Args:
        env (dict[str, str]): Environment variables.

    Returns:
        dict[str, str]: A copy with ``***`` as value of variables named like a secret, and URLs without user info.
    """
    redacted = {}
    for name, value in env.items():
        redacted[name] = REDACTED if SECRET_NAME.search(name) else redact_url(value)
    return redacted


def command_line(cmd: list[str]) -> str:
    # lobster-trace: SwRequirements.sw_req_verbose_output
    """Format a command so it can be pasted into a shell of the system.

    Args:
        cmd (list[str]): Command and its arguments.

    Returns:
        str: The command line, quoted for cmd.exe on Windows and for a POSIX shell elsewhere.
    """
    if sys.platform == "win32":
        return subprocess.list2cmdline(cmd)
    return shlex.join(cmd)


# Main *************************************************************************

# Functions called without the command line interface, e.g. by the tests, log with the default output.
setup_logging()
