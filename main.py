from datetime import datetime, timedelta
from typing import Any, Final

import dateparser
import httpx
from textual import work
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header

BARFUESSERBRUECKE: Final[int] = 780110
MORITZPLATZ: Final[int] = 780230
HALLE_SAALE: Final[int] = 8010159


class SwaptDisplay(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield DataTable()

    async def on_mount(self) -> None:
        table: DataTable = self.query_one(DataTable)
        table.add_columns(
            ("Linie", "linie_col"),
            ("Ziel", "ziel_col"),
            ("Soll", "soll_col"),
            ("Ist", "ist_col"),
            ("Verspätung", "verspaetung_col"),
        )

        data: list[tuple[str, str, str, str, int]] | None = await get_data()
        if data is None:
            return

        table.add_rows(data)

        self.set_interval(30, self.update_table)

    @work(exclusive=True)
    async def update_table(self) -> None:
        table: DataTable = self.query_one(DataTable)
        data: list[tuple[str, str, str, str, int]] | None = await get_data()
        if data is None:
            return

        for i, row in enumerate(table.rows):
            for j, col in enumerate(
                ["linie_col", "ziel_col", "soll_col", "ist_col", "verspaetung_col"]
            ):
                table.update_cell(row, col, data[i][j])

        self.notify("Updated table!")


async def get_data() -> list[tuple[str, str, str, str, int]] | None:
    url: str = f"https://v6.db.transport.rest/stops/{MORITZPLATZ}/departures"

    async with httpx.AsyncClient() as client:
        response: httpx.Response = await client.get(url)
        if response.status_code != 200:
            return None

        data: Any = response.json()
        formatted_data: list[tuple[str, str, str, str, int]] | None = format_data(data)

        return formatted_data


def format_data(data: Any) -> list[tuple[str, str, str, str, int]] | None:
    if not data:
        return None

    now: datetime = datetime.now()
    processed_data: list[tuple] = []
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
            plannedWhen: datetime | None = dateparser.parse(entry["plannedWhen"])
        except TypeError:
            continue

        if plannedWhen is None:
            continue

        delay: timedelta = when - plannedWhen

        plannedWhen_formatted: str = plannedWhen.time().isoformat("minutes")
        when_formatted: str = when.time().isoformat("minutes")
        delay_formatted: int = int(delay.total_seconds() // 60)

        processed_data.append(
            (name, direction, plannedWhen_formatted, when_formatted, delay_formatted)
        )

    return processed_data


def main() -> None:
    app = SwaptDisplay()
    app.run()


if __name__ == "__main__":
    main()
