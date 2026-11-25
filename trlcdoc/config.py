"""Loading, validation and path resolution of the trlcdoc project configuration."""

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
import re
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from .util import TrlcdocError

# Variables ********************************************************************

PACKAGE_DIR = Path(__file__).resolve().parent
SCHEMA_FILE = PACKAGE_DIR / "schema" / "trlcdoc.schema.json"
BUILTIN_DIR = PACKAGE_DIR / "converters"
BUILTIN_PREFIX = "builtin:"
TESTS_COVERAGE = "tests:coverage"

# Document types whose content are TRLC records.
TRLC_DOCUMENT_TYPES = ("trlc", "test_results")

# Placeholder in project owned pages for the page name of a document, {page:<id>}.
# Everything up to the closing brace is taken as id, so a misspelled id is reported.
PAGE_PLACEHOLDER = re.compile(r"\{page:([^}]*)\}")

# Path of an entry in the configuration, e.g. ("documents", 1, "include").
ConfigPath = tuple[str | int, ...]

# Configuration error: path of the entry and message.
ConfigError = tuple[ConfigPath, str]

# Classes **********************************************************************


class Config:
    """Validated project configuration with resolved paths."""

    def __init__(self, data: dict[str, Any], config_file: Path, output: Path | None = None) -> None:
        # lobster-trace: SwRequirements.sw_req_project_settings
        # lobster-trace: SwRequirements.sw_req_documents
        # lobster-trace: SwRequirements.sw_req_output_option
        """Construct the configuration.

        Args:
            data (dict[str, Any]): Schema validated configuration data.
            config_file (Path): The configuration file. Its folder is the project root.
            output (Path | None): Output folder from the command line, replaces paths.output. A relative
                path is relative to the current folder.
        """
        self.data = data
        self.config_file = config_file.resolve()
        self.output_option = output.resolve() if output is not None else None
        self.root = self.config_file.parent
        self.documents: list[dict[str, Any]] = data["documents"]
        self.tests: dict[str, Any] | None = data.get("tests")
        self.trace: dict[str, Any] | None = data.get("trace")
        self.project: dict[str, Any] = data["project"]
        self.html: dict[str, Any] = data.get("html", {})
        self.plantuml: dict[str, Any] = data.get("plantuml", {})

    # Paths ********************************************************************

    def path(self, value: str) -> Path:
        # lobster-trace: SwRequirements.sw_req_config_file
        """Resolve a configured path against the project root.

        Args:
            value (str): Absolute path or path relative to the project root.

        Returns:
            Path: The absolute path.
        """
        return (self.root / value).resolve()

    @property
    def output(self) -> Path:
        # lobster-trace: SwRequirements.sw_req_output_folder
        # lobster-trace: SwRequirements.sw_req_output_option
        """Folder for all generated files: the --output option, else paths.output."""
        result = self.output_option
        if result is None:
            result = self.path(self.data["paths"].get("output", "build/trlcdoc"))
        return result

    @property
    def trlc_model(self) -> Path:
        # lobster-trace: SwRequirements.sw_req_trlc_conversion
        """Folder with the TRLC model files."""
        return self.path(self.data["paths"]["trlc_model"])

    @property
    def plantuml_dir(self) -> Path:
        # lobster-trace: SwRequirements.sw_req_plantuml
        # lobster-trace: SwRequirements.sw_req_output_folder
        """Folder for the downloaded PlantUML jar."""
        return self.output / "plantuml"

    def convert_dir(self, fmt: str, doc_id: str) -> Path:
        # lobster-trace: SwRequirements.sw_req_trlc_conversion
        # lobster-trace: SwRequirements.sw_req_output_folder
        """Output folder of a converted document.

        Args:
            fmt (str): Output format, rst or markdown.
            doc_id (str): Document id.

        Returns:
            Path: The output folder.
        """
        return self.output / "convert" / fmt / doc_id

    @property
    def tests_dir(self) -> Path:
        # lobster-trace: SwRequirements.sw_req_test_run
        # lobster-trace: SwRequirements.sw_req_output_folder
        """Output folder of the tests step."""
        return self.output / "tests"

    @property
    def junit_file(self) -> Path:
        # lobster-trace: SwRequirements.sw_req_test_run
        """JUnit XML file with the test results."""
        result = self.tests_dir / "junit.xml"
        if self.tests is not None and self.tests["runner"] == "command":
            result = self.path(self.tests["junit"])
        return result

    @property
    def coverage_dir(self) -> Path:
        # lobster-trace: SwRequirements.sw_req_test_run
        """HTML coverage report folder."""
        result = self.tests_dir / "coverage"
        if self.tests is not None and "coverage" in self.tests:
            result = self.path(self.tests["coverage"])
        return result

    @property
    def test_results_dir(self) -> Path:
        # lobster-trace: SwRequirements.sw_req_test_results
        """Folder with the TRLC test result records generated from the JUnit XML."""
        return self.tests_dir / "results"

    @property
    def trace_dir(self) -> Path:
        # lobster-trace: SwRequirements.sw_req_trace_report
        # lobster-trace: SwRequirements.sw_req_output_folder
        """Output folder of the trace step."""
        return self.output / "trace"

    @property
    def trace_report_html(self) -> Path:
        # lobster-trace: SwRequirements.sw_req_trace_report
        """The HTML tracing report."""
        return self.trace_dir / "tracing_report.html"

    @property
    def trace_report_rst(self) -> Path:
        # lobster-trace: SwRequirements.sw_req_trace_report_rst
        """Folder of the reStructuredText tracing report, one page per level."""
        return self.trace_dir / "rst"

    @property
    def trace_report_format(self) -> str:
        # lobster-trace: SwRequirements.sw_req_trace_report_rst
        """Format of the tracing report: 'html' (default) or 'rst'."""
        return (self.trace or {}).get("report", "html")

    @property
    def sphinx_dir(self) -> Path:
        # lobster-trace: SwRequirements.sw_req_html_site
        # lobster-trace: SwRequirements.sw_req_output_folder
        """Generated Sphinx source folder."""
        return self.output / "sphinx"

    @property
    def html_dir(self) -> Path:
        # lobster-trace: SwRequirements.sw_req_html_site
        # lobster-trace: SwRequirements.sw_req_output_folder
        """Generated HTML site."""
        return self.output / "html"

    # Documents ****************************************************************

    def document(self, doc_id: str) -> dict[str, Any]:
        # lobster-trace: SwRequirements.sw_req_documents
        """Get a document by its id.

        Args:
            doc_id (str): Document id.

        Returns:
            dict[str, Any]: The document configuration.
        """
        return next(doc for doc in self.documents if doc["id"] == doc_id)

    def page_name(self, doc: dict[str, Any]) -> str:
        # lobster-trace: SwRequirements.sw_req_documents
        # lobster-trace: SwRequirements.sw_req_page_placeholders
        """Get the Sphinx page name of a document, the name used in a table of contents.

        Documents with several pages are a folder with an index page: TRLC documents and the
        reStructuredText tracing report. All other documents are a single page.

        Args:
            doc (dict[str, Any]): Document configuration.

        Returns:
            str: '<id>/index' for a folder of pages, otherwise '<id>'.
        """
        result = doc["id"]
        if doc["type"] in TRLC_DOCUMENT_TYPES or (doc["type"] == "trace_report" and self.trace_report_format == "rst"):
            result = f"{doc['id']}/index"
        return result

    def placeholder_files(self) -> list[tuple[str, ConfigPath, Path]]:
        # lobster-trace: SwRequirements.sw_req_html_customization
        # lobster-trace: SwRequirements.sw_req_page_placeholders
        """Get the project owned files whose placeholders are replaced.

        Returns:
            list[tuple[str, ConfigPath, Path]]: Configuration location, its entry path and the path of html.index,
            html.page_header and the rst and markdown documents, except documents with 'placeholders: false'.
        """
        result: list[tuple[str, ConfigPath, Path]] = [
            (f"html.{key}", ("html", key), self.path(self.html[key]))
            for key in ("index", "page_header")
            if key in self.html
        ]
        result.extend(
            (f"documents[{doc['id']}]", ("documents", index, "source"), self.path(doc["source"]))
            for index, doc in enumerate(self.documents)
            if doc["type"] in ("rst", "markdown") and doc.get("placeholders", True)
        )
        return result

    def trlc_sources(self, doc: dict[str, Any]) -> list[Path]:
        # lobster-trace: SwRequirements.sw_req_trlc_conversion
        """Get the TRLC source folders of a TRLC document.

        Args:
            doc (dict[str, Any]): Document of type trlc or test_results.

        Returns:
            list[Path]: The source folders.
        """
        result = [self.test_results_dir]
        if doc["type"] == "trlc":
            result = [self.path(doc["source"])]
        return result

    def included_documents(self, doc: dict[str, Any]) -> list[dict[str, Any]]:
        # lobster-trace: SwRequirements.sw_req_trlc_conversion
        """Get all documents included by a document, transitively.

        Args:
            doc (dict[str, Any]): The including document.

        Returns:
            list[dict[str, Any]]: Included documents, without the document itself.
        """
        result: list[dict[str, Any]] = []
        pending = list(doc.get("include", []))
        while pending:
            doc_id = pending.pop(0)
            if doc_id != doc["id"] and all(inc["id"] != doc_id for inc in result):
                included = self.document(doc_id)
                result.append(included)
                pending.extend(included.get("include", []))
        return result

    def included_sources(self, doc: dict[str, Any]) -> list[Path]:
        # lobster-trace: SwRequirements.sw_req_trlc_conversion
        """Get the TRLC source folders of all documents included by a document.

        Args:
            doc (dict[str, Any]): The including document.

        Returns:
            list[Path]: The source folders.
        """
        result: list[Path] = []
        for included in self.included_documents(doc):
            result.extend(self.trlc_sources(included))
        return result

    def file_reference(self, value: str) -> Path:
        # lobster-trace: SwRequirements.sw_req_trlc_conversion
        # lobster-trace: SwRequirements.sw_req_builtin_converters
        """Resolve a converter, translation or render configuration file reference.

        Args:
            value (str): 'builtin:<file>' or a path relative to the project root.

        Returns:
            Path: The absolute file path.
        """
        result = self.path(value)
        if value.startswith(BUILTIN_PREFIX):
            result = BUILTIN_DIR / value[len(BUILTIN_PREFIX) :]
        return result

    def html_source(self, doc: dict[str, Any]) -> Path:
        # lobster-trace: SwRequirements.sw_req_document_types
        """Resolve the HTML folder of a document of type html or command.

        Args:
            doc (dict[str, Any]): Document of type html or command.

        Returns:
            Path: The HTML folder.
        """
        result = self.coverage_dir
        if doc["type"] == "command":
            result = self.path(doc["output"])
        elif doc["source"] != TESTS_COVERAGE:
            result = self.path(doc["source"])
        return result

    # Project ******************************************************************

    @property
    def repository(self) -> str:
        # lobster-trace: SwRequirements.sw_req_project_settings
        # lobster-trace: SwRequirements.sw_req_trace_report
        """Configured repository URL or 'auto'."""
        return self.project.get("repository", "auto")


