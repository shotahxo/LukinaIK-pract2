"""Интерфейс командной строки."""

import argparse
import sys

from .cargo_index import CargoIndex, RegistryError
from .config import DEFAULT_CONFIG, ConfigError, load_config
from .ascii_tree import ascii_tree
from .graph import Settings, build_graph, find_cycles
from .mermaid import to_mermaid
from .report import print_graph
from .reverse import build_reverse_graph, print_reverse
from .sources import CargoSource
from .svg import save_svg
from .test_repo import RepositoryError, TestRepositorySource, load_repository

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
    parser.add_argument(
        "--direct", action="store_true",
        help="вывести только прямые зависимости (этап 2)",
    )
    parser.add_argument(
        "--levels", action="store_true",
        help="вывести уровни и рёбра графа (этап 3)",
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


def make_source(config):
    """Создать источник зависимостей: тестовый файл или индекс Cargo."""
    if config.test_mode:
        graph = load_repository(config.repository)
        return TestRepositorySource(graph, config.package)
    index = CargoIndex(config.repository)
    return CargoSource(index, config.package, config.version)


def visualize(config, source, graph, out):
    """Вывести ASCII-дерево и Mermaid, сохранить SVG (этап 5)."""
    if config.ascii_tree:
        print("\n".join(ascii_tree(graph, source.label)), file=out)
        print(file=out)
    print(to_mermaid(graph, source.label), file=out)
    for cycle in find_cycles(graph):
        path = " -> ".join(source.label(node) for node in cycle)
        print(f"Циклическая зависимость: {path}", file=out)
    try:
        save_svg(graph, source.label, config.output_image)
    except OSError as problem:
        raise RegistryError(f"не удалось сохранить {config.output_image}: "
                            f"{problem.strerror}") from problem
    print(f"Изображение графа сохранено: {config.output_image}", file=out)


def execute(config, out, direct=False, levels=False):
    """Выполнить анализ по настройкам."""
    if direct and not config.test_mode:
        print_direct(config, CargoIndex(config.repository), out)
        return
    settings = Settings(config.max_depth, config.filter_substring)
    if config.reverse_deps:
        show_reverse(config, settings, out)
        return
    source = make_source(config)
    graph = build_graph(source, settings)
    if levels:
        print_graph(graph, source, settings, out)
        return
    visualize(config, source, graph, out)


def show_reverse(config, settings, out):
    """Режим обратных зависимостей (этап 4, тестовый репозиторий)."""
    if not config.test_mode:
        raise RegistryError("обратные зависимости поддерживаются для "
                            "тестового репозитория (test_mode: true): "
                            "для crates.io потребовался бы весь индекс")
    repo = load_repository(config.repository)
    TestRepositorySource(repo, config.package)
    _source, reverse = build_reverse_graph(repo, config.package, settings)
    print_reverse(reverse, out)


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
        execute(config, out, args.direct, args.levels)
    except (RegistryError, RepositoryError) as problem:
        print(f"Ошибка получения данных: {problem}", file=err)
        return EXIT_DATA_ERROR
    return EXIT_OK
