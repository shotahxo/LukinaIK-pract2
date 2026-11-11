"""Тестовый репозиторий: граф пакетов из текстового файла.

Формат файла — по одной строке на пакет::

    A: B C      # пакет A зависит от B и C
    B: D
    D:          # у пакета D нет зависимостей

Имена пакетов — большие латинские буквы. Пакеты, которые встречаются
только справа от двоеточия, считаются пакетами без зависимостей.
"""

import re

NAME_RE = re.compile(r"^[A-Z]+$")
SEPARATOR = ":"
COMMENT = "#"


class RepositoryError(Exception):
    """Ошибка в файле тестового репозитория."""


def _check_name(name, line_number):
    """Проверить, что имя пакета состоит из больших латинских букв."""
    if not NAME_RE.match(name):
        raise RepositoryError(f"строка {line_number}: недопустимое имя "
                              f"пакета {name!r} (нужны A-Z)")
    return name


def _parse_line(raw, line_number):
    """Разобрать строку; вернуть (пакет, зависимости) или None."""
    text = raw.split(COMMENT, 1)[0].strip()
    if not text:
        return None
    if SEPARATOR not in text:
        raise RepositoryError(f"строка {line_number}: ожидалось "
                              f"«ПАКЕТ: ЗАВИСИМОСТИ»: {text}")
    left, right = text.split(SEPARATOR, 1)
    package = _check_name(left.strip(), line_number)
    deps = [_check_name(item, line_number) for item in right.split()]
    return package, deps


def parse_repository(text):
    """Разобрать текст репозитория: словарь «пакет → зависимости»."""
    graph = {}
    for line_number, raw in enumerate(text.splitlines(), start=1):
        parsed = _parse_line(raw, line_number)
        if parsed is None:
            continue
        package, deps = parsed
        if package in graph:
            raise RepositoryError(f"строка {line_number}: пакет {package} "
                                  f"описан повторно")
        graph[package] = deps
    return graph


def load_repository(path):
    """Прочитать файл тестового репозитория."""
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError as problem:
        raise RepositoryError(f"не удалось открыть {path}: "
                              f"{problem.strerror}") from problem
    try:
        return parse_repository(text)
    except RepositoryError as problem:
        raise RepositoryError(f"{path}, {problem}") from problem


class TestRepositorySource:
    """Источник зависимостей на основе тестового репозитория."""

    def __init__(self, graph, package):
        """Запомнить граф и корневой пакет."""
        known = set(graph) | {d for deps in graph.values() for d in deps}
        if package not in known:
            raise RepositoryError(f"пакет {package!r} не найден в "
                                  f"тестовом репозитории")
        self.graph = graph
        self.root = package

    def children(self, node):
        """Прямые зависимости пакета."""
        return list(self.graph.get(node, []))

    def name(self, node):
        """Имя пакета (для фильтрации)."""
        return node

    def label(self, node):
        """Подпись узла для вывода."""
        return node

    def all_nodes(self):
        """Все пакеты репозитория."""
        known = list(self.graph)
        for deps in self.graph.values():
            known.extend(d for d in deps if d not in known)
        return known
