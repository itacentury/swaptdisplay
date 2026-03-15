from pathlib import Path
from typing import NamedTuple


class Departure(NamedTuple):
    """Represents a single public transport departure."""

    line: str
    direction: str
    scheduled: str
    expected: str
    delay: int


class Station(NamedTuple):
    """A public transport station with display name and API ID."""

    name: str
    station_id: int


def parse_stations() -> list[Station]:
    """Parse stations from 'stations.txt' and return them sorted by name."""
    file_path: Path = Path(__file__).parent / "stations.txt"
    with open(file_path, encoding="UTF-8") as f:
        lines: list[str] = f.readlines()

    stations: list[Station] = []
    for line in lines:
        name, station_id = line.split(";", maxsplit=1)
        stations.append(Station(name, int(station_id)))
    stations.sort()
    return stations


def create_dict_by_name(stations: list[Station]) -> dict[str, Station]:
    """Create a lookup dictionary mapping station names to their Station objects."""
    return {station.name.lower(): station for station in stations}


def create_dict_by_id(stations: list[Station]) -> dict[int, Station]:
    """Create a lookup dictionary mapping station IDs to their Station objects."""
    return {station.station_id: station for station in stations}
