"""Provide the PlantUML jar, replacing the get_plantuml.sh/.bat scripts."""

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

import atexit
import os
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .config import Config
from .plantuml_client import encode_diagram
from .util import TrlcdocError, find_graphviz, find_tool, prepare_output

# Variables ********************************************************************

DEFAULT_VERSION = "1.2024.8"
DOWNLOAD_URL = "https://github.com/plantuml/plantuml/releases/download/v{version}/plantuml-{version}.jar"

# Java option that keeps PlantUML from starting the graphical user interface support of the system.
JAVA_HEADLESS = "-Djava.awt.headless=true"

# The picoweb server listens on this address only, so it cannot be reached from the network.
PICOWEB_HOST = "127.0.0.1"
# Seconds until the picoweb server must render its first diagram: Java start and PlantUML initialization.
PICOWEB_START_TIMEOUT = 30.0
# Seconds between two checks whether the picoweb server answers.
PICOWEB_POLL_INTERVAL = 0.1
# Seconds the picoweb server gets to stop before it is killed.
PICOWEB_STOP_TIMEOUT = 5.0
# Diagram that checks that the picoweb server renders. A sequence diagram doesn't need Graphviz.
PICOWEB_PROBE_DIAGRAM = "@startuml\nA -> B\n@enduml\n"

# Environment variables set while the picoweb server runs. The proxy exceptions keep requests
# to the local server away from a proxy configured for the internet.
PICOWEB_ENV_NAMES = ("PLANTUML", "NO_PROXY", "no_proxy")

# Classes **********************************************************************


@dataclass
class PicowebServer:
    # lobster-trace: SwRequirements.sw_req_plantuml_picoweb
    """The running PlantUML picoweb server and what to restore when it stops."""

    process: subprocess.Popen
    """The Java process of the server."""
    url: str
    """Server URL for the PLANTUML environment variable."""
    saved_env: dict[str, str | None] = field(default_factory=dict)
    """Values of PICOWEB_ENV_NAMES before the server started, None if unset."""
    saved_sigterm: Any = None
    """The SIGTERM handler before the server started, None if it was not replaced."""


# The picoweb server of this trlcdoc run: empty if none runs, never more than one entry.
_running_picoweb: list[PicowebServer] = []

# Functions ********************************************************************


def provide_plantuml(cfg: Config) -> Path | str:
    # lobster-trace: SwRequirements.sw_req_plantuml
    # lobster-trace: SwRequirements.sw_req_external_tools
    """Locate or download plantuml.jar and export it in the PLANTUML environment variable.

    The PLANTUML environment variable, a jar or a PlantUML server URL, has precedence
    over the configured jar, which has precedence over a download of the configured version.
    A jar needs Java and Graphviz, which are checked before anything is downloaded.

    With plantuml.picoweb (default), a jar is started once as local picoweb server, and its URL
    is exported instead of the jar. If the server doesn't start, the jar is exported.

    Args:
        cfg (Config): Project configuration.

    Returns:
        Path | str: The plantuml.jar file, or the PlantUML server URL.

    Raises:
        TrlcdocError: If the jar is missing and cannot be downloaded, or Java or Graphviz is missing.
    """
    env_jar = os.environ.get("PLANTUML", "")
    cfg_jar = cfg.plantuml.get("jar")
    version = cfg.plantuml.get("version", DEFAULT_VERSION)

    server = urlparse(env_jar).scheme in ("http", "https")
    if not server:
        find_tool("java", "A Java runtime is needed to run the PlantUML jar, or set PLANTUML to a PlantUML server URL.")
        find_graphviz("by PlantUML for all diagrams except sequence diagrams")

    if server:
        jar = env_jar
    elif env_jar and Path(env_jar).is_file():
        jar = Path(env_jar).resolve()
    elif cfg_jar:
        jar = cfg.path(cfg_jar)
    else:
        jar = cfg.plantuml_dir / f"plantuml-{version}.jar"
        if not jar.is_file():
            prepare_output(cfg.output)
            _download(DOWNLOAD_URL.format(version=version), jar)

    if isinstance(jar, Path) and not jar.is_file():
        raise TrlcdocError(f"PlantUML jar {jar} not found.")

    os.environ["PLANTUML"] = str(jar)
    print(f"PlantUML: {jar}")
    if isinstance(jar, Path) and cfg.plantuml.get("picoweb", True):
        url = start_picoweb(cfg, jar)
        if url is not None:
            return url
    return jar


def start_picoweb(cfg: Config, jar: Path) -> str | None:
    # lobster-trace: SwRequirements.sw_req_plantuml_picoweb
    """Start the PlantUML jar as local picoweb server and export its URL in the PLANTUML environment variable.

    The server runs until stop_picoweb(), which trlcdoc calls when it finishes, and at the latest
    when Python exits. If the server doesn't render a diagram within PICOWEB_START_TIMEOUT seconds,
    it is stopped and a warning is printed: the jar renders each diagram instead.

    Args:
        cfg (Config): Project configuration.
        jar (Path): The plantuml.jar file.

    Returns:
        str | None: The server URL, or None if the server is not available.
    """
    stop_picoweb()

    port = _free_port()
    url = f"http://{PICOWEB_HOST}:{port}/plantuml"
    cmd = [find_tool("java"), JAVA_HEADLESS, "-jar", str(jar), f"-picoweb:{port}:{PICOWEB_HOST}"]
    log_file = cfg.plantuml_dir / "picoweb.log"
    prepare_output(cfg.output)
    cfg.plantuml_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting PlantUML picoweb server {url}")
    with log_file.open("w", encoding="utf-8") as log:
        try:
            # The project root is the folder of relative !include paths, as the server gets no file name.
            process = subprocess.Popen(
                cmd, cwd=cfg.root, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT
            )
        except OSError as err:
            _warn_no_picoweb(str(err))
            return None

    server = PicowebServer(process, url, {name: os.environ.get(name) for name in PICOWEB_ENV_NAMES})
    _running_picoweb.append(server)
    atexit.register(stop_picoweb)
    server.saved_sigterm = _exit_on_sigterm()

    if not _wait_for_picoweb(process, url):
        stop_picoweb()
        output = log_file.read_text(encoding="utf-8", errors="replace").strip()
        _warn_no_picoweb(f"no diagram rendered within {PICOWEB_START_TIMEOUT:g} s. {output}".strip())
        return None

    os.environ["PLANTUML"] = url
    for name in ("NO_PROXY", "no_proxy"):
        os.environ[name] = ",".join(filter(None, [os.environ.get(name), PICOWEB_HOST]))
    return url


