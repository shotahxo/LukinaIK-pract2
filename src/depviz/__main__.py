"""Запуск: ``python3 -m depviz [-c config.yaml]``."""

import sys

from .cli import run

if __name__ == "__main__":
    sys.exit(run())
