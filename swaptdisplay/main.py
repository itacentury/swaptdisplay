"""Entry point for the SwaptDisplay application."""

from .app import SwaptDisplay


def main() -> None:
    """Run the SwaptDisplay application."""
    app = SwaptDisplay()
    app.run()


if __name__ == "__main__":
    main()
