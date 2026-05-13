"""cping - Ping Claude's service status from the terminal."""

import argparse
import json
import sys
import urllib.error
import urllib.request

__version__ = "0.1.0"

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


def fetch_status():
    """Fetch the status summary from the Atlassian Statuspage API."""
    req = urllib.request.Request(
        STATUS_URL,
        headers={"User-Agent": f"cping/{__version__}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        print(f"Error: Failed to connect to status page: {exc.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.HTTPError as exc:
        print(f"Error: HTTP {exc.code} from status page", file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, OSError) as exc:
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
    status_info = data.get("status", {})
    components = data.get("components", [])
    incidents = data.get("incidents", [])
    page = data.get("page", {})

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

    # Filter out top-level "page" component if present
    visible_components = [
        c for c in components if c.get("group", True) is not False
    ]

    if not visible_components:
        visible_components = components

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
            inc_name = incident.get("name", "Unknown incident")
            inc_status = incident.get("status", "investigating")
            impact = incident.get("impact", "none")
            symbol_i, color_i = STATUS_INDICATORS.get(
                impact, ("▲", YELLOW)
            )
            indicator = colorize(symbol_i, color_i, use_color)
            print(f"  {indicator} {inc_name}")
            print(f"    Status: {inc_status}")

            # Show latest update if available
            updates = incident.get("incident_updates", [])
            if updates:
                latest = updates[0]
                body = latest.get("body", "")
                if body:
                    # Wrap long update text
                    print(f"    {body[:200]}")

    # Updated timestamp
    updated_at = page.get("updated_at", status_info.get("updated_at", "N/A"))
    print()
    print(colorize(f"Updated: {updated_at}", GRAY, use_color))


def all_operational(data):
    """Check if all components are operational."""
    components = data.get("components", [])
    return all(
        c.get("status") == "operational"
        for c in components
    )


def build_parser():
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="cping",
        description="Ping Claude's service status from the terminal.",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"cping {__version__}",
    )
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output raw JSON",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    return parser


def main():
    """Entry point."""
    parser = build_parser()
    args = parser.parse_args()

    # Determine if color should be used
    use_color = not args.no_color and sys.stdout.isatty()

    data = fetch_status()

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        display_status(data, use_color)

    # Exit code: 0 if all operational, 2 if degraded
    if not all_operational(data):
        sys.exit(2)


if __name__ == "__main__":
    main()
