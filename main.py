from datetime import datetime
from typing import Any, Final, NamedTuple

import dateparser
import httpx
from textual import work
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header

BARFUESSERBRUECKE: Final[int] = 780110
MORITZPLATZ: Final[int] = 780230
HALLE_SAALE: Final[int] = 8010159


class Departure(NamedTuple):
    line: str
    direction: str
    scheduled: str
    expected: str
    delay: int


class SwaptDisplay(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield DataTable()

    async def on_mount(self) -> None:
        table: DataTable = self.query_one(DataTable)
        table.add_columns(
            ("Linie", "line_col"),
            ("Ziel", "dest_col"),
            ("Soll", "target_col"),
            ("Ist", "actual_col"),
            ("Verspätung", "delay_col"),
        )

        data: list[Departure] | None = await get_data()
        if data is None:
            return

        table.add_rows(data)

        self.set_interval(30, self.update_table)

    @work(exclusive=True)
    async def update_table(self) -> None:
        table: DataTable = self.query_one(DataTable)
        data: list[Departure] | None = await get_data()
        if data is None:
            self.notify("Error updating table", severity="error")
            return

        for i, row in enumerate(table.rows):
            for j, col in enumerate(
                ["line_col", "dest_col", "target_col", "actual_col", "delay_col"]
            ):
                table.update_cell(row, col, data[i][j])

        self.notify("Updated table!", severity="information")


async def get_data() -> list[Departure] | None:
    url: str = f"https://v6.db.transport.rest/stops/{MORITZPLATZ}/departures"

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            response: httpx.Response = await client.get(url)
            if response.status_code != 200:
                return None

            data: Any = response.json()
            formatted_data: list[Departure] | None = format_data(data)

            return formatted_data
        except httpx.ReadTimeout:
            return None


def format_data(data: Any) -> list[Departure] | None:
    if not data:
        return None

    now: datetime = datetime.now()
    processed_data: list[Departure] = []
    for entry in data["departures"]:
        try:
            when: datetime | None = dateparser.parse(entry["when"])
        except TypeError:
            continue

        if when is None:
            continue

        if when.timestamp() < now.timestamp():
            continue

        name: str = entry["line"]["name"]
        direction: str = entry["direction"]
        try:
            planned_when: datetime | None = dateparser.parse(entry["plannedWhen"])
        except TypeError:
            continue

        if planned_when is None:
            continue

        scheduled: str = planned_when.time().isoformat("minutes")
        expected: str = when.time().isoformat("minutes")
        delay: int = int((when - planned_when).total_seconds() // 60)

        departure: Departure = Departure(name, direction, scheduled, expected, delay)

        processed_data.append(departure)

    return processed_data


def main() -> None:
    app = SwaptDisplay()
    app.run()


if __name__ == "__main__":
    main()
