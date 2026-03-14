"""TUI application for displaying real-time public transport departures."""

from datetime import datetime
from typing import Any, Final, NamedTuple

import httpx
from textual import work
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header

BARFUESSERBRUECKE: Final[int] = 780110
MORITZPLATZ: Final[int] = 780230
HALLE_SAALE: Final[int] = 8010159

DEPARTURES_URL: Final[str] = (
    f"https://v6.db.transport.rest/stops/{MORITZPLATZ}/departures"
)


class Departure(NamedTuple):
    """Represents a single public transport departure."""

    line: str
    direction: str
    scheduled: str
    expected: str
    delay: int


class SwaptDisplay(App):
    """Main TUI app that displays a live departure table."""

    def __init__(self) -> None:
        super().__init__()
        self._client: httpx.AsyncClient = httpx.AsyncClient(timeout=10)

    def compose(self) -> ComposeResult:
        """Compose the layout with header, footer, and data table."""
        yield Header()
        yield Footer()
        yield DataTable()

    async def on_mount(self) -> None:
        """Initialize the table columns and load initial departure data."""
        table: DataTable = self.query_one(DataTable)
        table.add_columns(
            ("Linie", "line_col"),
            ("Ziel", "dest_col"),
            ("Soll", "target_col"),
            ("Ist", "actual_col"),
            ("Verspätung", "delay_col"),
        )

        data: list[Departure] | None = await get_departures(self._client)
        if data is None:
            return

        table.add_rows(data)

        self.set_interval(30, self.update_table)

    async def on_unmount(self) -> None:
        """Close the HTTP client on app shutdown."""
        await self._client.aclose()

    @work(exclusive=True)
    async def update_table(self) -> None:
        """Fetch fresh data and update all table cells."""
        table: DataTable = self.query_one(DataTable)
        departures: list[Departure] | None = await get_departures(self._client)
        if not departures:
            self.notify("Error updating table", severity="error")
            return

        for i, row in enumerate(table.rows):
            for j, col in enumerate(
                ["line_col", "dest_col", "target_col", "actual_col", "delay_col"]
            ):
                table.update_cell(row, col, departures[i][j])

        self.notify("Updated table!", severity="information")


async def get_departures(client: httpx.AsyncClient) -> list[Departure] | None:
    """Fetch departures from the transport API. Returns None on failure."""
    try:
        response: httpx.Response = await client.get(DEPARTURES_URL)
        response.raise_for_status()
        return extract_departures(response.json())
    except httpx.HTTPError:
        return None


def parse_datetime(datetime_string: str) -> datetime | None:
    """Parse an ISO 8601 datetime string. Returns None if parsing fails."""
    try:
        return datetime.fromisoformat(datetime_string)
    except ValueError:
        return None


def extract_departures(data: Any) -> list[Departure]:
    """Parse API response into a list of future departures."""
    if not data:
        return []

    departures: list[Departure] = []
    now: float = datetime.now().timestamp()
    for entry in data["departures"]:
        when: datetime | None = parse_datetime(entry["when"])
        if when is None:
            continue

        if when.timestamp() < now:
            continue

        line_name: str = entry["line"]["name"]
        direction: str = entry["direction"]
        planned_when: datetime | None = parse_datetime(entry["plannedWhen"])
        if planned_when is None:
            continue

        scheduled: str = planned_when.time().isoformat("minutes")
        expected: str = when.time().isoformat("minutes")
        delay: int = int((when - planned_when).total_seconds() // 60)

        departures.append(Departure(line_name, direction, scheduled, expected, delay))

    return departures


def main() -> None:
    """Run the SwaptDisplay application."""
    app = SwaptDisplay()
    app.run()


if __name__ == "__main__":
    main()
