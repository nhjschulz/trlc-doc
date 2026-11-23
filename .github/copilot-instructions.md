## Changing the Repository Contents

For any change to this repository, follow the development rules in

.claude/skills/trlcdoc-development/SKILL.md.

In particular, check whether the change needs an issue, preserve requirements/architecture/test traceability, and report verification honestly.

## Design documentation lives in `trlc/`

`trlc/` is the design documentation: read the requirements and the architecture (with its component diagrams)
to understand a feature before reading or changing its code. `lobster-trace: SwRequirements.<req>` comments
lead from a requirement to its code.

## Tests

[.github/workflows/test.yml](.github/workflows/test.yml) shows how the tests are set up and run, including the
external tools they need. [.github/workflows/pages.yaml](.github/workflows/pages.yaml) does the same for the full
self-build. `tests/conftest.py` builds a minimal TRLC project in `tmp_path` (`make_project`, `base_config`,
`write_config`); most tests start from it.
