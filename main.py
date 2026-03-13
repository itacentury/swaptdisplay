from typing import Any, Final
from datetime import datetime, timedelta
import dateparser
import httpx

from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, DataTable

BARFUESSERBRUECKE: Final[int] = 780110
MORITZPLATZ: Final[int] = 780230
HALLE_SAALE: Final[int] = 8010159

class AppDisplay(App):
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield DataTable()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns(("Linie", "linie_col"), ("Ziel", "ziel_col"), ("Soll", "soll_col"), ("Ist", "ist_col"), ("Verspätung", "verspaetung_col"))

        url: str = f"https://v6.db.transport.rest/stops/{MORITZPLATZ}/departures"

        with httpx.Client() as client:
            response = client.get(url)
            if response.status_code != 200:
                print(response.status_code)
                return

            data = response.json()
            data_tuples = get_data_tuples(data)
            if data_tuples is None:
                return
            
            table.add_rows(data_tuples)

        self.set_interval(30, self.update_table)

    @work(exclusive=True)
    async def update_table(self) -> None:
        table = self.query_one(DataTable)
        url: str = f"https://v6.db.transport.rest/stops/{MORITZPLATZ}/departures"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code != 200:
                return
            
            data = response.json()
            data_tuples = get_data_tuples(data)
            if data_tuples is None:
                return
            

            for i, row in enumerate(table.rows):
                for j, col in enumerate(["linie_col", "ziel_col", "soll_col", "ist_col", "verspaetung_col"]):
                    table.update_cell(row, col, data_tuples[i][j])

        self.notify("Updated table!")

    def action_toggle_dark(self) -> None:
        self.theme = ("textual-dark" if self.theme == "textual-light" else "textual-light")

def get_data_tuples(data: Any) -> list[tuple] | None:
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
        delay_formatted: int = delay.seconds // 60

        processed_data.append((name, direction, plannedWhen_formatted, when_formatted, delay_formatted))

    return processed_data

def main() -> None:
    app = AppDisplay()
    app.run()


if __name__ == "__main__":
    main()