# Functions ********************************************************************


def _check_references(cfg: Config) -> list[ConfigError]:
    # lobster-trace: SwRequirements.sw_req_config_validation
    # lobster-trace: SwRequirements.sw_req_output_folder
    """Check the cross references, which the JSON schema cannot express.

    Args:
        cfg (Config): Schema validated configuration.

    Returns:
        list[ConfigError]: Errors, empty if all references are valid.
    """
    errors: list[ConfigError] = []
    doc_ids = [doc["id"] for doc in cfg.documents]
    doc_types = {doc["id"]: doc["type"] for doc in cfg.documents}

    # A repeated id is reported at its second occurrence.
    for index, doc_id in enumerate(doc_ids):
        if doc_ids[:index].count(doc_id) == 1:
            errors.append((("documents", index, "id"), f"documents: id '{doc_id}' is used more than once."))

    for index, doc in enumerate(cfg.documents):
        errors.extend(_check_document(cfg, ("documents", index), doc, doc_types))

    if cfg.trace is not None:
        errors.extend(_check_levels(cfg, cfg.trace["levels"], doc_types))

    for key in ("logo", "favicon"):
        if cfg.project.get(key) and not cfg.path(cfg.project[key]).is_file():
            errors.append((("project", key), f"project.{key}: file '{cfg.project[key]}' not found."))

    for key in ("conf", "index", "page_header"):
        if key in cfg.html and not cfg.path(cfg.html[key]).is_file():
            errors.append((("html", key), f"html.{key}: file '{cfg.html[key]}' not found."))

    errors.extend(_check_page_placeholders(cfg, doc_ids))

    # With the --output option, paths.output is not used. load_config() checks the option instead.
    if cfg.output_option is None:
        for message in _check_output(cfg):
            errors.append((("paths", "output"), f"paths.output: {message}"))

    return errors