def stop_picoweb() -> None:
    # lobster-trace: SwRequirements.sw_req_plantuml_picoweb
    """Stop the picoweb server, if one runs, and restore the environment from before its start.

    The server gets PICOWEB_STOP_TIMEOUT seconds to stop, then it is killed.
    """
    if not _running_picoweb:
        return
    server = _running_picoweb.pop()
    atexit.unregister(stop_picoweb)

    if server.process.poll() is None:
        server.process.terminate()
        try:
            server.process.wait(PICOWEB_STOP_TIMEOUT)
        except subprocess.TimeoutExpired:
            server.process.kill()
            server.process.wait()

    for name, value in server.saved_env.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
    if server.saved_sigterm is not None:
        signal.signal(signal.SIGTERM, server.saved_sigterm)


def _free_port() -> int:
    # lobster-trace: SwRequirements.sw_req_plantuml_picoweb
    """Get a TCP port on PICOWEB_HOST that is free at the moment.

    Returns:
        int: The port number chosen by the system.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((PICOWEB_HOST, 0))
        return sock.getsockname()[1]


def _wait_for_picoweb(process: subprocess.Popen, url: str) -> bool:
    # lobster-trace: SwRequirements.sw_req_plantuml_picoweb
    """Wait until the picoweb server renders a diagram.

    Args:
        process (subprocess.Popen): The Java process of the server.
        url (str): Server URL.

    Returns:
        bool: True if the server rendered the probe diagram, False if it ended or the time is up.
    """
    probe_url = f"{url}/svg/{encode_diagram(PICOWEB_PROBE_DIAGRAM)}"
    # The probe goes directly to the local server, even if a proxy is configured.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    deadline = time.monotonic() + PICOWEB_START_TIMEOUT
    while time.monotonic() < deadline and process.poll() is None:
        try:
            with opener.open(probe_url, timeout=max(deadline - time.monotonic(), PICOWEB_POLL_INTERVAL)) as response:
                return response.status == 200
        except OSError:
            # Not listening yet.
            time.sleep(PICOWEB_POLL_INTERVAL)
    return False


def _exit_on_sigterm() -> Any:
    # lobster-trace: SwRequirements.sw_req_plantuml_picoweb
    """Let SIGTERM end trlcdoc like sys.exit(), so the picoweb server is stopped.

    By default, SIGTERM ends Python without running finally blocks and atexit functions,
    which would leave the server running. Signal handlers can only be set in the main thread.

    Returns:
        Any: The previous SIGTERM handler, None if the handler was not replaced.
    """
    if threading.current_thread() is not threading.main_thread():
        return None
    # Exit code 128 + signal number, as the shell reports a terminated process.
    return signal.signal(signal.SIGTERM, lambda signum, _frame: sys.exit(128 + signum))


def _warn_no_picoweb(reason: str) -> None:
    # lobster-trace: SwRequirements.sw_req_plantuml_picoweb
    """Warn that the picoweb server is not available and the jar renders each diagram.

    Args:
        reason (str): Why the server is not available.
    """
    print(
        "Warning: The PlantUML picoweb server is not available, every diagram starts the jar instead. "
        "Set plantuml.picoweb to false to skip the server.\n"
        f"  {reason}"
    )


def java_headless_env() -> dict[str, str]:
    # lobster-trace: SwRequirements.sw_req_plantuml
    """Get the environment that makes Java run PlantUML headless in the converters.

    pyTRLCConverter starts PlantUML with the headless option only on Linux. Windows needs none,
    but on macOS each diagram would start the graphical user interface support of Java (Dock icon).
    Java reads additional options from JAVA_TOOL_OPTIONS. It reports them on stderr, which
    pyTRLCConverter logs as error, so they are only set on macOS.

    see also: https://github.com/NewTec-GmbH/pyTRLCConverter/issues/180

    Returns:
        dict[str, str]: Additional environment variables for the converters, empty except on macOS.
    """
    env: dict[str, str] = {}
    options = os.environ.get("JAVA_TOOL_OPTIONS", "")
    if sys.platform == "darwin" and JAVA_HEADLESS not in options.split():
        env["JAVA_TOOL_OPTIONS"] = f"{options} {JAVA_HEADLESS}".strip()
    return env


def _download(url: str, target: Path) -> Path:
    # lobster-trace: SwRequirements.sw_req_plantuml
    """Download a file.

    Args:
        url (str): Source URL.
        target (Path): Destination file.

    Returns:
        Path: The downloaded file.

    Raises:
        TrlcdocError: If the download fails.
    """
    print(f"Downloading {url}")
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".part")
    try:
        urllib.request.urlretrieve(url, partial)
        partial.replace(target)
    except OSError as err:
        partial.unlink(missing_ok=True)
        raise TrlcdocError(f"Download of {url} failed: {err}") from err
    return target


# Main *************************************************************************
