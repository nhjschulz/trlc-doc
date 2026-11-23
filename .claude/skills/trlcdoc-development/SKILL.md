---
name: trlcdoc-development
description: Rules for every change to the trlc-doc repository (the trlcdoc package, its tests, TRLC requirements/architecture/test cases, examples, documentation, CI workflows, releases). Use it before writing code, tests, docs, commits, issue drafts or release changes in this repository.
---

# Developing trlcdoc

trlcdoc is developed requirements-driven and documents itself with itself. Every
change keeps four things true at the same time:

1. **Quality and readability over cleverness.** Code is read far more often than
   written. Prefer the obvious, explicit construct over a compact or clever one.
2. **Requirement, architecture and test trace coverage is complete.** Every
   requirement is satisfied by architecture, implemented by code and verified by a
   test case with a passing test result. A full `trlcdoc` build reports
   `0 not traced` on every level.
3. **Non-trivial changes have a GitHub issue** that describes the change before it
   is implemented. Cosmetic changes and obvious one-line fixes don't need one.
4. **Nothing is claimed that wasn't verified.** Report what was run and what wasn't.

## 1. Issue first

- A GitHub issue is required for every non-trivial change (new feature, behavior
  change, refactoring). Only cosmetic changes (formatting, renames, style) and
  obvious one-line fixes may skip it.
- If no issue exists, draft one for the user and stop until it exists. Draft it as
  **one markdown block** fenced with four backticks (so inner code fences survive),
  ready to paste, with these sections:
  - title (`# ...`), **Problem** or **Description**, **Steps to reproduce** for
    bugs (verified, with real output), **Proposal**, **Done when** (testable criteria,
    including requirement/test case updates).
- Read existing issues without `gh` (not installed):
  `curl -s https://api.github.com/repos/nhjschulz/trlc-doc/issues/<n>` and
  `.../issues/<n>/comments`.
- Commits that implement an issue end the message with `Closes #<n>`
  (`Part of #<n>` for partial commits).

## 2. Branches and commits

- `main` and `develop` are protected. All work happens on a branch created from
  the latest `origin/develop`, without upstream tracking:

  ```bash
  git fetch -q
  git switch --no-track -c <type>/<short_name> origin/develop
  ```

  Types: `feat/`, `fix/`, `docs/`, `chore/`, `refactor/`, `release/`.
- If the user's checkout has uncommitted changes, don't touch them: work in a
  worktree in the scratchpad (`git worktree add`), and remove it afterwards.
- Commit only when the user asks. Never push unless asked; give the push command
  (`git push -u origin <branch>`) in the report instead.
- Commit messages: `type(scope): Summary in imperative, capitalized`, a body that
  explains *why*, then the issue reference and the attribution line the session
  prescribes. One logical change per commit: renames, formatting and fixes are
  separate commits.
- Stage explicit paths. Check `git diff --cached --stat` before committing, so
  unrelated staged changes (e.g. an earlier `git rm`) don't slip in.
- PRs are merged with merge commits. A formatting commit is listed in
  `.git-blame-ignore-revs`.

## 3. Requirements, architecture, tests and tracing

The TRLC files are part of every functional change:

| What | Where | Rule |
| --- | --- | --- |
| Requirement | `trlc/swe-req/swe-req.trlc`, `SwReq sw_req_<topic>` | Describes the behavior with "The software shall ...", plus `verification_criteria`. Extend an existing requirement or add a new one. |
| Architecture | `trlc/swe-arch/swe-arch.trlc`, `SwArchSpec` | Every requirement is in `satisfies` of an architecture item, e.g. the component that implements it. |
| Code | `trlcdoc/*.py` | Every function has `# lobster-trace: SwRequirements.<req>` comment(s) directly after the `def` line, before the docstring. |
| Test case | `trlc/swe-test/swe-test.trlc`, `SwTestCase tc_<name>` | `verifies` the requirement; its description names the test file and what is checked. |
| Test | `tests/test_*.py`, `def test_<name>` | Implements `tc_<name>` (linked by name). |

- A new function without trace comment, or a requirement without code or test, is
  a finding of the trace step. Fix it, don't hide it.
