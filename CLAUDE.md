# CLAUDE.md -- cping

## Description

cping is a CLI tool that pings Claude's service status page and displays
a formatted summary in the terminal. It checks the Atlassian Statuspage API
at `https://status.claude.com/api/v2/summary.json`.

## Structure

```
cping              # Main CLI script (executable, no .py extension)
tests/smoke.sh     # Smoke tests
.github/workflows/ # CI configuration
```

## Tech Stack

- Python 3.6+ (single file, zero external dependencies)
- Standard library only: `urllib.request`, `json`, `sys`, `argparse`

## Build / Test

No build step required. Run directly:

```bash
./cping
./cping --json
./cping --no-color
```

Run smoke tests:

```bash
bash tests/smoke.sh
```

## Rules

- Include `Co-Authored-By: Claude` in commit messages (ClaudeCodeCafe org rule)
- Keep it as a single file with zero dependencies
- Follow PEP 8
- English only for all code, comments, and docs
- Exit codes: 0 = all operational, 1 = error, 2 = degraded