def _check_output(cfg: Config) -> list[str]:
    # lobster-trace: SwRequirements.sw_req_output_folder
    # lobster-trace: SwRequirements.sw_req_output_option
    """Check that the output folder is at a safe location.

    Args:
        cfg (Config): Schema validated configuration.

    Returns:
        list[str]: Errors without the name of the setting, empty if the location is safe.
    """
    errors: list[str] = []
    if cfg.output.is_relative_to(PACKAGE_DIR):
        errors.append("must not be inside the trlcdoc package folder.")
    # The clean step removes the output folder, so it must never contain the project.
    if cfg.root.is_relative_to(cfg.output):
        errors.append("must not be the project root or one of its parents.")
    return errors


def _check_page_placeholders(cfg: Config, doc_ids: list[str]) -> list[ConfigError]:
    # lobster-trace: SwRequirements.sw_req_config_validation
    # lobster-trace: SwRequirements.sw_req_page_placeholders
    """Check that the {page:<id>} placeholders of the project owned files name configured documents.

    Args:
        cfg (Config): Schema validated configuration.
        doc_ids (list[str]): Ids of the configured documents.

    Returns:
        list[ConfigError]: Errors, empty if all placeholders name a document.
    """
    errors: list[ConfigError] = []
    for where, entry, file in cfg.placeholder_files():
        if file.is_file():
            ids = PAGE_PLACEHOLDER.findall(file.read_text(encoding="utf-8"))
            errors.extend(
                (entry, f"{where}: placeholder '{{page:{doc_id}}}' names no document.")
                for doc_id in sorted(set(ids))
                if doc_id not in doc_ids
            )
    return errors


