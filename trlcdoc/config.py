"""Loading, validation and path resolution of the trlcdoc project configuration.

    Author: Norbert Schulz (norbert.schulz@newtec.de)
"""

# *******************************************************************************
# Copyright (c) NewTec GmbH 2026   -   www.newtec.de
# *******************************************************************************

# Imports **********************************************************************

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

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

# Classes **********************************************************************


class Config:
    """Validated project configuration with resolved paths."""

    def __init__(self, data: Dict[str, Any], config_file: Path) -> None:
        """Construct the configuration.

        Args:
            data (Dict[str, Any]): Schema validated configuration data.
            config_file (Path): The configuration file. Its folder is the project root.
        """
        self.data = data
        self.config_file = config_file.resolve()
        self.root = self.config_file.parent
        self.documents: List[Dict[str, Any]] = data["documents"]
        self.tests: Optional[Dict[str, Any]] = data.get("tests")
        self.trace: Optional[Dict[str, Any]] = data.get("trace")
        self.project: Dict[str, Any] = data["project"]
        self.html: Dict[str, Any] = data.get("html", {})
        self.plantuml: Dict[str, Any] = data.get("plantuml", {})

    # Paths ********************************************************************

    def path(self, value: str) -> Path:
        """Resolve a configured path against the project root.

        Args:
            value (str): Absolute path or path relative to the project root.

        Returns:
            Path: The absolute path.
        """
        return (self.root / value).resolve()

    @property
    def output(self) -> Path:
        """Folder for all generated files."""
        return self.path(self.data["paths"].get("output", "build/trlcdoc"))

    @property
    def trlc_model(self) -> Path:
        """Folder with the TRLC model files."""
        return self.path(self.data["paths"]["trlc_model"])

    @property
    def plantuml_dir(self) -> Path:
        """Folder for the downloaded PlantUML jar."""
        return self.output / "plantuml"

    def convert_dir(self, fmt: str, doc_id: str) -> Path:
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
        """Output folder of the tests step."""
        return self.output / "tests"

    @property
    def junit_file(self) -> Path:
        """JUnit XML file with the test results."""
        result = self.tests_dir / "junit.xml"
        if self.tests is not None and self.tests["runner"] == "command":
            result = self.path(self.tests["junit"])
        return result

    @property
    def coverage_dir(self) -> Path:
        """HTML coverage report folder."""
        result = self.tests_dir / "coverage"
        if self.tests is not None and "coverage" in self.tests:
            result = self.path(self.tests["coverage"])
        return result

    @property
    def test_results_dir(self) -> Path:
        """Folder with the TRLC test result records generated from the JUnit XML."""
        return self.tests_dir / "results"

    @property
    def trace_dir(self) -> Path:
        """Output folder of the trace step."""
        return self.output / "trace"

    @property
    def trace_report_html(self) -> Path:
        """The HTML tracing report."""
        return self.trace_dir / "tracing_report.html"

    @property
    def sphinx_dir(self) -> Path:
        """Generated Sphinx source folder."""
        return self.output / "sphinx"

    @property
    def html_dir(self) -> Path:
        """Generated HTML site."""
        return self.output / "html"

    # Documents ****************************************************************

    def document(self, doc_id: str) -> Dict[str, Any]:
        """Get a document by its id.

        Args:
            doc_id (str): Document id.

        Returns:
            Dict[str, Any]: The document configuration.
        """
        return next(doc for doc in self.documents if doc["id"] == doc_id)

    def trlc_sources(self, doc: Dict[str, Any]) -> List[Path]:
        """Get the TRLC source folders of a TRLC document.

        Args:
            doc (Dict[str, Any]): Document of type trlc or test_results.

        Returns:
            List[Path]: The source folders.
        """
        result = [self.test_results_dir]
        if doc["type"] == "trlc":
            result = [self.path(doc["source"])]
        return result

    def included_documents(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all documents included by a document, transitively.

        Args:
            doc (Dict[str, Any]): The including document.

        Returns:
            List[Dict[str, Any]]: Included documents, without the document itself.
        """
        result: List[Dict[str, Any]] = []
        pending = list(doc.get("include", []))
        while pending:
            doc_id = pending.pop(0)
            if doc_id != doc["id"] and all(inc["id"] != doc_id for inc in result):
                included = self.document(doc_id)
                result.append(included)
                pending.extend(included.get("include", []))
        return result

    def included_sources(self, doc: Dict[str, Any]) -> List[Path]:
        """Get the TRLC source folders of all documents included by a document.

        Args:
            doc (Dict[str, Any]): The including document.

        Returns:
            List[Path]: The source folders.
        """
        result: List[Path] = []
        for included in self.included_documents(doc):
            result.extend(self.trlc_sources(included))
        return result

    def file_reference(self, value: str) -> Path:
        """Resolve a converter, translation or render configuration file reference.

        Args:
            value (str): 'builtin:<file>' or a path relative to the project root.

        Returns:
            Path: The absolute file path.
        """
        result = self.path(value)
        if value.startswith(BUILTIN_PREFIX):
            result = BUILTIN_DIR / value[len(BUILTIN_PREFIX):]
        return result

    def html_source(self, doc: Dict[str, Any]) -> Path:
        """Resolve the HTML folder of a document of type html or command.

        Args:
            doc (Dict[str, Any]): Document of type html or command.

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
        """Configured repository URL or 'auto'."""
        return self.project.get("repository", "auto")

# Functions ********************************************************************


def _check_references(cfg: Config) -> List[str]:
    """Check the cross references, which the JSON schema cannot express.

    Args:
        cfg (Config): Schema validated configuration.

    Returns:
        List[str]: Error messages, empty if all references are valid.
    """
    errors: List[str] = []
    doc_ids = [doc["id"] for doc in cfg.documents]
    doc_types = {doc["id"]: doc["type"] for doc in cfg.documents}

    for doc_id in sorted({doc_id for doc_id in doc_ids if doc_ids.count(doc_id) > 1}):
        errors.append(f"documents: id '{doc_id}' is used more than once.")

    for doc in cfg.documents:
        errors.extend(_check_document(cfg, doc, doc_types))

    if cfg.trace is not None:
        errors.extend(_check_levels(cfg.trace["levels"], doc_types))

    if cfg.output.is_relative_to(PACKAGE_DIR):
        errors.append("paths.output: must not be inside the trlcdoc package folder.")
    # The clean step removes the output folder, so it must never contain the project.
    if cfg.root.is_relative_to(cfg.output):
        errors.append("paths.output: must not be the project root or one of its parents.")

    return errors


def _check_document(cfg: Config, doc: Dict[str, Any], doc_types: Dict[str, str]) -> List[str]:
    """Check the references of one document.

    Args:
        cfg (Config): Schema validated configuration.
        doc (Dict[str, Any]): The document.
        doc_types (Dict[str, str]): Document type per document id.

    Returns:
        List[str]: Error messages, empty if all references are valid.
    """
    errors: List[str] = []
    where = f"documents[{doc['id']}]"

    for inc in doc.get("include", []):
        if doc_types.get(inc) not in TRLC_DOCUMENT_TYPES:
            errors.append(f"{where}.include: '{inc}' is no document of type trlc or test_results.")

    files = {f"converter.{fmt}": value for fmt, value in doc.get("converter", {}).items()}
    files.update({key: doc[key] for key in ("translation", "render_cfg") if key in doc})
    for key, value in files.items():
        if not cfg.file_reference(value).is_file():
            errors.append(f"{where}.{key}: file '{value}' not found.")

    needs_tests = doc["type"] == "test_results" or doc.get("source") == TESTS_COVERAGE
    if needs_tests and cfg.tests is None:
        errors.append(f"{where}: needs a 'tests' section.")
    if doc["type"] == "trace_report" and cfg.trace is None:
        errors.append(f"{where}: type trace_report needs a 'trace' section.")
    return errors


def _check_levels(levels: List[Dict[str, Any]], doc_types: Dict[str, str]) -> List[str]:
    """Check the trace level references.

    Args:
        levels (List[Dict[str, Any]]): Configured trace levels.
        doc_types (Dict[str, str]): Document type per document id.

    Returns:
        List[str]: Error messages, empty if all references are valid.
    """
    errors: List[str] = []
    names = [level["name"] for level in levels]

    for name in sorted({name for name in names if names.count(name) > 1}):
        errors.append(f"trace.levels: name '{name}' is used more than once.")

    for level in levels:
        where = f"trace.levels[{level['name']}]"
        if "document" in level and doc_types.get(level["document"]) not in TRLC_DOCUMENT_TYPES:
            errors.append(f"{where}.document: '{level['document']}' is no document of type trlc or test_results.")
        for key in ("trace_to", "requires"):
            for target in level.get(key, []):
                if target not in names:
                    errors.append(f"{where}.{key}: level '{target}' is not defined.")
    return errors


def load_config(config_file: Path) -> Config:
    """Load and validate the project configuration.

    Args:
        config_file (Path): The trlcdoc YAML configuration file.

    Returns:
        Config: The validated configuration.

    Raises:
        TrlcdocError: If the file is missing or invalid.
    """
    if not config_file.is_file():
        raise TrlcdocError(f"Configuration file {config_file} not found.")

    with open(config_file, encoding="utf-8") as file:
        data = yaml.safe_load(file)

    with open(SCHEMA_FILE, encoding="utf-8") as file:
        schema = json.load(file)

    validator = jsonschema.Draft202012Validator(schema)
    schema_errors = sorted(validator.iter_errors(data), key=lambda err: list(err.absolute_path))
    if schema_errors:
        messages = [f"{'/'.join(str(p) for p in err.absolute_path) or '<root>'}: {err.message}"
                    for err in schema_errors]
        raise TrlcdocError(f"{config_file} does not match the schema:\n  " + "\n  ".join(messages))

    cfg = Config(data, config_file)
    reference_errors = _check_references(cfg)
    if reference_errors:
        raise TrlcdocError(f"{config_file} has invalid settings:\n  " + "\n  ".join(reference_errors))

    return cfg


def find_config(start: Path) -> Path:
    """Find the default configuration file trlcdoc.yaml in a folder or its parents.

    Args:
        start (Path): Folder to start the search in.

    Returns:
        Path: The configuration file, or start/trlcdoc.yaml if none was found.
    """
    candidates = [folder / "trlcdoc.yaml" for folder in (start, *start.parents)]
    return next((file for file in candidates if file.is_file()), start / "trlcdoc.yaml")

# Main *************************************************************************
