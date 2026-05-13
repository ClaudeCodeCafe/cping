"""cping - Ping Claude's service status from the terminal."""

import argparse
import json
import os
import signal
import sys
import urllib.error
import urllib.request

try:
    from importlib.metadata import version as _metadata_version

    __version__ = _metadata_version("cping-cli")
except Exception:
    __version__ = "0.1.0"  # fallback for standalone execution

STATUS_URL = "https://status.claude.com/api/v2/summary.json"
REQUEST_TIMEOUT = 10

# ANSI color codes
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
GRAY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Status indicator mapping: (symbol, color)
STATUS_INDICATORS = {
    "operational": ("●", GREEN),
    "degraded_performance": ("▲", YELLOW),
    "partial_outage": ("▲", YELLOW),
    "major_outage": ("✕", RED),
    "under_maintenance": ("◆", GRAY),
}

# Human-readable status labels
STATUS_LABELS = {
    "operational": "operational",
    "degraded_performance": "degraded",
    "partial_outage": "partial outage",
    "major_outage": "major outage",
    "under_maintenance": "maintenance",
}

# Overall status indicator descriptions
OVERALL_INDICATORS = {
    "none": ("●", GREEN, "All Systems Operational"),
    "minor": ("▲", YELLOW, "Minor System Outage"),
    "major": ("▲", YELLOW, "Partial System Outage"),
    "critical": ("✕", RED, "Major System Outage"),
    "maintenance": ("◆", GRAY, "Under Maintenance"),
}

# Incident impact mapping: (symbol, color)
INCIDENT_IMPACT = {
    "none": ("●", GREEN),
    "minor": ("▲", YELLOW),
    "major": ("✕", YELLOW),
    "critical": ("✕", RED),
}


def fetch_status():
    """Fetch the status summary from the Atlassian Statuspage API."""
    req = urllib.request.Request(
        STATUS_URL,
        headers={"User-Agent": f"cping/{__version__}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(
            f"Error: HTTP {exc.code} from {STATUS_URL}",
            file=sys.stderr,
        )
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(
            f"Error: Failed to connect to {STATUS_URL}: {exc.reason}",
            file=sys.stderr,
        )
        sys.exit(1)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def colorize(text, color, use_color=True):
    """Wrap text in ANSI color codes if color is enabled."""
    if use_color:
        return f"{color}{text}{RESET}"
    return text


def format_status_line(name, status, use_color, name_width):
    """Format a single component status line with right-aligned status."""
    symbol, color = STATUS_INDICATORS.get(status, ("?", GRAY))
    label = STATUS_LABELS.get(status, status)

    indicator = colorize(symbol, color, use_color)
    padded_name = name.ljust(name_width)
    status_text = colorize(label, color, use_color)

    return f"  {indicator} {padded_name}  {status_text}"


def display_status(data, use_color):
    """Display the formatted status output."""
    if not isinstance(data, dict):
        print("Error: unexpected API response format", file=sys.stderr)
        return False

    status_raw = data.get("status") or {}
    status_info = status_raw if isinstance(status_raw, dict) else {}
    raw_components = data.get("components") or []
    incidents_raw = data.get("incidents") or []
    incidents = incidents_raw if isinstance(incidents_raw, list) else []
    page_raw = data.get("page") or {}
    page = page_raw if isinstance(page_raw, dict) else {}

    # Validate component entries
    components = [
        c for c in raw_components
        if isinstance(c, dict) and "name" in c and "status" in c
    ]

    # Overall status
    indicator_key = status_info.get("indicator", "none")
    symbol, color, description = OVERALL_INDICATORS.get(
        indicator_key, ("?", GRAY, "Unknown")
    )

    if use_color:
        title = f"{BOLD}Claude Service Status{RESET}"
    else:
        title = "Claude Service Status"
    print(title)
    print(colorize("━" * 44, GRAY, use_color))

    # Display overall status line
    overall_indicator = colorize(symbol, color, use_color)
    overall_text = colorize(description, color, use_color)
    print(f"  {overall_indicator} {overall_text}")
    print()

    # Filter to showcased components only
    visible_components = [c for c in components if c.get("showcase", False)]

    if not visible_components:
        print(
            "  Warning: No component data available",
            file=sys.stderr,
        )
        return False

    # Calculate name width for alignment
    names = [c.get("name", "") for c in visible_components]
    name_width = max(len(n) for n in names) if names else 20

    for component in visible_components:
        name = component.get("name", "Unknown")
        comp_status = component.get("status", "operational")
        print(format_status_line(name, comp_status, use_color, name_width))

    # Show active incidents if any
    if incidents:
        print()
        if use_color:
            print(f"{BOLD}Active Incidents{RESET}")
        else:
            print("Active Incidents")
        print(colorize("━" * 44, GRAY, use_color))
        for incident in incidents:
            if not isinstance(incident, dict):
                continue
            inc_name = incident.get("name", "Unknown incident")
            inc_status = incident.get("status", "investigating")
            impact = incident.get("impact", "none")
            symbol_i, color_i = INCIDENT_IMPACT.get(
                impact, ("▲", YELLOW)
            )
            indicator = colorize(symbol_i, color_i, use_color)
            print(f"  {indicator} {inc_name}")
            print(f"    Status: {inc_status}")

            # Show latest update if available
            updates_raw = incident.get("incident_updates", [])
            updates = updates_raw if isinstance(updates_raw, list) else []
            if updates and isinstance(updates[0], dict):
                latest = updates[0]
                body = latest.get("body", "")
                if body:
                    truncated = body[:200]
                    if len(body) > 200:
                        truncated += "..."
                    print(f"    {truncated}")

    # Updated timestamp
    updated_at = page.get("updated_at", status_info.get("updated_at", "N/A"))
    print()
    print(colorize(f"Updated: {updated_at}", GRAY, use_color))

    return True


def all_operational(components):
    """Check if all given components are operational."""
    if not components:
        return False
    return all(c.get("status") == "operational" for c in components)


def build_parser():
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="cping",
        description="Ping Claude's service status from the terminal.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"cping {__version__}",
    )
    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="Output raw JSON (always exits 0 on success)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    return parser


def _get_visible_components(data):
    """Extract showcase components from API data with validation."""
    if not isinstance(data, dict):
        return []
    raw = data.get("components") or []
    valid = [
        c for c in raw
        if isinstance(c, dict) and "name" in c and "status" in c
    ]
    return [c for c in valid if c.get("showcase", False)]


def main():
    """Entry point."""
    # Handle SIGPIPE gracefully (e.g. when piping to head)
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    parser = build_parser()
    args = parser.parse_args()

    # Determine if color should be used
    # Priority: --no-color flag > NO_COLOR env > FORCE_COLOR env > isatty()
    if args.no_color or os.environ.get("NO_COLOR") is not None:
        use_color = False
    elif os.environ.get("FORCE_COLOR") is not None:
        use_color = True
    else:
        use_color = sys.stdout.isatty()

    data = fetch_status()

    if args.json:
        print(json.dumps(data, indent=2))
        sys.exit(0)

    has_components = display_status(data, use_color)

    if not has_components:
        sys.exit(1)

    # Exit code: 0 if all operational, 2 if degraded
    # Use the same showcase-filtered components that display_status() shows
    visible = _get_visible_components(data)
    if not all_operational(visible):
        sys.exit(2)


if __name__ == "__main__":
    main()
