"""
Greeter message provider implementation.
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

import getpass
from datetime import datetime
from typing import Optional

# Functions ********************************************************************

def _get_hour_of_day() -> int:
    # lobster-trace: SwRequirements.sw_func_daytime_greeting_selection
    """
    Provide the daytime hour based on the local system time.

    Returns:
        int: hour value 0..23
    """
    return datetime.now().hour

def greet(name : Optional[str]) -> str:
    """
    Greet the given user dependent on the current time.

    Args:
        name (Optional[str]): A name to greet or None to use the login name.

    Returns:
        str: A greeting message for the user.
    """

    if not name:
        # lobster-trace: SwRequirements.sw_req_cli_default_name
        name = getpass.getuser()

    # Get the current hour
    current_hour = _get_hour_of_day()

    # Determine the greeting message based on the current hour.
    if 5 <= current_hour < 11:
        # lobster-trace: SwRequirements.sw_func_morning_time_greeting
        greeting = f"Good morning {name}!"
    elif 11 <= current_hour < 13:
        # lobster-trace: SwRequirements.sw_func_midday_time_greeting
        greeting = f"Good midday {name}!"
    elif 13 <= current_hour < 19:
        # lobster-trace: SwRequirements.sw_func_afternoon_time_greeting
        greeting = f"Good afternoon {name}!"
    else:
        # lobster-trace: SwRequirements.sw_func_night_time_greeting
        greeting = f"Good night {name}!"

    return greeting