def _check_document(
    cfg: Config, entry: ConfigPath, doc: dict[str, Any], doc_types: dict[str, str]
) -> list[ConfigError]:
    # lobster-trace: SwRequirements.sw_req_config_validation
    """Check the references of one document.

    Args:
        cfg (Config): Schema validated configuration.
        entry (ConfigPath): Path of the document in the configuration.
        doc (dict[str, Any]): The document.
        doc_types (dict[str, str]): Document type per document id.

    Returns:
        list[ConfigError]: Errors, empty if all references are valid.
    """
    errors: list[ConfigError] = []
    where = f"documents[{doc['id']}]"

    for index, inc in enumerate(doc.get("include", [])):
        if doc_types.get(inc) not in TRLC_DOCUMENT_TYPES:
            errors.append(
                ((*entry, "include", index), f"{where}.include: '{inc}' is no document of type trlc or test_results.")
            )

    options = doc.get("pytrlcconverter", {})
    files = {("converter", fmt): value for fmt, value in options.get("converter", {}).items()}
    files.update({(key,): options[key] for key in ("translation", "render_cfg") if key in options})
    for keys, value in files.items():
        if not cfg.file_reference(value).is_file():
            errors.append(
                (
                    (*entry, "pytrlcconverter", *keys),
                    f"{where}.pytrlcconverter.{'.'.join(keys)}: file '{value}' not found.",
                )
            )

    needs_tests = doc["type"] == "test_results" or doc.get("source") == TESTS_COVERAGE
    if needs_tests and cfg.tests is None:
        errors.append((entry, f"{where}: needs a 'tests' section."))
    if doc["type"] == "trace_report" and cfg.trace is None:
        errors.append((entry, f"{where}: type trace_report needs a 'trace' section."))
    return errors


