# trlcdoc

Configurable documentation tooling for NewTec TRLC based projects.

The trlcdoc tool is a tailored utility for converting trlc files,
test results and lobster trace report into a static project report
web site. It is  driven by a configuration yaml file that defines
the project specific content to process.

Status: prototype. Projects add this repository as git submodule, e.g. in
`tools/trlc-doc`, and install it into their virtual environment.

## Usage

```bash
git submodule add https://github.com/nhjschulz/trlc-doc tools/trlc-doc
pip install -e tools/trlc-doc       # the submodule folder
trlcdoc                             # all steps, uses ./trlcdoc.yaml (or a parent folder)
trlcdoc tests trace                 # selected steps only
trlcdoc clean                       # remove all build artifacts
trlcdoc clean all                   # fresh full build
trlcdoc convert --format markdown   # Markdown export of the TRLC documents
trlcdoc trace --online              # tracing report linked to the repository
trlcdoc -c other.yaml check         # validate a configuration
```

Steps, always executed in this order:

| Step | Does |
|---|---|
| `clean` | Removes the output folder with all build artifacts, including the downloaded PlantUML jar. Not part of `all`. |
| `check` | Validates the configuration against the schema and checks all references. |
| `plantuml` | Uses `$PLANTUML`, a configured jar, or downloads the configured PlantUML version. |
| `tests` | Runs pytest (or a command), converts the JUnit XML into TRLC test result records. |
| `convert` | Converts each TRLC document with its pyTRLCConverter converter. |
| `trace` | Generates the lobster-trlc configs and the LOBSTER policy from `trace.levels`, creates the HTML tracing report. |
| `html` | Generates the Sphinx sources from `documents` and builds the site. |

Exit codes: `0` success, `1` content findings (failed tests, missing trace
links), `2` build error. All generated files go to `paths.output`
(default `build/trlcdoc`), never into this package folder.

## Configuration

The project configuration `trlcdoc.yaml` lives in the project root. Its schema
is [trlcdoc/schema/trlcdoc.schema.json](trlcdoc/schema/trlcdoc.schema.json);
editors with YAML language support validate against it with this first line:

```yaml
# yaml-language-server: $schema=tools/trlc-doc/trlcdoc/schema/trlcdoc.schema.json
```

Key concepts:

- **documents** are the pages of the site, in table of contents order. Their
  `id` is the key used everywhere else. Types: `trlc`, `test_results`,
  `trace_report`, `html`, `rst`, `markdown`, `text`, `command`.
- **converter** names the pyTRLCConverter project file per output format.
  `builtin:<file>` refers to [trlcdoc/converters](trlcdoc/converters), any other
  path is relative to the project root.
- **include** lists the documents whose TRLC files are needed to resolve
  references, e.g. the requirements for the architecture.
- **trace.levels** are the LOBSTER levels. Each TRLC level names its `document`;
  the lobster-trlc inputs are derived from it and its includes.
- **tests.link** maps test results to TRLC test cases: the JUnit `property`
  if the test records one, otherwise the `from` -> `to` name pattern. A test
  recording several test cases needs `array: true` and a model with
  `relates SwTestCase [1 .. *]`.
- **html** customizes the site: `theme`, `extensions`, `extra_conf`, a project
  start page `index` (it owns the toctree; TRLC documents are named
  `<id>/index`), a `page_header` for every generated page, and a project Sphinx
  configuration file `conf`, executed at the end of the generated conf.py with
  `PROJECT_ROOT` set. In these files and in `rst`/`markdown` documents,
  `{project_root}` is replaced by the relative path from the page to the
  project root.
- A TRLC or test result document without `title` takes its page title from the
  converted content.
- **PLANTUML** environment variable: a plantuml.jar or a PlantUML server URL.

The built-in converters are the project converters of
[pyTRLCConverter](https://github.com/NewTec-GmbH/pyTRLCConverter) (`tools/converter`),
for its 3.x API. pyTRLCConverter also determines the trlc version.

See the flashcontainer
[trlcdoc.yaml](https://github.com/nhjschulz/flashcontainer/blob/master/trlcdoc.yaml)
for a complete example.

## Trlcdoc Documentation

The trlc project documentation is itself being generated using trlcdoc. Run the
following commands to build it:

```
# setup virtual environment and install trlcdoc

python3 -m venv .venv
. .venv/bin/activate
pip install -e .[test]

# generate documentation
trlcdoc -c trlcdoc.yaml 
```
The resulting documentation is generated in folder `build/trlcdoc/html`

## Tests

The pytest unit tests in [tests](tests) verify the software requirements. Each
test function `test_<name>` implements the TRLC test case `tc_<name>` in
[trlc/swe-test](trlc/swe-test), which links it to its requirements. Most tests
run trlcdoc on a minimal example project, created in a temporary folder.

```
pip install -e .[test]
pytest
```

The HTML site tests need a Java runtime for PlantUML. They use the jar from
`$PLANTUML`, or download it once into the pytest cache. The
[Tests workflow](.github/workflows/test.yml) runs the tests on every push and
pull request on Linux and Windows.

## License

GPL-3.0, see [LICENSE](LICENSE).