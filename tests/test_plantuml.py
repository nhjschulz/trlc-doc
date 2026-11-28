"""Tests of the PlantUML provider."""

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

import io
import os
import runpy
import shutil
import signal
import subprocess
import sys
import urllib.request
from pathlib import Path

import pytest
from conftest import base_config, write_config

from trlcdoc import cli, convert, plantuml, plantuml_client
from trlcdoc.config import load_config
from trlcdoc.html import SPHINX_TEMPLATE_DIR, _write_sphinx_config
from trlcdoc.plantuml import DEFAULT_VERSION, JAVA_HEADLESS, provide_plantuml, stop_picoweb
from trlcdoc.util import MARKER_FILE, TrlcdocError

# Variables ********************************************************************

DIAGRAM = "@startuml\nAlice -> Bob: picoweb test\n@enduml\n"
SYNTAX_ERROR_DIAGRAM = "@startuml\nthis is no diagram(\n@enduml\n"

# Classes **********************************************************************

# Functions ********************************************************************


def test_plantuml(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The PlantUML jar is taken from $PLANTUML, the configuration or downloaded, and exported in $PLANTUML.

    Args:
        project (Path): Configuration file of the example project.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.
    """
    root = project.parent
    downloads: list[str] = []

    def fake_download(url: str, target: str) -> None:
        downloads.append(url)
        Path(target).write_bytes(b"jar")

    monkeypatch.setattr(urllib.request, "urlretrieve", fake_download)
    # Java and Graphviz are checked by test_external_tools, here any host may run the test.
    monkeypatch.setattr(plantuml, "find_tool", lambda name, hint: name)
    monkeypatch.setattr(plantuml, "find_graphviz", lambda purpose: "dot")
    # The jars are no real jars, the picoweb server is checked by test_plantuml_picoweb.
    monkeypatch.setattr(plantuml, "start_picoweb", lambda cfg, jar: None)

    # Download of the configured version into the output folder. Setting PLANTUML before deleting it
    # lets monkeypatch restore it, provide_plantuml() exports the jar otherwise beyond this test.
    monkeypatch.setenv("PLANTUML", "")
    monkeypatch.delenv("PLANTUML")
    data = base_config()
    data["plantuml"] = {"version": "1.2023.1"}
    cfg = load_config(write_config(root, data))
    jar = provide_plantuml(cfg)
    assert jar == cfg.plantuml_dir / "plantuml-1.2023.1.jar"
    assert downloads == ["https://github.com/plantuml/plantuml/releases/download/v1.2023.1/plantuml-1.2023.1.jar"]
    assert os.environ["PLANTUML"] == str(jar)
    assert (cfg.output / MARKER_FILE).is_file()

    # An existing download is reused, the default version is used without configuration.
    monkeypatch.delenv("PLANTUML")
    assert provide_plantuml(cfg) == jar
    assert len(downloads) == 1
    monkeypatch.delenv("PLANTUML")
    cfg = load_config(write_config(root, base_config()))
    assert provide_plantuml(cfg).name == f"plantuml-{DEFAULT_VERSION}.jar"

    # A configured jar has precedence over the download.
    (root / "my-plantuml.jar").write_bytes(b"jar")
    data["plantuml"] = {"jar": "my-plantuml.jar"}
    monkeypatch.delenv("PLANTUML")
    assert provide_plantuml(load_config(write_config(root, data))) == root / "my-plantuml.jar"

    # The environment variable has precedence over the configured jar.
    env_jar = root / "env-plantuml.jar"
    env_jar.write_bytes(b"jar")
    monkeypatch.setenv("PLANTUML", str(env_jar))
    assert provide_plantuml(load_config(write_config(root, data))) == env_jar

    # A PlantUML server URL in the environment variable is kept, nothing is downloaded.
    monkeypatch.setenv("PLANTUML", "https://plantuml.example.com/plantuml")
    assert provide_plantuml(load_config(write_config(root, data))) == "https://plantuml.example.com/plantuml"
    assert os.environ["PLANTUML"] == "https://plantuml.example.com/plantuml"
    assert len(downloads) == 2

    # A configured jar that does not exist is an error.
    monkeypatch.delenv("PLANTUML")
    data["plantuml"] = {"jar": "missing.jar"}
    with pytest.raises(TrlcdocError, match="not found"):
        provide_plantuml(load_config(write_config(root, data)))


def test_plantuml_headless(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """PlantUML runs headless: the Sphinx configuration of the html step passes the Java option on every system,
    the convert step passes it to pyTRLCConverter in JAVA_TOOL_OPTIONS on macOS, keeping options set by the user.

    Args:
        project (Path): Configuration file of the example project.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.
    """
    cfg = load_config(project)
    jar = cfg.root / "plantuml.jar"
    jar.write_bytes(b"jar")
    monkeypatch.setenv("PLANTUML", str(jar))

    # html step: the generated Sphinx configuration defines the PlantUML command.
    src_dir = cfg.root / "sphinx"
    src_dir.mkdir()
    shutil.copy(SPHINX_TEMPLATE_DIR / "conf.py", src_dir / "conf.py")
    _write_sphinx_config(cfg, src_dir, [])
    sphinx_conf = runpy.run_path(str(src_dir / "conf.py"))
    assert sphinx_conf["plantuml"] == ["java", JAVA_HEADLESS, "-jar", str(jar)]

    # convert step: the additional environment of the pyTRLCConverter call. The tool lookup is
    # skipped, as shutil.which doesn't work with a simulated platform.
    envs: list[dict[str, str] | None] = []
    monkeypatch.setattr(convert, "run", lambda cmd, cwd, env=None: envs.append(env) or 0)
    monkeypatch.setattr(convert, "find_tool", lambda name: name)
    doc = next(doc for doc in cfg.documents if doc["type"] == "trlc")
    monkeypatch.setenv("JAVA_TOOL_OPTIONS", "-Xmx1g")

    monkeypatch.setattr(sys, "platform", "darwin")
    convert.convert_document(cfg, doc, "rst")
    assert envs[-1] == {"JAVA_TOOL_OPTIONS": f"-Xmx1g {JAVA_HEADLESS}"}

    # The option is not added twice.
    monkeypatch.setenv("JAVA_TOOL_OPTIONS", JAVA_HEADLESS)
    convert.convert_document(cfg, doc, "rst")
    assert envs[-1] == {}

    # Linux gets the option from pyTRLCConverter, Windows needs none.
    for platform in ("linux", "win32"):
        monkeypatch.setattr(sys, "platform", platform)
        convert.convert_document(cfg, doc, "rst")
        assert envs[-1] == {}


def _render(url: str, diagram: str, options: list[str], capsys: pytest.CaptureFixture) -> tuple[int, bytes, str]:
    """Render a diagram with the PlantUML client in this process, as Sphinx does in a process of its own.

    Args:
        url (str): PlantUML server URL.
        diagram (str): PlantUML diagram source.
        options (list[str]): PlantUML options of sphinxcontrib-plantuml.
        capsys (pytest.CaptureFixture): pytest output capture.

    Returns:
        tuple[int, bytes, str]: Exit code, image and error output of the client.
    """
    capsys.readouterr()
    stdin = io.TextIOWrapper(io.BytesIO(diagram.encode("utf-8")), encoding="utf-8")
    stdout = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(sys, "stdin", stdin)
        monkeypatch.setattr(sys, "stdout", stdout)
        exit_code = plantuml_client.main([url, *options])
    stdout.flush()
    return exit_code, stdout.buffer.getvalue(), capsys.readouterr().err


def test_plantuml_picoweb(
    project: Path, plantuml_jar: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """A PlantUML jar is started once as local picoweb server, which renders the diagrams of the converters
    and of Sphinx, and is stopped with the environment restored.

    Args:
        project (Path): Configuration file of the example project.
        plantuml_jar (Path): The PlantUML jar.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.
        capsys (pytest.CaptureFixture): pytest output capture.
    """
    monkeypatch.setenv("PLANTUML", str(plantuml_jar))
    # On Windows, no_proxy and NO_PROXY are one variable: deleting no_proxy first works on every system.
    monkeypatch.delenv("no_proxy", raising=False)
    monkeypatch.setenv("NO_PROXY", "example.com,127.0.0.1")
    windows = sys.platform == "win32"
    sigterm_handler = signal.getsignal(signal.SIGTERM)
    cfg = load_config(project)

    # The server runs on a local port, its URL is exported for the converters and Sphinx.
    url = provide_plantuml(cfg)
    assert isinstance(url, str)
    assert url.startswith("http://127.0.0.1:") and url.endswith("/plantuml")
    assert os.environ["PLANTUML"] == url
    # A listed host is not added again.
    assert os.environ["NO_PROXY"] == "example.com,127.0.0.1"
    monkeypatch.setenv("TRLCDOC_TEST_NO_PROXY", " example.com ,")
    for _ in range(2):
        plantuml._add_no_proxy_host("TRLCDOC_TEST_NO_PROXY", "127.0.0.1")
        assert os.environ["TRLCDOC_TEST_NO_PROXY"] == "example.com,127.0.0.1"
    assert os.environ["no_proxy"] == ("example.com,127.0.0.1" if windows else "127.0.0.1")
    process = plantuml._running_picoweb[0].process
    assert process.poll() is None
    assert f"Starting PlantUML picoweb server {url}" in capsys.readouterr().out

    # Sphinx renders with the client, as a command like the jar.
    src_dir = cfg.root / "sphinx"
    src_dir.mkdir()
    shutil.copy(SPHINX_TEMPLATE_DIR / "conf.py", src_dir / "conf.py")
    _write_sphinx_config(cfg, src_dir, [])
    sphinx_conf = runpy.run_path(str(src_dir / "conf.py"))
    assert sphinx_conf["plantuml"] == [sys.executable, "-m", "trlcdoc.plantuml_client", url]
    result = subprocess.run(
        [*sphinx_conf["plantuml"], "-pipe", "-charset", "utf-8", "-tsvg"],
        input=DIAGRAM.encode("utf-8"),
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert b"<svg" in result.stdout and b"picoweb test" in result.stdout

    # png is the default format, a diagram error gives the error image and exit code 1.
    exit_code, image, _ = _render(url, DIAGRAM, ["-pipe"], capsys)
    assert exit_code == 0 and image.startswith(b"\x89PNG")
    exit_code, image, error = _render(url, SYNTAX_ERROR_DIAGRAM, ["-pipe", "-tsvg"], capsys)
    assert exit_code == 1 and b"Syntax Error" in image
    assert f"PlantUML server {url}: 400" in error

    # SIGTERM ends trlcdoc like sys.exit(), so the server is stopped.
    with pytest.raises(SystemExit) as exit_info:
        signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
    assert exit_info.value.code == 128 + signal.SIGTERM

    # Stopping ends the process and restores the environment and the SIGTERM handler.
    stop_picoweb()
    assert process.poll() is not None
    assert not plantuml._running_picoweb
    assert os.environ["PLANTUML"] == str(plantuml_jar)
    assert os.environ["NO_PROXY"] == "example.com,127.0.0.1"
    assert os.environ.get("no_proxy") == ("example.com,127.0.0.1" if windows else None)
    assert signal.getsignal(signal.SIGTERM) == sigterm_handler
    exit_code, _, error = _render(url, DIAGRAM, ["-pipe"], capsys)
    assert exit_code == 1 and "not reachable" in error
    stop_picoweb()

    # No server if disabled, or if PLANTUML is a server already.
    data = base_config()
    data["plantuml"] = {"picoweb": False}
    assert provide_plantuml(load_config(write_config(cfg.root, data))) == plantuml_jar
    monkeypatch.setenv("PLANTUML", "https://plantuml.example.com/plantuml")
    assert provide_plantuml(cfg) == "https://plantuml.example.com/plantuml"
    assert not plantuml._running_picoweb


def test_plantuml_picoweb_stop(project: Path, plantuml_jar: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The picoweb server is stopped at the end of a run, after a build error and on an interrupt.

    Args:
        project (Path): Configuration file of the example project.
        plantuml_jar (Path): The PlantUML jar.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.
    """
    monkeypatch.setenv("PLANTUML", str(plantuml_jar))
    processes: list[subprocess.Popen] = []
    start_picoweb = plantuml.start_picoweb

    def recording_start_picoweb(cfg: plantuml.Config, jar: Path) -> str | None:
        url = start_picoweb(cfg, jar)
        processes.append(plantuml._running_picoweb[0].process)
        return url

    monkeypatch.setattr(plantuml, "start_picoweb", recording_start_picoweb)

    # End of a successful run.
    assert cli.main(["-c", str(project), "plantuml"]) == 0
    assert len(processes) == 1 and processes[0].poll() is not None
    assert os.environ["PLANTUML"] == str(plantuml_jar)

    # A build error and an interrupt in the step after the plantuml step.
    run_step = cli._run_step
    for error in (TrlcdocError("convert failed"), KeyboardInterrupt()):

        def failing_run_step(step: str, cfg: plantuml.Config, args: object, error: BaseException = error) -> bool:
            if step == "plantuml":
                return run_step(step, cfg, args)
            raise error

        monkeypatch.setattr(cli, "_run_step", failing_run_step)
        expected_exit_code = 2 if isinstance(error, TrlcdocError) else cli.EXIT_INTERRUPTED
        assert cli.main(["-c", str(project), "convert"]) == expected_exit_code
        assert processes[-1].poll() is not None
        assert not plantuml._running_picoweb
    assert len(processes) == 3


def test_plantuml_picoweb_fallback(
    project: Path, plantuml_jar: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Without a working picoweb server, a warning is printed and each diagram uses the jar.

    Args:
        project (Path): Configuration file of the example project.
        plantuml_jar (Path): The PlantUML jar, here only a source of a Java runtime check.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch.
        capsys (pytest.CaptureFixture): pytest output capture.
    """
    cfg = load_config(project)
    warning = "Warning: The PlantUML picoweb server is not available, every diagram starts the jar instead."
    processes: list[subprocess.Popen] = []
    popen = subprocess.Popen

    def recording_popen(*args: object, **kwargs: object) -> subprocess.Popen:
        process = popen(*args, **kwargs)
        processes.append(process)
        return process

    # A jar that Java cannot run: the server ends at once.
    broken_jar = cfg.root / "broken.jar"
    broken_jar.write_bytes(b"no jar")
    monkeypatch.setenv("PLANTUML", str(broken_jar))
    assert provide_plantuml(cfg) == broken_jar
    assert os.environ["PLANTUML"] == str(broken_jar)
    assert warning in capsys.readouterr().err
    assert not plantuml._running_picoweb

    # A server that doesn't answer in time is stopped.
    monkeypatch.setenv("PLANTUML", str(plantuml_jar))
    monkeypatch.setattr(plantuml, "PICOWEB_START_TIMEOUT", 0.0)
    monkeypatch.setattr(plantuml.subprocess, "Popen", recording_popen)
    assert provide_plantuml(cfg) == plantuml_jar
    monkeypatch.undo()
    assert len(processes) == 1 and processes[0].poll() is not None
    output = capsys.readouterr().err
    assert warning in output and "no diagram rendered within 0 s" in output
    assert not plantuml._running_picoweb

    # Java that cannot be started.
    monkeypatch.setenv("PLANTUML", str(plantuml_jar))
    monkeypatch.setattr(plantuml, "find_tool", lambda name, hint="": str(cfg.root / "no-java"))
    assert provide_plantuml(cfg) == plantuml_jar
    assert warning in capsys.readouterr().err
    assert not plantuml._running_picoweb


# Main *************************************************************************