def _check_levels(cfg: Config, levels: list[dict[str, Any]], doc_types: dict[str, str]) -> list[ConfigError]:
    # lobster-trace: SwRequirements.sw_req_config_validation
    # lobster-trace: SwRequirements.sw_req_trace_levels
    # lobster-trace: SwRequirements.sw_req_trace_doxygen
    """Check the trace level references.

    Args:
        cfg (Config): Schema validated configuration.
        levels (list[dict[str, Any]]): Configured trace levels.
        doc_types (dict[str, str]): Document type per document id.

    Returns:
        list[ConfigError]: Errors, empty if all references are valid.
    """
    errors: list[ConfigError] = []
    names = [level["name"] for level in levels]

    # A repeated name is reported at its second occurrence.
    for index, name in enumerate(names):
        if names[:index].count(name) == 1:
            errors.append((("trace", "levels", index, "name"), f"trace.levels: name '{name}' is used more than once."))

    for index, level in enumerate(levels):
        entry: ConfigPath = ("trace", "levels", index)
        where = f"trace.levels[{level['name']}]"
        if "document" in level and doc_types.get(level["document"]) not in TRLC_DOCUMENT_TYPES:
            errors.append(
                (
                    (*entry, "document"),
                    f"{where}.document: '{level['document']}' is no document of type trlc or test_results.",
                )
            )
        if "doxyfile" in level and not cfg.path(level["doxyfile"]).is_file():
            errors.append(((*entry, "doxyfile"), f"{where}.doxyfile: file '{level['doxyfile']}' not found."))
        for key in ("trace_to", "requires"):
            for target_index, target in enumerate(level.get(key, [])):
                if target not in names:
                    errors.append(((*entry, key, target_index), f"{where}.{key}: level '{target}' is not defined."))
    return errors


def _line_map(text: str) -> dict[ConfigPath, int]:
    # lobster-trace: SwRequirements.sw_req_config_validation
    """Map the path of every configuration entry to its line in the file.

    Args:
        text (str): Content of the configuration file, valid YAML.

    Returns:
        dict[ConfigPath, int]: Line number, starting at 1, per entry path. A mapping key gives the line of the
        key, a list item the line of the item. The root is line 1.
    """
    lines: dict[ConfigPath, int] = {(): 1}

    def walk(node: yaml.Node, path: ConfigPath, parents: tuple[int, ...]) -> None:
        # Aliases may refer to an enclosing node, which would recurse forever.
        if id(node) in parents:
            return
        parents = (*parents, id(node))
        children: list[tuple[str | int, yaml.Node, yaml.Node]] = []
        if isinstance(node, yaml.MappingNode):
            children = [(key.value, key, value) for key, value in node.value if isinstance(key, yaml.ScalarNode)]
        elif isinstance(node, yaml.SequenceNode):
            children = [(index, item, item) for index, item in enumerate(node.value)]
        for name, position, value in children:
            lines.setdefault((*path, name), position.start_mark.line + 1)
            walk(value, (*path, name), parents)

    root = yaml.compose(text, Loader=yaml.SafeLoader)
    if root is not None:
        walk(root, (), ())
    return lines


