# Greeter - A simple Python Example with TRLC <!-- omit in toc -->

This folder contains a small **Python project** example with TRLC. It follows
the TRLC work instructions to implement traceability according to the
V-Model for software development.

- [Abstract](#abstract)
- [Workspace Setup](#workspace-setup)
- [Running Greeter](#running-greeter)
- [Creating Reports](#creating-reports)
  - [Configuration](#configuration)
  - [Single Steps](#single-steps)
- [Important](#important)

## Abstract

Greeter is an almost trivial program. It 'greets' a user with a different phrase
dependent on the system time. The real value of this example comes from its TRLC
and Lobster tool integrations. It shows:

- How to apply TRLC in a Python project.
- Get software V-Model traceability between requirements, design, sources and tests.

## Workspace Setup

Greeter is typical Python Project and should be setup using a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate.ps1 # <- Windows Power Shell version
```

Note:

- For Windows CMD shell, use ```.venv\Scripts\activate.bat``` to activate the
  virtual environment.
- For Linux/Macos, use ```source .venv/bin/activate``` to activate the virtual
  environment.

Then install the greeter package with its development tools: trlcdoc, which
brings the TRLC components, and the test tools pytest, pytest-cov and freezegun:

```bash
pip install -e ".[dev]"
```

## Running Greeter

The Greeter tool itself is not the focus of this TRLC using example, but it
is operational. The installation above provides the ```greet``` command:

```bash
greet [name]
```

## Creating Reports

[trlcdoc](https://github.com/nhjschulz/trlc-doc) creates all reports and the
documentation website in one run. It is installed with the ```dev``` extra
and needs Java for the PlantUML diagrams (the PlantUML jar is downloaded
automatically).

```bash
trlcdoc
```

trlcdoc runs these steps:

1. Check the configuration.
2. Run the unit tests with pytest, including the coverage report, and convert
   the test results into TRLC records.
3. Convert the requirements, architecture, test cases and test results with
   [pyTRLCConverter](https://github.com/NewTec-GmbH/pyTRLCConverter) into
   reStructuredText.
4. Create the traceability report with
   [LOBSTER](https://github.com/bmw-software-engineering/lobster).
5. Build the HTML website with Sphinx.

The resulting website is generated in ```build/trlcdoc/html```. Open it with:

```bash
trlcdoc show
```

The exit code is 0 on success, 1 if there are content findings like failed
tests or missing trace links, and 2 on build errors.

### Configuration

Everything is configured in ```trlcdoc.yaml```:

- **documents:** the pages of the website, their TRLC sources and the
  pyTRLCConverter converters. The example uses the converters built into
  trlcdoc.
- **tests:** the pytest arguments and how the test results are linked to the
  TRLC test cases (```record_property("lobster-trace", ...)``` in the tests).
- **trace:** the traceability levels and how they trace to each other.

See the
[trlcdoc configuration reference](https://github.com/nhjschulz/trlc-doc/blob/main/configuration.md)
for all options.

### Single Steps

The steps can also be run one by one, e.g. while editing requirements:

```bash
trlcdoc check                      # check the configuration
trlcdoc tests                      # run the unit tests
trlcdoc convert                    # TRLC to reStructuredText
trlcdoc convert --format markdown  # TRLC to Markdown in build/trlcdoc/convert/markdown
trlcdoc trace                      # traceability report
trlcdoc html                       # website
trlcdoc clean                      # remove build/trlcdoc
```

## Important

The constraints are mainly driven by the lobster-python tool and may change in future.

- Tracing supports the following levels:
  - Class
  - Method
  - Function
