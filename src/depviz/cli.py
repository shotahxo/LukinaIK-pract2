"""Интерфейс командной строки."""

import argparse
import sys

from .config import DEFAULT_CONFIG, ConfigError, load_config

EXIT_OK = 0
EXIT_CONFIG_ERROR = 2


def build_parser():
    """Описать аргументы командной строки."""
    parser = argparse.ArgumentParser(
        prog="depviz",
        description="Визуализация графа зависимостей пакетов Cargo.",
    )
    parser.add_argument(
        "-c", "--config", default=DEFAULT_CONFIG, metavar="FILE",
        help=f"YAML-файл конфигурации (по умолчанию {DEFAULT_CONFIG})",
    )
    return parser


def run(argv=None, out=None, err=None):
    """Выполнить программу и вернуть код завершения."""
    out = out or sys.stdout
    err = err or sys.stderr
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as problem:
        print(f"Ошибка конфигурации: {problem}", file=err)
        return EXIT_CONFIG_ERROR
    for line in config.describe():
        print(line, file=out)
    return EXIT_OK
