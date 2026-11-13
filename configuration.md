# trlcdoc Configuration Reference <!-- omit from toc -->

This document explains the trlcdoc project configuration file `trlcdoc.yaml`
section by section: what every key means, which step uses it, and what changes
in the generated documentation when you set it.

The formal definition is the JSON schema
[trlcdoc/schema/trlcdoc.schema.json](trlcdoc/schema/trlcdoc.schema.json). This
document adds the behavior behind the keys.

- [1. Overview](#1-overview)
  - [1.1 Where the file lives](#11-where-the-file-lives)
  - [1.2 Top level anatomy](#12-top-level-anatomy)
  - [1.3 Steps and the sections they use](#13-steps-and-the-sections-they-use)
  - [1.4 Validation](#14-validation)
  - [1.5 A minimal configuration](#15-a-minimal-configuration)
- [2. project](#2-project)
- [3. paths](#3-paths)
- [4. documents](#4-documents)
  - [4.1 Common keys](#41-common-keys)
  - [4.2 type: trlc](#42-type-trlc)
  - [4.3 type: test\_results](#43-type-test_results)
  - [4.4 type: trace\_report](#44-type-trace_report)
  - [4.5 type: html](#45-type-html)
  - [4.6 type: command](#46-type-command)
  - [4.7 type: rst and type: markdown](#47-type-rst-and-type-markdown)
  - [4.8 type: text](#48-type-text)
  - [4.9 pytrlcconverter: the pyTRLCConverter options](#49-pytrlcconverter-the-pytrlcconverter-options)
- [5. tests](#5-tests)
  - [5.1 runner: pytest](#51-runner-pytest)
  - [5.2 runner: command](#52-runner-command)
  - [5.3 link: from test results to test cases](#53-link-from-test-results-to-test-cases)
  - [5.4 The generated test result records](#54-the-generated-test-result-records)
- [6. trace](#6-trace)
  - [6.1 Requirement levels](#61-requirement-levels)
  - [6.2 Implementation levels](#62-implementation-levels)
  - [6.3 trace\_to and requires](#63-trace_to-and-requires)
  - [6.4 Online tracing report](#64-online-tracing-report)
- [7. plantuml](#7-plantuml)
- [8. html](#8-html)
  - [8.1 theme, extensions and extra\_conf](#81-theme-extensions-and-extra_conf)
  - [8.2 conf: project Sphinx configuration](#82-conf-project-sphinx-configuration)
  - [8.3 index: project start page](#83-index-project-start-page)
  - [8.4 page\_header](#84-page_header)
  - [8.5 The {project\_root} placeholder](#85-the-project_root-placeholder)
- [9. Generated files](#9-generated-files)
- [10. Typical errors](#10-typical-errors)
- [11. Complete examples](#11-complete-examples)

## 1. Overview

### 1.1 Where the file lives

trlcdoc reads the file given with `-c`/`--config`. Without this option it
searches `trlcdoc.yaml` in the current folder and then in each parent folder,
so you can run `trlcdoc` from any sub folder of the project.

**The folder of the configuration file is the project root.** Every relative
path in the file is resolved against it, independent of the folder you start
trlcdoc from. Tests, converters and trace tools also run with the project root
as working directory.

Put this line at the top of the file to get completion and validation in
editors with YAML language support (e.g. VS Code with the Red Hat YAML
extension). The path is relative to the configuration file:

```yaml
# yaml-language-server: $schema=tools/trlc-doc/trlcdoc/schema/trlcdoc.schema.json
```

A project without the submodule can reference the published schema instead.
Each release tag `Vx.y.z` has its own copy, so pick the one that matches the
trlcdoc version you use (the configuration may change incompatibly before 1.0):

```yaml
# yaml-language-server: $schema=https://nhjschulz.github.io/trlc-doc/schema/V0.3.0/trlcdoc.schema.json
```

The schema of the current `main` branch is available without a version:
`https://nhjschulz.github.io/trlc-doc/schema/trlcdoc.schema.json`.

### 1.2 Top level anatomy

```yaml
project:    # required - name, author, copyright, repository, logo, favicon
paths:      # required - TRLC model folder and output folder
documents:  # required - the pages of the site, in table of contents order
tests:      # optional - test execution and the link of test results to TRLC test cases
trace:      # optional - LOBSTER trace levels and their relations
plantuml:   # optional - PlantUML jar or version to download
html:       # optional - Sphinx theme, extensions and site customization
```

No other top level keys are allowed. Unknown keys are reported as errors, which
catches typos like `document:` instead of `documents:`.

### 1.3 Steps and the sections they use

trlcdoc works in steps. They always run in this order, no matter in which order
you name them on the command line:

| Step       | Uses                                    | Produces                                    |
|------------|-----------------------------------------|---------------------------------------------|
| `clean`    | `paths.output`                          | Removes the output folder                   |
| `check`    | the whole file                          | Nothing, validates the configuration        |
| `plantuml` | `plantuml`                              | PlantUML jar, `PLANTUML` environment variable |
| `tests`    | `tests`                                 | JUnit XML, coverage report, TRLC test results |
| `convert`  | `documents` of type `trlc`/`test_results`, `paths.trlc_model` | Converted reStructuredText (or Markdown) |
| `trace`    | `trace`, `documents`, `project.repository` | LOBSTER files and the HTML tracing report |
| `html`     | `documents`, `project`, `html`          | The HTML site                               |
| `show`     | `paths.output`                          | Nothing, opens `html/index.html` in the web browser |

`trlcdoc` without arguments runs `all`: every step except `clean` and `show`. It leaves
out `tests` if there is no `tests` section and `trace` if there is no `trace`
section. `convert` and `html` always run `plantuml` first.

`show` opens the start page of the built site. Under WSL it uses the Windows
default browser (`wslview` or `explorer.exe`), otherwise Python's `webbrowser`
module, which the `BROWSER` environment variable can override. Without a built
site or without a web browser it stops with exit code `2`.

Exit codes: `0` success, `1` content findings (failed tests, missing trace
links), `2` build or configuration error.

### 1.4 Validation

The configuration is checked in two stages before any step runs, including the
`check` step:

1. **Schema validation**: types, required keys, allowed keys per document
   type, id patterns.
2. **Reference checks** that the schema cannot express:
   - document ids and trace level names are unique,
   - `include` and `trace.levels[].document` refer to documents of type `trlc`
     or `test_results`,
   - `trace_to` and `requires` refer to defined levels,
   - the converter, translation and render configuration files of the
     `pytrlcconverter` options exist,
   - `html.conf`, `html.index` and `html.page_header` files exist,
   - a `test_results` document or a `tests:coverage` source has a `tests` section,
   - a `trace_report` document has a `trace` section,
   - `paths.output` is neither inside the trlcdoc package nor the project root
     or one of its parents.

All problems are reported at once. Run `trlcdoc check` after every change of
the configuration.

### 1.5 A minimal configuration

The smallest useful configuration converts one folder of TRLC requirements into
an HTML site:

```yaml
project:
  name: example
  author: Jane Doe
  copyright: "2026, Jane Doe"

paths:
  trlc_model: trlc/model

documents:
  - id: sw_requirements
    title: SW Requirements
    type: trlc
    source: trlc/swe-req
    pytrlcconverter:
      converter:
        rst: builtin:req2rst.py
```

`trlcdoc` runs `check`, `plantuml`, `convert` and `html` and writes the site
to `build/trlcdoc/html`. The following chapters add tests, tracing and site
customization step by step.

## 2. project

Project metadata for the HTML site and the online tracing report.

```yaml
project:
  name: pyTRLCConverter
  version: "3.0.0"
  author: NewTec GmbH
  copyright: 2024 - 2026, NewTec GmbH
  repository: https://github.com/NewTec-GmbH/pyTRLCConverter
  logo: doc/images/NewTec_Logo.png
  favicon: doc/images/favicon.ico
```

| Key          | Required | Default | Meaning and impact |
|--------------|----------|---------|--------------------|
| `name`       | yes      |         | Sphinx `project`. Appears in the page header, the browser title of every page and in the heading `<name> documentation` of the generated start page. |
| `version`    | no       | none    | Sphinx `version` and `release`. Follows the name in the page header, the browser title and the start page heading: `<name> <version> documentation`. Quote it (`"1.0"`): YAML reads an unquoted `1.0` as a number, which the schema rejects. |
| `author`     | yes      |         | Sphinx `author`. |
| `copyright`  | yes      |         | Sphinx `copyright`, shown in the page footer. Quote it if it contains a colon or starts with a number followed by special characters. |
| `repository` | no       | `auto`  | Repository URL. Used by `trlcdoc trace --online` to turn the file references of the tracing report into links to the repository, and for the links of Markdown pages to project files ([4.7](#47-type-rst-and-type-markdown)). `auto` takes the URL from `git remote get-url origin`. SSH URLs (`git@host:owner/repo.git`) are converted to HTTPS, a trailing `.git` is removed. |
| `logo`       | no       | none    | Image file shown by the theme as site logo (Sphinx `html_logo`). |
| `favicon`    | no       | none    | Browser tab icon (Sphinx `html_favicon`). |

Each page footer also shows the date of the build and the git commit it was
built from, if the project is a git repository. This needs no configuration.

## 3. paths

```yaml
paths:
  trlc_model: trlc/model
  output: build/trlcdoc
```

| Key          | Required | Default         | Meaning and impact |
|--------------|----------|-----------------|--------------------|
| `trlc_model` | yes      |                 | Folder with the TRLC model files (`.rsl`). It is passed as include to every pyTRLCConverter run and as input to every lobster-trlc run, so all documents and trace levels can resolve the record types. |
| `output`     | no       | `build/trlcdoc` | Folder for everything trlcdoc generates. trlcdoc never writes anywhere else, except for files your own test or document commands write. |

**Impact of `output`:** `trlcdoc clean` deletes this folder completely,
including the downloaded PlantUML jar. Therefore it must not be the project
root or one of its parents, and it must not be inside the trlcdoc package.
Add it to `.gitignore`. Chapter [9](#9-generated-files) shows its content.

## 4. documents

`documents` is a list of the pages of the HTML site. **The list order is the
table of contents order** of the generated start page and the order of the
previous/next links.

Each document has a `type`. The type decides where the content comes from,
which other keys are allowed, and which steps work on it:

| `type`         | Content                                         | Required keys                | Optional keys |
|----------------|-------------------------------------------------|------------------------------|---------------|
| `trlc`         | TRLC records converted by pyTRLCConverter       | `source`, `pytrlcconverter`  | `title`, `include` |
| `test_results` | TRLC records generated from the test results    | `pytrlcconverter`            | `title`, `include` |
| `trace_report` | The LOBSTER HTML tracing report                 | `title`                      |               |
| `html`         | An existing HTML folder, e.g. a coverage report | `title`, `source`            |               |
| `command`      | An HTML folder generated by an external tool    | `title`, `command`, `output` |               |
| `rst`          | A project owned reStructuredText page           | `source`                     | `title`       |
| `markdown`     | A project owned Markdown page                   | `source`                     | `title`       |
| `text`         | A plain text file shown literally               | `title`, `source`            |               |

Every document also requires `id` and `type`. Keys not listed for a type are
rejected.

### 4.1 Common keys

| Key     | Meaning and impact |
|---------|--------------------|
| `id`    | Unique key of the document. Lower case letters, digits and `_`, starting with a letter (`sw_requirements`). It names the page and the output folders (`convert/rst/<id>`), and other parts of the configuration refer to the document by it (`include`, `trace.levels[].document`). Changing it changes the page URL. |
| `title` | Page heading and table of contents entry. trlcdoc writes it as top level heading above the content, except for `rst` and `markdown` pages ([4.7](#47-type-rst-and-type-markdown)). |
| `type`  | One of the types above. |

**Page names:** documents of type `trlc` and `test_results` become the page
`<id>/index.html`, all others `<id>.html`. The folder per TRLC document keeps
the converted pages and their diagram images together, so relative image
paths work. This matters when you write your own start page
([8.3](#83-index-project-start-page)) or link to pages from outside.

### 4.2 type: trlc

A folder of `.trlc` files, converted with a pyTRLCConverter project converter
in the `convert` step and included into one HTML page in the `html` step.

```yaml
  - id: sw_architecture
    title: SW-Architecture
    type: trlc
    source: trlc/swe-arch
    include: [sw_requirements]
    pytrlcconverter:
      converter:
        rst: builtin:req2rst.py
        markdown: builtin:req2markdown.py
      translation: builtin:translation.json
      render_cfg: tools/converter/renderCfg.json
```

| Key           | Meaning and impact |
|---------------|--------------------|
| `source`      | Folder with the `.trlc` files of this document (pyTRLCConverter `--source`). All files in it are converted; each converted file is included into the page in file name order. |
| `include`     | Ids of other `trlc` or `test_results` documents whose records are referenced here, e.g. the requirements an architecture item `satisfies`. Their files are passed as `--include` (to resolve the references) and as `--exclude` (so they are not rendered on this page). Includes are transitive: including `sw_test` also includes what `sw_test` includes. Without the include, the conversion fails with an unresolved reference. |
| `pytrlcconverter` | The options of the pyTRLCConverter run: converter, translation and render configuration, see [4.9](#49-pytrlcconverter-the-pytrlcconverter-options). |
| `title`       | Optional for this type. **Without `title`**, trlcdoc writes no heading, and the first heading of the converted content is the page title. Use this if your converter writes its own document heading, otherwise the page shows two headings. |

PlantUML diagrams referenced by the records are rendered by the converter
during `convert`, so this step needs the PlantUML jar (it is provided
automatically).

### 4.3 type: test_results

The test results of the `tests` step, converted like a `trlc` document. It has
no `source`: the records come from `<output>/tests/results`, which the `tests`
step generates (see [5.4](#54-the-generated-test-result-records)).

```yaml
  - id: sw_test_results
    title: SW-Test Results
    type: test_results
    include: [sw_test]
    pytrlcconverter:
      converter:
        rst: builtin:create_test_report_in_rst.py
        markdown: builtin:create_test_report_in_markdown.py
```

- Requires a `tests` section.
- `include` must name the document with the TRLC test cases, because every
  result record references its test case.
- Run the `tests` step before `convert`. `all` does this; `trlcdoc convert`
  alone fails with *No test results ... run the tests step first* on a fresh
  output folder.
- Without `title`, the heading written by the converter is the page title, as
  for `trlc`.

### 4.4 type: trace_report

Embeds the LOBSTER HTML tracing report generated by the `trace` step.

```yaml
  - id: sw_tracing_report
    title: Software Tracing Report
    type: trace_report
```

Requires a `trace` section. Only `id`, `title` and `type` are allowed. The
report is included as raw HTML into the page, so it gets the site navigation
around it. Run `trace` before `html`.

### 4.5 type: html

An existing HTML folder with an `index.html`. The folder is copied into the
site as `<id>/`, and the page shows its `index.html` in an iframe.

```yaml
  - id: coverage_report
    title: Coverage Report
    type: html
    source: tests:coverage
```

| Key      | Meaning and impact |
|----------|--------------------|
| `source` | HTML folder, relative to the project root. The special value `tests:coverage` refers to the coverage report of the `tests` step (`tests.coverage`, or `<output>/tests/coverage` for pytest), and requires a `tests` section. |

The folder must exist when the `html` step runs, otherwise it fails with
*... index.html not found, generate it first*.

### 4.6 type: command

Like `html`, but the folder is generated by an external tool, e.g. an API
documentation generator. The command runs at the start of the `html` step.

```yaml
  - id: api
    title: API Reference
    type: command
    command: [doxygen, doc/Doxyfile]
    output: build/doxygen/html
```

| Key       | Meaning and impact |
|-----------|--------------------|
| `command` | The program and its arguments as a list, without a shell. It runs in the project root. A non-zero exit code stops the build. To use shell features, call the shell explicitly: `[bash, -c, "..."]`. |
| `output`  | The HTML folder the command writes, relative to the project root. It must contain `index.html`. It is copied into the site as `<id>/`. |

### 4.7 type: rst and type: markdown

A page you write yourself, for content that is not TRLC: a user manual,
a detailed design, release notes.

```yaml
  - id: sw_detail_design
    type: rst
    source: doc/sphinx/sw_detail_design.rst

  - id: notes
    type: markdown
    source: doc/release_notes.md
```

- `source` is the `.rst` or `.md` file. It is copied into the Sphinx source
  folder as `<id>.rst` or `<id>.md`; Markdown is rendered with MyST.
- **The file is used as is:** trlcdoc adds no heading and no page header
  ([8.4](#84-page_header)), the page shows the first heading of the file.
- **A configured `title`** is the page title in the table of contents, the
  navigation links and the browser title, e.g. `README` for a `README.md` whose
  first heading is the project name. Without `title`, the first heading of the
  file is used there as well.
- The file is copied, so relative paths in it would point into the output
  folder. In **Markdown** files, relative links and images are resolved against
  the location of the Markdown file in the project, so a file that renders in
  the repository renders in the site as well:

  | Relative target | Becomes |
  |---|---|
  | An image | The image, copied into the site. |
  | The `source` of a document of type `trlc`, `rst`, `markdown` or `text` | A link to that page. An anchor (`file.md#section`) is kept. |
  | Any other project file or folder | A link to it in the repository at the commit the site is built from (`<repository>/blob/<commit>/<path>`, `tree` for folders), see `project.repository`. |
  | Any other project file or folder, without git repository or repository URL | Plain text, with a warning. |
  | A target that does not exist, or lies outside the project | Left to MyST, which warns about it. |

  In reStructuredText files, use the
  [`{project_root}`](#85-the-project_root-placeholder) placeholder for images
  and includes from the project:
  `.. image:: {project_root}/doc/images/context.svg`.
- **`placeholders: false`** copies the file without replacing the
  placeholder, for a page that explains it, like this configuration reference.

### 4.8 type: text

A plain text file shown literally, e.g. the license.

```yaml
  - id: license
    title: License information
    type: text
    source: LICENSE
```

### 4.9 pytrlcconverter: the pyTRLCConverter options

Documents of type `trlc` and `test_results` are converted with
pyTRLCConverter. The `pytrlcconverter` block holds the options of this run.
They apply only to these two types; the other document types do not accept the
block.

```yaml
    pytrlcconverter:
      converter:
        rst: builtin:req2rst.py
        markdown: builtin:req2markdown.py
      translation: builtin:translation.json
      render_cfg: tools/converter/renderCfg.json
```

| Key           | Required | pyTRLCConverter option | Meaning and impact |
|---------------|----------|------------------------|--------------------|
| `converter`   | yes      | `--project`            | Project converter per output format. `rst` is required, it is used for the HTML site. `markdown` is only used by `trlcdoc convert --format markdown`; a document without it is skipped in that run. |
| `translation` | no       | `--translation`        | JSON file mapping attribute names to the names shown in the output, e.g. `verification_criteria` to *Verification Criteria*. Without it, the attribute names of the TRLC model are shown. |
| `render_cfg`  | no       | `--renderCfg`          | JSON file declaring the format of attribute values (`md` CommonMark, `gfm` GitHub Flavored Markdown, or `rst`), selected by package, type and attribute name patterns. Matching values are rendered as rich text (lists, tables, emphasis, links); all others are escaped and shown as plain text. |

A render configuration looks like this (see the pyTRLCConverter documentation
for all options):

```json
{
    "renderCfg": [
        {"package": "SwRequirements", "type": "SwReq", "attribute": "description", "format": "md"}
    ]
}
```

The values of `converter`, `translation` and `render_cfg` are file references
in one of two forms:

- `builtin:<file>`: a file shipped with trlcdoc in
  [trlcdoc/converters](trlcdoc/converters).
- any other value: a path relative to the project root, for project owned
  converters.

The built-in files are the project converters of pyTRLCConverter
(`tools/converter`) for its 3.x API:

| File                                   | Use for |
|----------------------------------------|---------|
| `req2rst.py`, `req2markdown.py`        | Requirements, constraints and architecture records |
| `tc2rst.py`, `tc2markdown.py`          | Test case records |
| `create_test_report_in_rst.py`, `create_test_report_in_markdown.py` | Test result records (`test_results` documents) |
| `translation.json`                     | Display names of the attributes used by these converters |
| `renderCfg.json`                       | Renders the `description` of `Info`, `SwReq`, `SwReqNonFunc`, `SwConstraint`, `SwArchSpec` and `SwTestCase` records and the `verification_criteria` of `SwReq` and `SwArchSpec` records as GitHub Flavored Markdown |

They expect the record types of the NewTec TRLC model (`SwReq`,
`SwConstraint`, `SwArchSpec`, `SwTestCase`, `SwTestCaseResult`, and
`Generic.PlantUML` for diagrams). If your model differs, copy the converters
into your project, adapt them and reference them by path.

Each converter run looks like this, which helps when a conversion fails:

```text
pyTRLCConverter --source=<source> --include=<trlc_model>
                --include=<included source> --exclude=<included source> ...
                --out=<output>/convert/<format>/<id> --project=<converter>
                [--translation=<file>] [--renderCfg=<file>] <format>
```

## 5. tests

Runs the tests, keeps the JUnit XML and coverage report, and converts the
results into TRLC records, so they can be shown as a document and traced to
the test cases.

```yaml
tests:
  runner: pytest
  args: [tests, -v, --cov=src]
  link:
    property: lobster-trace
    from: "test_{name}"
    to: "SwTests.tc_{name}"
```

| Key        | Required              | Meaning and impact |
|------------|-----------------------|--------------------|
| `runner`   | yes                   | `pytest` or `command`. |
| `args`     | no                    | pytest arguments (runner `pytest` only). |
| `command`  | runner `command`      | The test command (runner `command` only). |
| `junit`    | runner `command`      | JUnit XML file the command writes. |
| `coverage` | no                    | HTML coverage folder, if not the default. |
| `link`     | yes                   | How test results are linked to TRLC test cases. |

A failed test is a content finding: the build continues, the result is shown
as `FAILED`, and trlcdoc exits with `1`.

### 5.1 runner: pytest

trlcdoc runs pytest with the Python interpreter trlcdoc itself runs in, so
install trlcdoc and your project into the same virtual environment:

```text
python -m pytest <args> -o junit_family=xunit1 --junitxml=<output>/tests/junit.xml
                 [--cov-report=term --cov-report=html:<coverage folder>]
```

- `args` typically name the test folder and options like `-v`.
- **An argument starting with `--cov` enables the HTML coverage report**
  (pytest-cov must be installed). It is written to `tests.coverage` if set,
  otherwise to `<output>/tests/coverage`. Refer to it with a document of type
  `html` and `source: tests:coverage`.
- The coverage data file `.coverage` is kept in `<output>/tests`, not in the
  project root.
- pytest exit codes 0 (passed) and 1 (tests failed) are accepted; any other
  code (e.g. usage error, no tests collected) is a build error.

### 5.2 runner: command

For tests that are not run by pytest, e.g. C unit tests built with CMake. The
command must write a JUnit XML file.

```yaml
tests:
  runner: command
  command: [bash, tools/run_unit_tests.sh, build/junit.xml]
  junit: build/junit.xml
  coverage: build/coverage/html
  link:
    from: "test_{name}"
    to: "SwTests.tc_{name}"
```

- `command` runs in the project root, without a shell. Its exit code is
  ignored, because test tools usually report failed tests with a non-zero
  code; the results are taken from the JUnit file.
- `junit` is the JUnit XML file, relative to the project root. If it is
  missing after the command, the step fails.
- `coverage` is the HTML coverage folder the command writes, if any.

### 5.3 link: from test results to test cases

Every executed test must be linked to at least one TRLC test case. trlcdoc
tries three ways for each JUnit test case, in this order, and uses the first
one that finds a test case:

1. **Property:** the JUnit test case has properties named `link.property`
   (default `lobster-trace`). Their values are the qualified test case ids. In
   pytest a test records them with the `record_property` fixture:

   ```python
   def test_parse_header(record_property):
       # lobster-trace: SwTests.tc_parse_header
       record_property("lobster-trace", "SwTests.tc_parse_header")
       ...
   ```

2. **Output:** the test writes the test case ids to its output, and
   `link.output` is the pattern to find them, with an `{id}` placeholder for
   the qualified test case id. Every matching output line links one test case;
   an id written several times is linked once. trlcdoc reads the JUnit
   `<system-out>` of the test case and of its test suite:

   - The `<system-out>` of a **test case** (e.g. pytest) belongs to that test.
   - The `<system-out>` of a **test suite** (e.g. Ceedling) holds the output of
     all its tests. Only lines in the Unity format
     `<file>:<line>:<test>:<level>: <message>` are used, the `<test>` field
     names the test the line belongs to.

   This is the way for C unit tests with Unity and Ceedling, which have no
   test properties. A macro writes the test case ids with `TEST_MESSAGE`:

   ```c
   #define LOBSTER_TRACE(_id)  TEST_MESSAGE("lobster-trace: " _id)

   void test_Greeter_morningGreeting(void)
   {
       LOBSTER_TRACE("SwTests.tc_greet_morning_time_greeting");
       LOBSTER_TRACE("SwTests.tc_greet_user_name");
       ...
   }
   ```

   Ceedling's built-in `junit` report writes these lines into the suite
   output:

   ```text
   test/test_Greeter.c:42:test_Greeter_morningGreeting:INFO: lobster-trace: SwTests.tc_greet_user_name
   ```

   Enable the report in `project.yml` and point `tests.junit` to it:

   ```yaml
   # project.yml (Ceedling)
   :plugins:
     :enabled:
       - report_tests_log_factory
   :report_tests_log_factory:
     :reports:
       - junit
   ```

   ```yaml
   # trlcdoc.yaml
   tests:
     runner: command
     command: [ceedling, test:all]
     junit: build/artifacts/test/junit_tests_report.xml
     link:
       output: "lobster-trace: {id}"
       array: true
   ```

   Write the trace messages at the start of the test: a test that aborts
   before them has no link.

3. **Name pattern:** if the test has neither, its name is matched
   against `link.from`, and the `{name}` part is inserted into `link.to`. With
   `from: "test_{name}"` and `to: "SwTests.tc_{name}"`, the test
   `test_parse_header` is linked to `SwTests.tc_parse_header`. pytest
   parametrization is removed first: `test_parse_header[v2]` is matched as
   `test_parse_header`.

| Key        | Default         | Meaning and impact |
|------------|-----------------|--------------------|
| `property` | `lobster-trace` | Name of the JUnit property holding the test case id. |
| `output`   |                 | Pattern searched in the test output, must contain `{id}`. `{id}` matches a qualified id `Package.record`. |
| `from`     |                 | Test function name pattern, must contain `{name}`. `{name}` matches letters, digits and `_`. |
| `to`       |                 | Qualified test case id pattern `Package.record`, must contain `{name}`. |
| `array`    | `false`         | Write the linked test cases as a list. Needed as soon as one test records more than one test case. |

`link` needs `output`, or `from` and `to`, or both. The property is always
tried first.

Tests that cannot be linked are a build error that lists them all. Fix them by
recording the property, writing the test case id to the output or renaming the
test. Skipped tests are left out.

**`array`:** a test recording several test cases is an error unless `array:
true` is set. With `array`, every result record gets a list
(`relates = [SwTests.a, SwTests.b]`), even for one test case, so the TRLC
model must declare the component as array:

```text
type SwTestCaseResult {
    name    String
    result  SwTestResult
    relates SwTestCase [1 .. *]
}
```

Without `array`, the model uses a single reference: `relates SwTestCase`.

### 5.4 The generated test result records

The `tests` step writes `<output>/tests/results/sw_test_result_report.trlc`:

```text
package SwTests

section "SW Test Results" {

    SwTestCaseResult test_parse_header_result {
        name = "test_parse_header"
        result = SwTestResult.PASSED
        relates = SwTests.tc_parse_header
    }

}
```

**The records are written into the package of the linked test cases**, here
`SwTests`. All linked test cases must belong to one package, and every id must
be qualified with its package; otherwise the `tests` step fails and lists the
tests. Your TRLC model must therefore define, in the package of the test
cases:

```text
enum SwTestResult {
    FAILED
    PASSED
}

type SwTestCaseResult {
    name    String
    result  SwTestResult
    relates SwTestCase          // or SwTestCase [1 .. *] with link.array
}
```

The record names are the test names with `_result` appended (with a number
appended for duplicates). These records are the input of the `test_results`
document and of a trace level with `document: <test_results id>`.

## 6. trace

Defines the LOBSTER trace levels. The `trace` step extracts the items of each
level, writes the LOBSTER policy from the relations, and creates the HTML
tracing report `<output>/trace/tracing_report.html`.

```yaml
trace:
  namespace: req
  levels:
    - name: SW Requirement
      document: sw_requirements
      record_type: SwRequirements.SwReq
      requires: [SW Test Case, SW Architecture]

    - name: SW Architecture
      document: sw_architecture
      record_type: SwArch.SwArchSpec
      tags: [satisfies]
      trace_to: [SW Requirement]
```

| Key         | Default | Meaning and impact |
|-------------|---------|--------------------|
| `namespace` | `req`   | LOBSTER namespace of all TRLC items. An item is identified as `<namespace> <Package>.<record>`, e.g. `req SwRequirements.sw_req_cli`. Keep the default: `lobster-python` reads `# lobster-trace: Package.record` comments into the `req` namespace, so code can only trace to TRLC items in that namespace. |
| `levels`    |         | The levels, see below. Their order is the order in the report. |

After the report, trlcdoc prints every item that is not traced as required:

```text
Tracing:
  SW Requirement: 19 items, 1 not traced
    req SwRequirements.sw_req_cli
  SW Architecture: 9 items, 0 not traced
```

Untraced items are content findings: the report is still created, and trlcdoc
exits with `1`.

### 6.1 Requirement levels

The default `kind: requirements` takes the records of one record type from a
TRLC document (extracted with lobster-trlc).

```yaml
    - name: SW Test Result
      document: sw_test_results
      record_type: SwTests.SwTestCaseResult
      tags: [relates]
      description_fields: [name]
      trace_to: [SW Test Case]
```

| Key                  | Default         | Meaning and impact |
|----------------------|-----------------|--------------------|
| `name`               |                 | Level name, shown in the report and used in `trace_to`/`requires`. |
| `kind`               | `requirements`  | Omit for TRLC levels. |
| `document`           |                 | Id of a `trlc` or `test_results` document. Its `source` and its `include` documents are the input, together with `paths.trlc_model`. |
| `record_type`        |                 | `Package.Type` of the records forming this level. Records of other types in the same document are ignored, so several levels can use the same document (e.g. `SwReq` and `SwConstraint` from `sw_requirements`). |
| `tags`               | `[]`            | Record components holding the references to the items of the levels in `trace_to`, e.g. `satisfies`, `verifies`, `relates`. Without tags, the items have no outgoing links. |
| `description_fields` | `[description]` | Record components shown as item text in the report. Test result records have no `description`, use `[name]`. |
| `trace_to`           | `[]`            | Levels this level links to, see [6.3](#63-trace_to-and-requires). |
| `requires`           | `[]`            | Levels that must link to this level, see [6.3](#63-trace_to-and-requires). |

### 6.2 Implementation levels

`kind: implementation` takes the items from source code. The only extractor is
`lobster-python`: every function and method is an item, linked by
`# lobster-trace:` comments.

```yaml
    - name: SW Code
      kind: implementation
      extractor: lobster-python
      sources: [src/pyTRLCConverter]
      trace_to: [SW Requirement]
```

```python
def convert_section(self, section, level):
    # lobster-trace: SwRequirements.sw_req_rst_section
    ...
```

| Key         | Meaning and impact |
|-------------|--------------------|
| `extractor` | `lobster-python`. |
| `sources`   | Files or folders to scan, relative to the project root. |

`document`, `record_type` are not allowed here; `extractor` and `sources` are
not allowed for requirement levels. `tags` and `description_fields` have no
effect.

Use a second implementation level for test code (`sources: [tests]`,
`trace_to: [SW Test Case]`) to check that every test function traces to a test
case.

### 6.3 trace_to and requires

These two keys become the LOBSTER policy and decide which items are reported
as not traced:

- **`trace_to: [X]`** means the items of this level link to items of level `X`
  (up). Every item of this level then needs at least one such link, otherwise
  it is reported with *missing up reference*. The links come from the `tags`
  components (TRLC) or the `lobster-trace` comments (code).
- **`requires: [X, Y]`** means every item of this level must be linked from
  level `X` *and* from level `Y` (down). The listed levels must have this
  level in their `trace_to`, otherwise LOBSTER reports an error.
- **Without `requires`**, LOBSTER requires a link from *every* level that has
  this level in its `trace_to`. With `requires`, only the listed levels are
  required. List them explicitly anyway, it documents the expectation and
  keeps the result stable when you add a level.

Example: the levels of [11](#11-complete-examples) give this chain:

```text
SW Requirement  <-- satisfies --  SW Architecture
SW Requirement  <-- verifies  --  SW Test Case  <-- relates --  SW Test Result
SW Requirement  <-- lobster-trace --  SW Code
```

A requirement with `requires: [SW Code, SW Test Case, SW Architecture]` is
only fully traced when an architecture item satisfies it, a test case
verifies it, and a function references it. A test case with `requires: [SW
Test Result]` must have been executed.

Generated files in `<output>/trace` help with debugging: one
`<level>.yaml`/`<level>.lobster` per level and the policy
`lobster-report.conf`.

### 6.4 Online tracing report

By default the report links each item to its local file. `trlcdoc trace
--online` (or `trlcdoc --online`) links to the files in the repository at the
current commit instead, which is what you want for a published site. This
uses `project.repository` and needs a git repository with the commit pushed.

## 7. plantuml

PlantUML renders the diagrams in TRLC records (during `convert`) and in
`.. uml::` directives of the site (during `html`). Java is required unless you
use a PlantUML server.

```yaml
plantuml:
  version: "1.2026.1"
```

| Key       | Default    | Meaning and impact |
|-----------|------------|--------------------|
| `version` | `1.2024.8` | PlantUML release downloaded from GitHub into `<output>/plantuml` if no jar is configured. Quote it, so YAML keeps it a string. The download happens once; `clean` removes it. |
| `jar`     | none       | Use this `plantuml.jar` (relative to the project root) instead of downloading one. |

The jar is selected in this order:

1. the `PLANTUML` environment variable, if it is an existing jar file or a
   `http(s)://` PlantUML server URL,
2. `plantuml.jar`,
3. the download of `plantuml.version`.

trlcdoc sets `PLANTUML` for the converters and Sphinx. Set it yourself to use a
company wide jar or server without changing the configuration, e.g. in CI:
`PLANTUML=https://www.plantuml.com/plantuml`.

## 8. html

Settings of the Sphinx site. All keys are optional.

```yaml
html:
  theme: sphinx_rtd_theme
  extensions:
    - sphinx_rtd_theme
    - sphinx.ext.autodoc
  extra_conf:
    html_theme_options:
      navigation_depth: 3
  conf: doc/sphinx/sphinx_conf.py
  index: doc/sphinx/index.rst
  page_header: doc/sphinx/page_header.rst
```

### 8.1 theme, extensions and extra_conf

| Key          | Default | Meaning and impact |
|--------------|---------|--------------------|
| `theme`      | `haiku` | Sphinx `html_theme`. trlcdoc's `custom.css` is only applied to `haiku`. Other themes must be installed in the environment, and usually also listed in `extensions` (e.g. `sphinx_rtd_theme`). |
| `extensions` | `[]`    | Sphinx extensions added to the ones trlcdoc always loads (`myst_parser` for Markdown, `sphinxcontrib.plantuml` for diagrams). They must be installed in the environment. |
| `extra_conf` | `{}`    | Sphinx configuration values, set as variables in trlcdoc's `conf.py` (see [8.2](#82-conf-project-sphinx-configuration)). Any value that YAML can express: strings, numbers, lists, dicts. |

`extra_conf` is the simplest way to set Sphinx options:

```yaml
html:
  extra_conf:
    html_title: "Example Project"
    html_show_sourcelink: false
    html_theme_options:
      collapse_navigation: false
```

Use `conf` instead when a value needs Python, e.g. a computed path or a
`setup()` hook.

### 8.2 conf: project Sphinx configuration


The `html` step copies
[trlcdoc/sphinx/conf.py](trlcdoc/sphinx/conf.py) unchanged from the trlcdoc
package into `<output>/sphinx/`, next to a `trlcdoc_settings.json` with the
project values from `trlcdoc.yaml`. The `conf.py` reads this JSON file, sets
the Sphinx configuration and, at its very end, executes the `conf` file in its
own namespace with `exec()`. Read that `conf.py` to see what your file can
use.

The `conf` file runs after `extra_conf`, so it can read and change every value
trlcdoc sets. Everything defined in `conf.py` before it is available without
an import:

| Name                                                  | Content |
|-------------------------------------------------------|---------|
| `PROJECT_ROOT`                                        | `pathlib.Path` of the project root. |
| `trlcdoc_links`                                       | Dict with `repository` (HTTPS URL, `None` without git or origin remote), `commit` (`HEAD`, `None` outside git), `root` and the page mappings of the Markdown link resolution. |
| `project`, `author`, `copyright`, `version`, `release` | From the `project` section. |
| `extensions`                                          | trlcdoc's extensions plus `html: extensions`. |
| `html_theme`, `html_static_path`, `html_logo`, `html_favicon`, `html_last_updated_fmt` | Site settings. |
| `rst_prolog`, `source_suffix`, `myst_heading_anchors`, `plantuml` | Source and diagram settings. |
| `Path`, `os`, `json`, `subprocess`, `shutil`, `urlparse`, `Any` | Modules and names imported by `conf.py`. |

Names starting with `_` (e.g. `_SETTINGS`) are internal and may change.
Code checkers do not know about this namespace and report these names as
undefined; `# pylint: skip-file` silences pylint.

```python
# doc/sphinx/sphinx_conf.py
# pylint: skip-file

autoapi_dirs = [str(PROJECT_ROOT / 'src')]
html_static_path.append(str(PROJECT_ROOT / 'doc' / 'sphinx' / '_static'))
html_css_files = ['custom.css']


def setup(app):
    app.connect('builder-inited', lambda app: print("project hook"))
```

- The file runs in the Sphinx folder `<output>/sphinx/`, so **build paths
  from `PROJECT_ROOT`**, not relative to the file.
- Functions defined in the file become Sphinx configuration values too, e.g.
  `linkcode_resolve()` for `sphinx.ext.linkcode`. They can use the names
  above, e.g. `trlcdoc_links["repository"]` and `trlcdoc_links["commit"]` to
  link the API sources to the repository.
- A `setup(app)` function is called after trlcdoc's own setup.
- Do not reassign `html_static_path`, append to it: trlcdoc's `_static`
  folder holds the stylesheet and the `s5defs.txt` roles included in every
  page.

### 8.3 index: project start page

Without `index`, trlcdoc generates the start page: the heading
`<project name> documentation` and a table of contents with all documents. With
`index`, your reStructuredText file is the start page, e.g. for an
introduction, a logo or several table of contents sections.

```rst
pyTRLCConverter
===============

.. image:: {project_root}/doc/images/context.svg

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   sw_requirements/index
   sw_architecture/index
   sw_detail_design
   sw_tracing_report
   license_include
```

Your page **owns the table of contents**: trlcdoc adds nothing to it, so list
every document, using the page names of [4.1](#41-common-keys)
(`<id>/index` for `trlc` and `test_results`, `<id>` for all others). A
document missing in the toctree is still built, and Sphinx warns that it is
not included in any toctree. The `documents` order then only determines the
build, not the navigation.

### 8.4 page_header

reStructuredText inserted at the top of every page trlcdoc generates: the
generated start page and the pages of type `trlc`, `test_results`,
`trace_report`, `html`, `command` and `text`. Not the pages of type
`rst`/`markdown` and not a project `index`, these are yours already.

```rst
.. figure:: {project_root}/doc/images/NewTec_Logo.png
   :align: right
   :width: 150px

.. container:: clearboth

   \
```

Use it for a logo, a classification notice or a disclaimer. Because it is
inserted into pages at different folder depths, image paths must use
`{project_root}`.

### 8.5 The {project_root} placeholder

trlcdoc copies project owned pages into the generated Sphinx folder, at
different depths (`index.rst`, `sw_requirements/index.rst`). A relative path
written in the original file would therefore be wrong.

In these files, trlcdoc replaces `{project_root}` with the relative path from
the page to the project root:

- `html.index`,
- `html.page_header` (separately for each page it is inserted into),
- documents of type `rst` and `markdown`, unless they set
  `placeholders: false` ([4.7](#47-type-rst-and-type-markdown)).

```rst
.. image:: {project_root}/doc/images/architecture.svg
.. literalinclude:: {project_root}/examples/simple/simple.trlc
```

The placeholder is not replaced in the `conf` file; use `PROJECT_ROOT` there.

## 9. Generated files

Everything goes to `paths.output`:

```text
build/trlcdoc/
├── plantuml/plantuml-<version>.jar     plantuml step (download)
├── tests/
│   ├── junit.xml                       tests step (pytest)
│   ├── coverage/                       HTML coverage report (pytest with --cov)
│   └── results/sw_test_result_report.trlc
├── convert/
│   ├── rst/<id>/                       convert step, one folder per TRLC document
│   └── markdown/<id>/                  convert --format markdown
├── trace/
│   ├── <level>.yaml, <level>.lobster   extracted items per level
│   ├── lobster-report.conf             generated policy
│   ├── report.lobster
│   └── tracing_report.html
├── sphinx/                             generated Sphinx sources, conf.py (copy) and trlcdoc_settings.json
├── doctrees/                           Sphinx cache
└── html/                               the site, open html/index.html
```

Publish the `html` folder. Each step clears its own folders before it runs,
so stale files of a previous run do not remain.

## 10. Typical errors

| Message | Cause and fix |
|---------|---------------|
| `... does not match the schema: documents/1: 'title' is a required property` | The document type needs this key, see the table in [4](#4-documents). The number is the position in the list, starting at 0. |
| `documents/0: 'titel' is not one of ['id', 'title', ...]` | Typo in a document key, or a key that is not allowed for this document type. |
| `Additional properties are not allowed ('document' was unexpected)` | Typo in a key of the other sections, e.g. a top level key. |
| `documents[x].include: 'y' is no document of type trlc or test_results.` | `include` names a missing id or a page type without TRLC records. |
| `documents[x].pytrlcconverter.converter.rst: file '...' not found.` | Wrong path, or `builtin:` prefix missing for a built-in file. |
| `documents/0: 'converter' is not one of ['id', 'title', ...]` | A pyTRLCConverter option on document level. Move it into the `pytrlcconverter` block. |
| `trace.levels[A].requires: level 'B' is not defined.` | The level name must match exactly, including spaces and case. |
| `Tests without test case link (property ..., output ..., name pattern ...)` | Tests without test case link, see [5.3](#53-link-from-test-results-to-test-cases). |
| `Tests linked to several test cases, which needs tests.link.array` | Set `array: true` and make `relates` an array in the model. |
| `Tests linked to test cases of several packages` | All test cases of the results must be in one package, see [5.4](#54-the-generated-test-result-records). |
| `tests/link: {...} is not valid under any of the given schemas` | `link` needs `output`, or both `from` and `to`. |
| `No test results in ..., run the tests step first.` | Run `trlcdoc tests convert` or `trlcdoc`. |
| `No converted files in ..., run the convert step first.` | Run `convert` before `html`. |
| `pyTRLCConverter` reports an unresolved reference | The referenced records' document is missing in `include`. |
| LOBSTER: `X cannot trace to Y items` | A level in `requires` of `Y` lacks `Y` in its `trace_to`. |
| Sphinx: `document isn't included in any toctree` | With `html.index`, add the page to your toctree. |

## 11. Complete examples

A configuration example using all sections, with requirements, architecture, test
cases, test results, code tracing and a customized site.

```yaml
# yaml-language-server: $schema=https://nhjschulz.github.io/trlc-doc/schema/V0.3.0/trlcdoc.schema.json

project:
  name: pyTRLCConverter
  author: NewTec GmbH
  copyright: 2024 - 2026, NewTec GmbH
  repository: https://github.com/NewTec-GmbH/pyTRLCConverter
  logo: doc/images/NewTec_Logo.png
  favicon: doc/images/favicon.ico

paths:
  trlc_model: trlc/model
  output: build/trlcdoc

plantuml:
  version: "1.2026.1"

documents:
  - id: sw_requirements                 # no title: the converter writes the heading
    type: trlc
    source: trlc/swe-req
    pytrlcconverter:
      converter:
        rst: tools/converter/req2rst.py   # project owned converters
        markdown: tools/converter/req2markdown.py
      translation: tools/converter/translation.json
      render_cfg: tools/converter/renderCfg.json

  - id: sw_architecture
    type: trlc
    source: trlc/swe-arch
    include: [sw_requirements]          # architecture items reference requirements
    pytrlcconverter:
      converter:
        rst: tools/converter/req2rst.py
      translation: tools/converter/translation.json
      render_cfg: tools/converter/renderCfg.json

  - id: sw_detail_design
    type: rst
    source: doc/sphinx/sw_detail_design.rst

  - id: sw_tests
    type: trlc
    source: trlc/swe-test
    include: [sw_requirements]
    pytrlcconverter:
      converter:
        rst: tools/converter/tc2rst.py
      translation: tools/converter/translation.json

  - id: sw_tracing_report
    title: SW Tracing Report
    type: trace_report

  - id: sw_test_result_report
    type: test_results
    include: [sw_tests]                 # results reference the test cases
    pytrlcconverter:
      converter:
        rst: tools/converter/create_test_report_in_rst.py

  - id: coverage_report
    title: Coverage Report
    type: html
    source: tests:coverage

  - id: license_include
    title: License information
    type: text
    source: LICENSE

tests:
  runner: pytest
  args: [tests, -v, --cov=./src]        # --cov enables the coverage report
  link:
    property: lobster-trace             # record_property("lobster-trace", "SwTests.x")
    array: true                         # some tests record several test cases
    from: "test_{name}"
    to: "SwTests.{name}"

trace:
  levels:
    - name: SW Requirement
      document: sw_requirements
      record_type: SwRequirements.SwReq
      description_fields: [description, valid_status]
      requires: [SW Code, SW Test Case, SW Architecture]

    - name: SW Constraint
      document: sw_requirements
      record_type: SwRequirements.SwConstraint
      requires: [SW Architecture]

    - name: SW Architecture
      document: sw_architecture
      record_type: SwArch.SwArchSpec
      tags: [satisfies]
      trace_to: [SW Requirement, SW Constraint]

    - name: SW Code
      kind: implementation
      extractor: lobster-python
      sources: [src/pyTRLCConverter]
      trace_to: [SW Requirement]

    - name: SW Test Case
      document: sw_tests
      record_type: SwTests.SwTestCase
      tags: [verifies]
      trace_to: [SW Requirement]

    - name: SW Test Result
      document: sw_test_result_report
      record_type: SwTests.SwTestCaseResult
      tags: [relates]
      description_fields: [name]
      trace_to: [SW Test Case]

    - name: SW Test Code
      kind: implementation
      extractor: lobster-python
      sources: [tests]
      trace_to: [SW Test Case]

html:
  theme: sphinx_rtd_theme
  extensions: [sphinx_rtd_theme, autoapi.extension, sphinx.ext.napoleon, sphinx_favicon]
  conf: doc/sphinx/sphinx_conf.py
  index: doc/sphinx/index.rst
  page_header: doc/sphinx/page_header.rst
```

More configurations in use:

- [trlcdoc.yaml](trlcdoc.yaml) of trlcdoc itself: built-in converters, name
  pattern test linking, default site.
- [flashcontainer](https://github.com/nhjschulz/flashcontainer/blob/master/trlcdoc.yaml):
  the same structure with property based test linking.
