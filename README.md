# cping

Ping Claude's service status from the terminal.

A single-file Python 3 CLI tool with zero external dependencies that checks
[status.claude.com](https://status.claude.com) and displays a formatted view
of all Claude service components.

## Install

### Homebrew

```bash
brew install ClaudeCodeCafe/tap/cping
```

### Manual

```bash
curl -fsSL https://raw.githubusercontent.com/ClaudeCodeCafe/cping/main/cping -o /usr/local/bin/cping
chmod +x /usr/local/bin/cping
```

## Usage

```bash
cping
```

```
Claude Service Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ● claude.ai                   operational
  ● Claude API                  operational
  ● Claude Code                 operational
  ● platform.claude.com         operational
  ● Claude for Government       operational

Updated: 2026-05-13T09:00:00Z
```

### Options

| Flag           | Description          |
| -------------- | -------------------- |
| `-v, --version`| Show version         |
| `-h, --help`  | Show help            |
| `-j, --json`  | Output raw JSON      |
| `--no-color`  | Disable colored output |

### Exit Codes

| Code | Meaning                                  |
| ---- | ---------------------------------------- |
| 0    | All systems operational                  |
| 1    | Error (network, parse, etc.)             |
| 2    | One or more components not operational   |

### Status Indicators

- `●` Green -- Operational
- `▲` Yellow -- Degraded performance / Partial outage
- `✕` Red -- Major outage
- `◆` Gray -- Under maintenance

## Requirements

- Python 3.6+

No external packages required. Uses only the Python standard library.

## License

MIT
