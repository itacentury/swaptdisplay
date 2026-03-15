"""TUI application for displaying real-time public transport departures."""

from typing import Final

import httpx
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Header, Select

from .api import get_departures
from .models import (
    Departure,
    Station,
    create_dict_by_id,
    create_dict_by_name,
    parse_stations,
)

STATIONS: Final[list[Station]] = parse_stations()
STATIONS_BY_NAME: Final[dict[str, Station]] = create_dict_by_name(STATIONS)
STATIONS_BY_ID: Final[dict[int, Station]] = create_dict_by_id(STATIONS)


class SwaptDisplay(App):
    """Main TUI app that displays a live departure table."""

    CSS_PATH = "app.tcss"

    def __init__(self, station_name_or_id: str | int) -> None:
        super().__init__()
        self._station: Station = (
            STATIONS_BY_NAME.get(
                station_name_or_id.lower(), STATIONS_BY_NAME["Augsburg Hbf".lower()]
            )
            if isinstance(station_name_or_id, str)
            else STATIONS_BY_ID.get(
                station_name_or_id, STATIONS_BY_NAME["Augsburg Hbf".lower()]
            )
        )

        self._client: httpx.AsyncClient = httpx.AsyncClient(timeout=10)
        self.title = "Swapt Display"

    def compose(self) -> ComposeResult:
        """Compose the layout with header, footer, and data table."""
        yield Header()
        yield Select(
            ((station.name, station) for station in STATIONS),
            allow_blank=False,
            value=self._station,
            type_to_search=True,
        )
        yield DataTable()

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        """Handle station selection change and trigger a table refresh."""
        if event.value is Select.BLANK:
            return

        table: DataTable = self.query_one(DataTable)
        table.loading = True

        self._station = event.value  # type: ignore[arg-type, call-arg, assignment]
        self.update_table()

    @staticmethod
    def _style_departure(departure: Departure) -> tuple[str, str, str, Text, Text]:
        """Convert a Departure into a styled row tuple with color-coded delay."""
        if departure.delay <= 0:
            style = "green"
        elif departure.delay <= 5:
            style = "yellow"
        else:
            style = "red"

        expected = Text(departure.expected, style=style)
        delay = Text(str(departure.delay), style=style)
        return (departure.line, departure.direction, departure.scheduled, expected, delay)

    async def on_mount(self) -> None:
        """Initialize the table columns and load initial departure data."""
        table: DataTable = self.query_one(DataTable)
        table.loading = True
        table.zebra_stripes = True
        table.cursor_type = "row"
        table.add_columns("Linie", "Ziel", "Soll", "Ist", "Verspätung")

        self.update_table()
        self.set_interval(10, self.update_table)

    async def on_unmount(self) -> None:
        """Close the HTTP client on app shutdown."""
        await self._client.aclose()

    @work(exclusive=True)
    async def update_table(self) -> None:
        """Fetch fresh data and update all table cells."""
        table: DataTable = self.query_one(DataTable)
        departures: list[Departure] | None = await get_departures(
            self._client, self._station.station_id
        )
        if not departures:
            return

        table.clear()
        table.add_rows([self._style_departure(d) for d in departures])
        table.loading = False
