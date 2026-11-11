"""Интерфейс командной строки."""

import argparse
import sys

from .cargo_index import CargoIndex, RegistryError
from .config import DEFAULT_CONFIG, ConfigError, load_config

EXIT_OK = 0
EXIT_DATA_ERROR = 1
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
    parser.add_argument(
        "--show-config", action="store_true",
        help="вывести все параметры конфигурации (этап 1)",
    )
    return parser


def print_direct(config, index, out):
    """Вывести прямые зависимости заданной версии пакета (этап 2)."""
    deps = index.dependencies(config.package, config.version)
    required = [dep for dep in deps if dep.is_required()]
    print(f"Пакет {config.package} {config.version} "
          f"(репозиторий {index.url})", file=out)
    print(f"Прямые зависимости: {len(required)}", file=out)
    for dep in sorted(required, key=lambda item: item.name):
        print(f"  {dep.describe()}", file=out)
    skipped = len(deps) - len(required)
    if skipped:
        print(f"Не учитываются (dev или optional): {skipped}", file=out)


def execute(config, out):
    """Выполнить анализ по настройкам."""
    if config.test_mode:
        print("Тестовый режим будет поддержан на этапе 3.", file=out)
        return
    print_direct(config, CargoIndex(config.repository), out)


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
    if args.show_config:
        for line in config.describe():
            print(line, file=out)
    try:
        execute(config, out)
    except RegistryError as problem:
        print(f"Ошибка получения данных: {problem}", file=err)
        return EXIT_DATA_ERROR
    return EXIT_OK
