"""
AudioDL launcher module.

Usage:
  python -m audiodl

This starts the Tkinter GUI defined in `yt_playlist_gui.py` and ensures the
default output directory exists.
"""

from pathlib import Path

try:
    # Import the existing GUI app without moving user files.
    from yt_playlist_gui import App, DEFAULT_OUT_DIR
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"Failed to import GUI: {exc}")


def main() -> None:
    DEFAULT_OUT_DIR.mkdir(exist_ok=True)
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()

