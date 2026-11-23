"""
Greeter main module
"""
# BSD 3-Clause License
#
# Copyright (c) 2025, NewTec GmbH
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Imports **********************************************************************

import argparse
import sys

from greeter.greet import greet

# Variables ********************************************************************

PROG_NAME = "greet"
PROG_DESC = "A python CLI tool to greet a user considering the time."
PROG_COPYRIGHT = "Copyright (c) 2025 NewTec GmbH"

# Functions ********************************************************************


def _create_args_parser() -> argparse.ArgumentParser:
    """
    Create parser for command line arguments.

    Returns:
        argparse.ArgumentParser:  The parser object for command line arguments.
    """
    parser = argparse.ArgumentParser(prog=PROG_NAME, description=PROG_DESC, epilog=PROG_COPYRIGHT)

    # lobster-trace: SwRequirements.sw_req_cli_user_name
    parser.add_argument(
        "name", type=str, nargs="?", default=None, help="Specify a user name to greet, defaults to login name if unset."
    )

    return parser


def main() -> int:
    # lobster-trace: SwRequirements.sw_req_cli
    """
    Main entry point.

    Returns:
        0 (int): success
    """
    # lobster-trace: SwRequirements.sw_req_cli_help
    # lobster-trace: SwRequirements.sw_req_cli_usage_error
    args = _create_args_parser().parse_args()

    # lobster-trace: SwRequirements.sw_req_cli_user_name
    name = args.name

    # lobster-trace: SwRequirements.sw_func_msg_output
    print(greet(name))

    return 0


# lobster-trace: SwRequirements.sw_req_cli
if __name__ == "__main__":
    sys.exit(main())
