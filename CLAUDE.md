# CLAUDE.md -- cping

## Description

cping is a CLI tool that pings Claude's service status page and displays
a formatted summary in the terminal. It checks the Atlassian Statuspage API
at `https://status.claude.com/api/v2/summary.json`.

## Structure

```
cping                  # Standalone CLI script (direct execution, Homebrew)
src/cping/
  __init__.py          # Package init, re-exports __version__
  __main__.py          # python -m cping support
  cli.py               # Core logic (canonical source, mirrors ./cping)
pyproject.toml         # pip/pipx packaging (PyPI name: cping-cli)
tests/smoke.sh         # Smoke tests
.github/workflows/     # CI configuration
```

## Tech Stack

- Python 3.8+ (zero external dependencies)
- Standard library only: `urllib.request`, `json`, `sys`, `argparse`
- Build system: hatchling (for pip packaging)

## Build / Test

Run directly (standalone):

```bash
./cping
./cping --json
./cping --no-color
```

Run via package:

```bash
PYTHONPATH=src python3 -m cping
pip install -e .  # editable install
```

Run smoke tests:

```bash
bash tests/smoke.sh
```

## Rules

- Include `Co-Authored-By: Claude` in commit messages (ClaudeCodeCafe org rule)
- Keep zero external dependencies
- Keep `./cping` standalone script and `src/cping/cli.py` in sync (identical logic)
- Follow PEP 8
- English only for all code, comments, and docs
- Exit codes: 0 = all operational, 1 = error, 2 = degraded
