"""Entry point for the SwaptDisplay application."""

import argparse

from .app import SwaptDisplay


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="swaptdisplay",
        description="TUI for real-time public transport departures.",
    )

    group_one = parser.add_mutually_exclusive_group()
    group_one.add_argument(
        "-s",
        "--station",
        default="Augsburg Hbf",
        help="initial station name to display (default: %(default)s)",
    )
    group_one.add_argument(
        "-i",
        "--station-id",
        type=int,
        help="initial station id to display",
    )

    group_two = parser.add_mutually_exclusive_group()
    group_two.add_argument(
        "-s2",
        "--station2",
        default="Königsplatz",
        help="second station name for dual mode (default: %(default)s)",
    )
    group_two.add_argument(
        "-i2",
        "--station2-id",
        type=int,
        help="second station id for dual mode",
    )

    parser.add_argument(
        "-d",
        "--dual",
        action="store_true",
        help="start with both station panels visible",
    )

    return parser


def _resolve_station(
    name: str | None, station_id: int | None, fallback: str
) -> str | int:
    """Return the station ID if given, otherwise the name or fallback."""
    if station_id is not None:
        return station_id
    return name or fallback


def main() -> None:
    """Parse CLI arguments and run the SwaptDisplay application."""
    args = _build_parser().parse_args()

    first = _resolve_station(args.station, args.station_id, "Augsburg Hbf")
    second = _resolve_station(args.station2, args.station2_id, "Königsplatz")

    app = SwaptDisplay(first, second, args.dual)
    app.run()


if __name__ == "__main__":
    main()
