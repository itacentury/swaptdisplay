"""API client for fetching public transport departures."""

from datetime import UTC, datetime
from typing import Any

import httpx

from .models import Departure


async def get_departures(
    client: httpx.AsyncClient, station_id: int
) -> list[Departure] | None:
    """Fetch departures from the transport API. Returns None on failure."""
    url: str = f"https://v6.db.transport.rest/stops/{station_id}/departures"

    try:
        response: httpx.Response = await client.get(url)
        response.raise_for_status()
        return extract_departures(response.json())
    except httpx.HTTPError, ValueError:
        return None


def parse_datetime(datetime_string: str) -> datetime | None:
    """Parse an ISO 8601 datetime string. Returns None if parsing fails."""
    if not isinstance(datetime_string, str):
        return None

    try:
        return datetime.fromisoformat(datetime_string)
    except ValueError:
        return None


def extract_departures(data: Any) -> list[Departure]:
    """Extract and parse departures from the API response."""
    if not data:
        return []

    departures: list[Departure] = []
    now: float = datetime.now(tz=UTC).timestamp()
    for entry in data["departures"]:
        try:
            when: datetime | None = parse_datetime(entry["when"])
            if when is None:
                continue

            if when.timestamp() < now:
                continue

            line_name: str = entry["line"]["name"]
            direction: str = str(entry["direction"]).removesuffix(", Augsburg (Bayern)")
            planned_when: datetime | None = parse_datetime(entry["plannedWhen"])
            if planned_when is None:
                continue

            scheduled: str = planned_when.time().isoformat("minutes")
            expected: str = when.time().isoformat("minutes")
            delay: int = int((when - planned_when).total_seconds() // 60)

            departures.append(Departure(line_name, direction, scheduled, expected, delay))
        except KeyError:
            continue

    departures.sort(key=lambda e: (e.expected, e.scheduled, e.line))
    return departures