- TRLC text: one bullet per line. A wrapped bullet produces a Sphinx warning
  ("Bullet list ends without a blank line", pyTRLCConverter issue #174). Keep lines
  at most 120 characters.
- When a change touches TRLC text, or during a release, check whether a
  pyTRLCConverter release newer than the required minimum fixes issue #174
  (release notes on GitHub, or `pip index versions pyTRLCConverter`). If yes, raise
  the minimum version in `pyproject.toml`, verify that a wrapped bullet builds
  without warning, and only then allow multi-line bullets.
- A test for a bug must fail without the fix: verify it by stashing the fix
  (`git stash push -- <file>`), running the test, and restoring it.

## 4. Code

- The code follows PEP 8 with a line length of 120: `ruff format` enforces the
  layout, `ruff check` the rules (`E`, `W` for pycodestyle, `N` for naming). New
  code must pass both without disabling rules.
- Python 3.10 or newer: built-in generics and `X | None`, `pathlib`, f-strings.
- Google-style docstrings with `Args:`, `Returns:`, `Raises:`. The types in the
  docstring match the signature.
- Small functions with one purpose and a clear name. Comments explain *why*, not
  *what*. No clever one-liners, nested comprehensions or tricks where a plain loop
  or an extra named variable reads better.
- Follow the file layout: license header, `# Imports ***`, `# Variables ***`,
  `# Classes ***`, `# Functions ***`, `# Main ***` sections.
- Errors for the user raise `TrlcdocError` with a message that names the
  configuration entry, file or tool and what to do. Exit codes: 0 success,
  1 content findings (failed tests, untraced items), 2 build or configuration error.
- Configuration changes: update the JSON schema `trlcdoc/schema/trlcdoc.schema.json`
  and the reference checks in `trlcdoc/config.py` together.
- `trlcdoc/converters/` is a copy of pyTRLCConverter's project converters: don't
  restyle it; it is excluded from ruff and coverage. During a release, and before
  changing a file in `trlcdoc/converters/`, compare the converters with the project
  converters of the latest pyTRLCConverter release and tell the user about
  differences. Don't copy them in without being asked.
- ruff is the linter and formatter (line length 120). Don't disable a rule to make
  a finding go away; fix the code. Use `# fmt: off`/`# fmt: on` only for
  deliberately aligned data, with a comment why.

## 5. Documentation

User-visible changes update the documentation in the same branch:

- `configuration.md`: the configuration reference (every key, behavior, typical
  errors in chapter 10). Keep its chapter numbers and anchors stable.
- `README.md` (GitHub) and `PYPI.md` (PyPI page).
- The examples in `examples/` if they use the changed feature.

Write for the reader: short sentences, concrete examples, no marketing words.

## 6. Verification before reporting

Run and report the results of:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m pytest -q tests
.venv/bin/trlcdoc clean all     # exit 0, no Sphinx WARNING, every level "0 not traced"
```

- Install into the `.venv` with `uv pip install --python .venv/bin/python ...` if
  uv is available; a uv-created venv has no pip inside. Without uv, the venv was
  made with `python -m venv`: use `.venv/bin/python -m pip install ...`.
- The HTML tests need Java; the C/C++ tracing test needs doxygen (skipped without
  it, which leaves `tc_trace_doxygen` untraced in a full build).
- CI: `test.yml` runs ruff and the test matrix, `pages.yaml` runs the full
  `trlcdoc` build, `release.yaml` publishes to PyPI. A new tool the tests or the
  build need (e.g. doxygen, Java, Graphviz) goes into both `test.yml` and
  `pages.yaml`; otherwise the skipped test leaves its test case untraced and the
  Pages build fails.
- When a change affects the examples, build each affected example with
  `trlcdoc clean all` (and `trace html --online` for link changes) in its folder.
- Tools that aren't installed (gcovr, cargo tools, ...) go into the scratchpad, not
  into the user's home or system. Tell the user about anything installed elsewhere.
- Report honestly: what passed, what wasn't run and why, and known limitations.

## 7. Examples

`examples/<language>-<trace tool>-<test tool>` (e.g. `c-doxygen-ceedling`,
`cpp-doxygen-gtest`, `python-lobster-pytest`):

- The same Greeter program, requirements, architecture and test cases in each
  language, so they can be compared.
- Keep `trlcdoc.yaml` minimal: only keys that differ from trlcdoc's defaults, no
  settings a reader has to understand without a reason.
- No project branding: no custom Sphinx theme,
  logos, favicon or CSS. The site uses trlcdoc's defaults and the built-in
  converters (`builtin:...`).
- `project.repository` is omitted (`auto`), so online links point to this
  repository. Each example has a `.gitignore` for its build output and a README
  focused on the documentation generation.

## 8. Releases

- Branch `release/x.y.z`: replace every reference to the old version
  (`git grep -n "<old version>"`): `pyproject.toml`, `trlcdoc.yaml`
  (`project.version`), the schema URLs `.../schema/Vx.y.z/...` in `README.md`,
  `PYPI.md`, `configuration.md` and the examples, and the examples' minimum
  `trlcdoc` version.
- Check the package, tests, self-build and every example. Build the package into
  the scratchpad, not into the repository, and check it like the release workflow:
  - with uv: `uv build --out-dir <dist>`, then `uvx twine check --strict <dist>/*`
  - without uv: `python -m pip install build twine` into a venv, then
    `python -m build --outdir <dist>` and `python -m twine check --strict <dist>/*`
- Tags are `Vx.y.z` (uppercase V). A GitHub release triggers the PyPI workflow
  (environment `pypi`, may wait for approval); the tag push publishes the schema
  copy via the Pages workflow.
