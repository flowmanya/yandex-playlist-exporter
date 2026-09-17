import sys

from app.cli import run_cli
from app.gui import run_gui


def main():
    if len(sys.argv) > 1:
        return run_cli(sys.argv[1])

    run_gui()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
