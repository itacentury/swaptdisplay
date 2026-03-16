"""TUI application for displaying real-time public transport departures."""

from typing import ClassVar, Final

import httpx
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable, Footer, Header, Select

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
    """Main TUI app that displays live departure tables."""

    CSS_PATH: ClassVar[str] = "app.tcss"
    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        ("t", "toggle_second", "Toggle second station")
    ]

    def __init__(
        self,
        first_station: str | int,
        second_station: str | int,
        show_second: bool = False,
    ) -> None:
        super().__init__()
        self._first_station: Station = self._resolve_station(
            first_station, "Augsburg Hbf"
        )
        self._second_station: Station = self._resolve_station(
            second_station, "Königsplatz"
        )
        self._show_second: bool = show_second
        self._client: httpx.AsyncClient = httpx.AsyncClient(timeout=10)
        self.title = "Swapt Display"

    def _resolve_station(self, station: str | int, fallback_name: str) -> Station:
        """Resolve a station name or ID to a Station, falling back to the given name."""
        return (
            STATIONS_BY_NAME.get(station.lower(), STATIONS_BY_NAME[fallback_name.lower()])
            if isinstance(station, str)
            else STATIONS_BY_ID.get(station, STATIONS_BY_NAME[fallback_name.lower()])
        )

    def compose(self) -> ComposeResult:
        """Compose the layout with header, station panels, and footer."""
        yield Header()
        with Vertical(id="firstPanel"):
            yield Select(
                ((station.name, station) for station in STATIONS),
                allow_blank=False,
                value=self._first_station,
                type_to_search=True,
                id="firstSelect",
            )
            yield DataTable(id="firstTable")
        with Vertical(id="secondPanel"):
            yield Select(
                ((station.name, station) for station in STATIONS),
                allow_blank=False,
                value=self._second_station,
                type_to_search=True,
                id="secondSelect",
            )
            yield DataTable(id="secondTable")
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the table columns and load initial departure data."""
        tables: list[DataTable] = []
        tables.append(self.query_one("#firstTable", DataTable))
        tables.append(self.query_one("#secondTable", DataTable))

        for table in tables:
            table.loading = True
            table.zebra_stripes = True
            table.cursor_type = "row"
            table.add_columns("Linie", "Ziel", "Soll", "Ist", "Verspätung")

        if not self._show_second:
            panel: Vertical = self.query_one("#secondPanel", Vertical)
            panel.display = False

        self.update_all_tables()
        self.set_interval(10, self.update_all_tables)

    async def on_unmount(self) -> None:
        """Close the HTTP client on app shutdown."""
        await self._client.aclose()

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        """Handle station selection change and trigger a table refresh."""
        if event.value is Select.BLANK:
            return

        if event.select.id == "firstSelect":
            table: DataTable = self.query_one("#firstTable", DataTable)
            table.loading = True

            self._first_station = event.value  # type: ignore[assignment]
            self.update_first_table()
        elif event.select.id == "secondSelect":
            table = self.query_one("#secondTable", DataTable)
            table.loading = True

            self._second_station = event.value  # type: ignore[assignment]
            self.update_second_table()

    def action_toggle_second(self) -> None:
        """Toggle visibility of the second station panel and refresh its data."""
        panel: Vertical = self.query_one("#secondPanel", Vertical)
        panel.display = not panel.display
        self._show_second = panel.display
        if not self._show_second:
            return

        self.update_second_table()

    def update_all_tables(self) -> None:
        """Trigger a refresh of all visible station tables."""
        self.update_first_table()
        self.update_second_table()

    @work(exclusive=True, group="update_first")
    async def update_first_table(self) -> None:
        """Fetch and display departures for the first station."""
        table: DataTable = self.query_one("#firstTable", DataTable)
        departures: list[Departure] | None = await get_departures(
            self._client, self._first_station.station_id
        )

        if not departures:
            return

        await self.update_table(table, departures)

    @work(exclusive=True, group="update_second")
    async def update_second_table(self) -> None:
        """Fetch and display departures for the second station if visible."""
        if not self._show_second:
            return

        table: DataTable = self.query_one("#secondTable", DataTable)
        departures: list[Departure] | None = await get_departures(
            self._client, self._second_station.station_id
        )

        if not departures:
            return

        await self.update_table(table, departures)

    async def update_table(self, table: DataTable, departures: list[Departure]) -> None:
        """Clear and repopulate a table with styled departure rows."""
        table.clear()
        table.add_rows([self._style_departure(d) for d in departures])
        table.loading = False

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
