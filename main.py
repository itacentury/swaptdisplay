import requests
# import json
from requests import Response
from typing import Any, Final
from datetime import datetime, timedelta
import dateparser

BARFUESSERBRUECKE: Final[int] = 780110
MORITZPLATZ: Final[int] = 780230
HALLE_SAALE: Final[int] = 8010159

def get_posts(id: int) -> Any | None:
    url: str = f"https://v6.db.transport.rest/stops/{id}/departures"

    try:
        response: Response = requests.get(url)

        if response.status_code == 200:
            posts: Any = response.json()
            return posts
        else:
            print(f"Error: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def main() -> None:
    data: Any | None = get_posts(MORITZPLATZ)

    if data is None:
        return
    
    now: datetime = datetime.now()
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

        print(f"Linie: {name}")
        print(f"Ziel: {direction}")
        print(f"Soll Ankunft: {plannedWhen.time().isoformat("minutes")} Uhr")
        print(f"Ist Ankunft:  {when.time().isoformat("minutes")} Uhr")
        print(f"Verspätung:   {delay.seconds // 60} min")

        print("-" * 50)

if __name__ == "__main__":
    main()
