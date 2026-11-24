# trlcdoc

[![License: GPL-3.0-or-later](https://img.shields.io/badge/license-GPL--3.0--or--later-blue)](https://github.com/nhjschulz/trlc-doc/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/trlcdoc)](https://pypi.org/project/trlcdoc/)
[![Tests](https://github.com/nhjschulz/trlc-doc/actions/workflows/test.yml/badge.svg)](https://github.com/nhjschulz/trlc-doc/actions/workflows/test.yml)
[![Docs](https://github.com/nhjschulz/trlc-doc/actions/workflows/pages.yaml/badge.svg?branch=main)](https://nhjschulz.github.io/trlc-doc/)
[![Project Status: WIP](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)

Configurable documentation tooling for TRLC based projects.

The trlcdoc tool is a tailored utility for converting TRLC files,
test results and LOBSTER trace reports into a static project report
website. It is driven by a configuration YAML file that defines
the project specific content to process.

 trlcdoc is not a standalone solution, but a component extending the
[trlc](https://github.com/bmw-software-engineering/trlc)
and
[BMW LOBSTER tooling](https://github.com/bmw-software-engineering/lobster)
with automated documentation generation.
An understanding of their purpose and usage is required to benefit from it.
The following 6 minute video gives you a quick overview of what trlcdoc offers:

![trlcdoc overview video](./trlcdoc-video.webp)
▶ [Watch the overview video on YouTube](https://www.youtube.com/watch?v=_ZVOgigi_ws) (6 min, AI generated)

**Status**: alpha. The configuration may change incompatibly before 1.0.0.

## Goals

The trlcdoc tool was created to simplify the documentation
generation for development projects that follow an *everything
as code* approach. Its focus is not on end-user documentation,
but on information for the development team, such as requirements, architecture,
test results and traces between them.

The trlcdoc tool aims for the following goals:

* **Portability**: Replace host system dependent scripting that
  is difficult to maintain and gets duplicated into new projects
  over and over again (bat files, bash scripts, make, ...).

* **Configurability**: Tool operation is driven by a single configuration
  file in YAML format, which makes it easy to apply it to new projects.

* **Correctness**: Analyze results of each execution step, report errors
  and stop before producing incomplete or broken results.

* **Quality**: The development of trlcdoc follows best practices from the
  V-Model. It is driven by requirements, has a documented architecture and
  high unit test code coverage. In addition, its own project documentation is
  built by itself following the "eating your own dog food" practice.

## Principle of Operation

trlcdoc provides a fixed set of steps to generate the documentation. All
steps are configured by sections in a YAML configuration file. The steps to
execute are given to trlcdoc as arguments. Without arguments, or with `all`,
trlcdoc executes all steps except `clean` and `show`.

The table below shows the supported steps. Steps always execute in this order:

| Step | Does |
|---|---|
| `clean` | Removes the output folder with all build artifacts, including the downloaded PlantUML jar. Not part of `all`. |
| `check` | Validates the configuration against the schema and checks all references. |
| `plantuml` | Uses `$PLANTUML`, a configured jar, or downloads the configured PlantUML version. |
| `tests` | Runs pytest (or a command), converts the JUnit XML into TRLC test result records. |
| `convert` | Converts each TRLC document with its pyTRLCConverter converter. |
| `trace` | Generates the lobster-trlc configs and the LOBSTER policy from `trace.levels`, creates the HTML tracing report. |
| `html` | Generates the Sphinx sources from `documents` and builds the site. |
| `show` | Opens the start page of the built site in the web browser. Not part of `all`. |

Exit codes: `0` success, `1` content findings (failed tests, missing trace
links), `2` build error. All generated files go to `paths.output`
(default `build/trlcdoc`), never into this package folder.

## Usage

### Installation

The HTML site generation needs a Java runtime for PlantUML, and
[Graphviz](https://graphviz.org) for all diagrams except sequence diagrams and
for the tracing policy diagram of the tracing report. Tracing C/C++ code needs
[doxygen](https://www.doxygen.nl). All of them must be on the `PATH`; trlcdoc
stops with an error if a step needs a missing tool.

**From PyPI:**

```bash
pip install trlcdoc
trlcdoc --help
```

**As a submodule:**

```bash
# Create a python venv (recommended)
python3 -m venv .venv
. .venv/bin/activate

# add trlcdoc to your project as a submodule
git submodule add https://github.com/nhjschulz/trlc-doc tools/trlc-doc
pip install -e tools/trlc-doc       # the submodule folder

trlcdoc --help
```

**For developing trlcdoc itself:**

```bash
pip install -e ."[test,doc,lint]"
trlcdoc --help

pytest              # unit tests
ruff check .        # lint
ruff format .       # format the code, the Tests workflow checks it
```

### Execution Examples

```bash
trlcdoc                             # all steps, uses ./trlcdoc.yaml (or a parent folder)
trlcdoc tests trace                 # selected steps only
trlcdoc clean                       # remove all build artifacts
trlcdoc clean all                   # fresh full build
trlcdoc all show                    # full build, then open the site in the browser
trlcdoc convert --format markdown   # Markdown export of the TRLC documents
trlcdoc trace --online              # tracing report linked to the repository
trlcdoc -c other.yaml check         # validate a configuration
```

## Configuration

The project configuration `trlcdoc.yaml` lives in the project root. See
[configuration.md](configuration.md) which explains every section and key with
examples. The schema of the configuration
is [trlcdoc/schema/trlcdoc.schema.json](trlcdoc/schema/trlcdoc.schema.json);
editors with YAML language support validate against it with this first line:

```yaml
# yaml-language-server: $schema=tools/trlc-doc/trlcdoc/schema/trlcdoc.schema.json
```

Without the submodule, use the published schema of your trlcdoc release
(one copy per tag `Vx.y.z`):

```yaml
# yaml-language-server: $schema=https://nhjschulz.github.io/trlc-doc/schema/V0.6.0/trlcdoc.schema.json
```

Users of Visual Studio Code can use the
[redhat.vscode-yaml](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml)
extension to get schema validation for `trlcdoc.yaml` files.

See trlcdoc's own [trlcdoc.yaml](./trlcdoc.yaml) configuration as a full example.

Key concepts:

- **documents** are the pages of the site, in table of contents order. Their
  `id` is the key used everywhere else. Types: `trlc`, `test_results`,
  `trace_report`, `html`, `rst`, `markdown`, `text`, `command`.
- **pytrlcconverter** holds the pyTRLCConverter options of a `trlc` or
  `test_results` document: the project `converter` per output format, the
  `translation` and the render configuration `render_cfg`.
  `builtin:<file>` refers to [trlcdoc/converters](trlcdoc/converters), any other
  path is relative to the project root.
- **include** lists the documents whose TRLC files are needed to resolve
  references, e.g. the requirements for the architecture.
- **trace.levels** are the LOBSTER levels. Each TRLC level names its `document`;
  the lobster-trlc inputs are derived from it and its includes.
- **tests.link** maps test results to TRLC test cases: the JUnit `property`
  if the test records one, otherwise the `output` pattern in the test output
  (e.g. Unity `TEST_MESSAGE` lines of Ceedling tests), otherwise the
  `from` -> `to` name pattern. A test recording several test cases needs
  `array: true` and a model with `relates SwTestCase [1 .. *]`. The result
  records are written into the package of the linked test cases.
- **html** customizes the site: `theme`, `extensions`, `extra_conf`, a project
  start page `index` (it owns the toctree; TRLC documents are named
  `<id>/index`), a `page_header` for every generated page, and a project Sphinx
  configuration file `conf`, executed at the end of trlcdoc's
  [conf.py](trlcdoc/sphinx/conf.py) with `PROJECT_ROOT` and `trlcdoc_links` set. In these files and in `rst`/`markdown` documents,
  `{project_root}` is replaced by the relative path from the page to the
  project root. Further placeholders insert the page name of a document or of
  all documents, e.g. for the toctree of the start page, and `trlcdoc check`
  compares that toctree with the documents (see the configuration reference,
  chapter 8).
- A TRLC or test result document without `title` takes its page title from the
  converted content.
- **PLANTUML** environment variable: a plantuml.jar or a PlantUML server URL.

The built-in TRLC converters are the project converters of
[pyTRLCConverter](https://github.com/NewTec-GmbH/pyTRLCConverter) (`tools/converter`),
for its 3.x API. pyTRLCConverter also determines the trlc version.

## Trlcdoc Documentation

The trlcdoc project documentation is itself being generated using trlcdoc.
The latest version is available online at
[https://nhjschulz.github.io/trlc-doc/](https://nhjschulz.github.io/trlc-doc/).

Run the following commands to build it locally:

```bash
# setup virtual environment and install trlcdoc

python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[test,doc]"

# generate documentation
trlcdoc -c trlcdoc.yaml
```

The website is written to `build/trlcdoc/html`.

## Project Integration Examples

The [examples](examples) folder contains the same small program, *Greeter*, in
several languages, each with its own toolchain. All examples share the same
requirements, architecture and test cases, so they show side by side how trlcdoc
is configured for a toolchain. Each example builds its complete documentation
site with a single `trlcdoc` call in its folder.

| Example | Language | Build and tests | Code tracing | Test result link | Coverage |
| --- | --- | --- | --- | --- | --- |
| [c-doxygen-ceedling](examples/c-doxygen-ceedling/README.md) | C | CMake, Ceedling (Unity, CMock) | doxygen, lobster-doxygen | test output | Ceedling gcov plugin, gcovr |
| [cpp-doxygen-gtest](examples/cpp-doxygen-gtest/README.md) | C++ | CMake, googletest | doxygen, lobster-doxygen | test property | gcovr |
| [python-lobster-pytest](examples/python-lobster-pytest/README.md) | Python | pip, pytest | lobster-python | test property | pytest-cov |

- **Code tracing:** how the code names the requirements it implements, e.g.
  doxygen `@implements{...}` tags in C and C++, `# lobster-trace:` comments in
  Python. See [6.2](configuration.md#62-implementation-levels) of the
  configuration reference.
- **Test result link:** how a test result finds its TRLC test case, by a test
  property or by a line in the test output. See
  [5.3](configuration.md#53-link-from-test-results-to-test-cases).

trlcdoc documents itself the same way as the Python example. Unlike the examples, which
keep trlcdoc's default look, its own site is customized in the `html` section:

- the [Read the Docs theme](https://sphinx-rtd-theme.readthedocs.io) instead of
  the default `haiku`, and the trlcdoc logo (`project.logo`),
- an API reference generated with sphinx-autoapi, with source links to the
  repository (`sphinx.ext.linkcode`), and a full-width page layout, both set up
  in the project Sphinx configuration
  [doc/sphinx/sphinx_conf.py](doc/sphinx/sphinx_conf.py).

The theme and the API reference need the `doc` extra: `pip install -e ".[doc]"`.

## License

GPL-3.0-or-later, see [LICENSE](LICENSE).