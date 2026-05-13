# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-05-13

### Added

- Initial release
- Fetch and display Claude service status from `status.claude.com`
- Colored terminal output with status indicators
- `--json` flag for raw JSON output (always exits 0 on success)
- `--no-color` flag to disable colored output
- `NO_COLOR` / `FORCE_COLOR` environment variable support
- Overall status summary line display
- Active incident display with truncated update bodies
- Exit code 0 (all operational) / 2 (degraded) in default mode
- pip/pipx packaging via `cping-cli` on PyPI
- Homebrew tap support
- Standalone single-file execution
- Smoke tests and unit tests with mocked HTTP
- CI with Python 3.8–3.12 matrix

[0.1.0]: https://github.com/ClaudeCodeCafe/cping/releases/tag/v0.1.0
