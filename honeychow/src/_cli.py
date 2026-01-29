import argparse

from . import __author__, __version__


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='"Honey Chow": A fast, asynchronous username enumeration tool.',
    )

    parser.add_argument("username", nargs="?", help="Username to search for")

    parser.add_argument(
        "-s", "--sites", nargs="+", help="Specific sites to check (space-separated)"
    )

    parser.add_argument(
        "-c", "--categories", nargs="+", help="Categories to search (space-separated)"
    )

    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=15,
        help="Request timeout in seconds (default: 15)",
    )

    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=100,
        help="Max concurrent requests (default: 100)",
    )

    parser.add_argument(
        "-o", "--output", metavar="PATH", help="Export results to CSV file"
    )

    parser.add_argument(
        "-O",
        "--output-all",
        action="store_true",
        help="Include not found and failed in CSV export",
    )

    parser.add_argument(
        "-N",
        "--not-found",
        action="store_true",
        help="Show sites where username wasn't found",
    )

    parser.add_argument(
        "-f",
        "--failed",
        action="store_true",
        help="Show sites that errored (timeout, connection error, etc.)",
    )

    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Only show summary (no live output)"
    )

    parser.add_argument(
        "-S", "--list-sites", action="store_true", help="List all available sites"
    )

    parser.add_argument(
        "-C",
        "--list-categories",
        action="store_true",
        help="List all available categories",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}, MIT License, {__author__}",
    )

    return parser.parse_args()
