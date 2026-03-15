"""Entry point for the SwaptDisplay application."""

import argparse

from .app import SwaptDisplay


def main() -> None:
    """Run the SwaptDisplay application."""
    parser = argparse.ArgumentParser(
        prog="swaptdisplay",
        description="TUI for real-time public transport departures.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-n",
        "--station-name",
        default="Augsburg Hbf",
        help="initial station name to display (default: %(default)s)",
    )
    group.add_argument(
        "-i",
        "--station-id",
        type=int,
        help="initial station id to display",
    )

    args = parser.parse_args()
    station: str | int = (
        args.station_id if args.station_id is not None else args.station_name
    )
    app = SwaptDisplay(station)
    app.run()


if __name__ == "__main__":
    main()