def _schema_error_path(err: jsonschema.ValidationError) -> ConfigPath:
    # lobster-trace: SwRequirements.sw_req_config_validation
    """Get the path of the entry a schema error is about.

    Args:
        err (jsonschema.ValidationError): The schema error.

    Returns:
        ConfigPath: The path of the value, or of the key for a key that is not allowed.
    """
    path: ConfigPath = tuple(err.absolute_path)
    if "propertyNames" in err.schema_path:
        path = (*path, err.instance)
    elif err.validator == "additionalProperties" and isinstance(err.instance, dict):
        allowed = err.schema.get("properties", {})
        path = (*path, *[key for key in err.instance if key not in allowed][:1])
    return path


def _format_errors(config_file: Path, text: str, errors: list[ConfigError]) -> str:
    # lobster-trace: SwRequirements.sw_req_config_validation
    """Format configuration errors with file and line of their entry, ordered by line.

    Args:
        config_file (Path): The configuration file.
        text (str): Content of the configuration file, valid YAML.
        errors (list[ConfigError]): The errors.

    Returns:
        str: One line '<file>:<line>: <message>' per error. An entry that is not in the file, e.g. a
        missing key, gets the line of its closest parent.
    """
    lines = _line_map(text)

    def line(path: ConfigPath) -> int:
        while path not in lines:
            path = path[:-1]
        return lines[path]

    numbered = sorted(((line(path), message) for path, message in errors), key=lambda error: error[0])
    return "\n  ".join(f"{config_file}:{number}: {message}" for number, message in numbered)


def load_config(config_file: Path, output: Path | None = None) -> Config:
    # lobster-trace: SwRequirements.sw_req_config_file
    # lobster-trace: SwRequirements.sw_req_config_validation
    # lobster-trace: SwRequirements.sw_req_output_option
    """Load and validate the project configuration.

    Args:
        config_file (Path): The trlcdoc YAML configuration file.
        output (Path | None): Output folder from the command line, replaces paths.output. A relative
            path is relative to the current folder.

    Returns:
        Config: The validated configuration.

    Raises:
        TrlcdocError: If the file is missing or invalid.
    """
    if not config_file.is_file():
        raise TrlcdocError(f"Configuration file {config_file} not found.")

    text = config_file.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise TrlcdocError(f"{config_file} is no valid YAML: {error}") from error

    with open(SCHEMA_FILE, encoding="utf-8") as file:
        schema = json.load(file)

    validator = jsonschema.Draft202012Validator(schema)
    schema_errors: list[ConfigError] = [
        (_schema_error_path(err), f"{'/'.join(str(p) for p in err.absolute_path) or '<root>'}: {err.message}")
        for err in sorted(validator.iter_errors(data), key=lambda err: list(err.absolute_path))
    ]
    if schema_errors:
        raise TrlcdocError(
            f"{config_file} does not match the schema:\n  " + _format_errors(config_file, text, schema_errors)
        )

    cfg = Config(data, config_file, output)
    reference_errors = _check_references(cfg)
    if reference_errors:
        raise TrlcdocError(
            f"{config_file} has invalid settings:\n  " + _format_errors(config_file, text, reference_errors)
        )

    if cfg.output_option is not None:
        output_errors = _check_output(cfg)
        if output_errors:
            raise TrlcdocError(f"--output {cfg.output_option}: " + " ".join(output_errors))

    return cfg


def find_config(start: Path) -> Path:
    # lobster-trace: SwRequirements.sw_req_config_file
    """Find the default configuration file trlcdoc.yaml in a folder or its parents.

    Args:
        start (Path): Folder to start the search in.

    Returns:
        Path: The configuration file, or start/trlcdoc.yaml if none was found.
    """
    candidates = [folder / "trlcdoc.yaml" for folder in (start, *start.parents)]
    return next((file for file in candidates if file.is_file()), start / "trlcdoc.yaml")


# Main *************************************************************************
