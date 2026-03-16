# swaptdisplay

Terminal-based departure board for public transit, built with [Textual](https://textual.textualize.io/).
Uses the [v6.db.transport.rest](https://v6.db.transport.rest/getting-started.html) API for real-time departure data.

## Installation

Requires Python 3.14+.

```sh
uv sync
```

## Usage

```sh
uv run swaptdisplay
# or
uv run python -m swaptdisplay
```

### CLI Options

| Flag                   | Description                                                |
| ---------------------- | ---------------------------------------------------------- |
| `-s`, `--station`      | Station name (default: `Augsburg Hbf`)                     |
| `-i`, `--station-id`   | Station ID (alternative to name)                           |
| `-s2`, `--station2`    | Second station name for dual mode (default: `Königsplatz`) |
| `-i2`, `--station2-id` | Second station ID (alternative to name)                    |
| `-d`, `--dual`         | Start with both station panels visible                     |

Press `t` to toggle the second station panel at runtime.

## License

[GPLv3](LICENSE)
