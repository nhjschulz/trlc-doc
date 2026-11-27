"""Render a PlantUML diagram with a PlantUML server, as `plantuml -pipe` does with the jar.

sphinxcontrib-plantuml can only run a command: it passes the diagram on stdin and expects the image
on stdout. This module is that command for a PlantUML server. It is started for every diagram, so it
imports only what it needs.

Usage: python -m trlcdoc.plantuml_client <server URL> [PlantUML options, e.g. -pipe -tsvg]
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

import base64
import sys
import urllib.error
import urllib.request
import zlib

# Variables ********************************************************************

# PlantUML encodes the compressed diagram with its own base64 alphabet, see https://plantuml.com/text-encoding.
BASE64_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
PLANTUML_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"

# Seconds to wait for the image of one diagram.
RENDER_TIMEOUT = 60

# Classes **********************************************************************

# Functions ********************************************************************


def encode_diagram(text: str) -> str:
    # lobster-trace: SwRequirements.sw_req_plantuml
    """Encode a diagram for the URL of a PlantUML server.

    Args:
        text (str): PlantUML diagram source.

    Returns:
        str: The diagram, compressed with deflate and encoded with the PlantUML base64 alphabet.
    """
    # zlib adds a 2 byte header and a 4 byte checksum to the raw deflate data PlantUML expects.
    compressed = zlib.compress(text.encode("utf-8"))[2:-4]
    encoded = base64.b64encode(compressed).decode("ascii")
    return encoded.translate(str.maketrans(BASE64_CHARS, PLANTUML_CHARS)).rstrip("=")


def file_format(options: list[str]) -> str:
    # lobster-trace: SwRequirements.sw_req_plantuml
    """Get the image format from the PlantUML command line options.

    Args:
        options (list[str]): PlantUML options, e.g. ['-pipe', '-tsvg'] or ['-tlatex:nopreamble'].

    Returns:
        str: The format, png if no -t option is given, as with the jar.
    """
    fmt = "png"
    for option in options:
        if option.startswith("-t"):
            fmt = option[2:].split(":")[0]
    return fmt


def main(argv: list[str] | None = None) -> int:
    # lobster-trace: SwRequirements.sw_req_plantuml
    """Read a diagram from stdin, render it with the PlantUML server and write the image to stdout.

    Args:
        argv (list[str] | None): Server URL and PlantUML options, defaults to sys.argv[1:].

    Returns:
        int: 0 on success, 1 if the server reports a diagram error or cannot be reached.
    """
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("Usage: python -m trlcdoc.plantuml_client <server URL> [PlantUML options]", file=sys.stderr)
        return 1
    server_url = args[0].rstrip("/")
    text = sys.stdin.buffer.read().decode("utf-8")
    url = f"{server_url}/{file_format(args[1:])}/{encode_diagram(text)}"

    try:
        with urllib.request.urlopen(url, timeout=RENDER_TIMEOUT) as response:
            sys.stdout.buffer.write(response.read())
    except urllib.error.HTTPError as err:
        # A diagram error comes with an image that shows it, like the output of the jar.
        sys.stdout.buffer.write(err.read())
        print(f"PlantUML server {server_url}: {err.code} {err.reason}", file=sys.stderr)
        return 1
    except OSError as err:
        print(f"PlantUML server {server_url} not reachable: {err}", file=sys.stderr)
        return 1
    return 0


# Main *************************************************************************

if __name__ == "__main__":
    sys.exit(main())
