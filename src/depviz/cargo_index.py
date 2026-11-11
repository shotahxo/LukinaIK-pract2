"""Получение зависимостей пакетов Rust из индекса реестра Cargo.

Используется «разреженный» (sparse) протокол индекса crates.io:
для каждого пакета по адресу ``<repository>/<путь>`` лежит текстовый
файл, где каждая строка — JSON-описание одной версии пакета со списком
её зависимостей. Менеджер пакетов ``cargo`` и сторонние библиотеки не
используются: файлы скачиваются через ``urllib`` и разбираются вручную.
"""

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from .semver import Requirement, Version, VersionError, best_match

ONE_LETTER = 1
TWO_LETTERS = 2
THREE_LETTERS = 3
TIMEOUT_SECONDS = 20
HTTP_NOT_FOUND = 404
USER_AGENT = "depviz/0.1 (study project)"
INCLUDED_KINDS = ("normal", "build")


class RegistryError(Exception):
    """Ошибка при получении данных из репозитория пакетов."""


@dataclass(frozen=True)
class Dependency:
    """Зависимость из описания версии пакета."""

    name: str
    requirement: str
    kind: str
    optional: bool
    target: str

    def is_required(self):
        """Нужна ли зависимость для сборки пакета (не dev, не optional)."""
        return self.kind in INCLUDED_KINDS and not self.optional

    def describe(self):
        """Строка для вывода: имя, требование, вид и признаки."""
        notes = [self.kind]
        if self.optional:
            notes.append("optional")
        if self.target:
            notes.append(f"target: {self.target}")
        return f"{self.name} {self.requirement} ({', '.join(notes)})"


def index_path(name):
    """Путь к файлу пакета в индексе по правилам Cargo."""
    lowered = name.lower()
    size = len(lowered)
    if size == ONE_LETTER:
        return f"1/{lowered}"
    if size == TWO_LETTERS:
        return f"2/{lowered}"
    if size == THREE_LETTERS:
        return f"3/{lowered[0]}/{lowered}"
    return f"{lowered[:2]}/{lowered[2:4]}/{lowered}"


def http_fetch(url):
    """Скачать текст по URL; ``None``, если файла нет (404)."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as reply:
            return reply.read().decode("utf-8")
    except urllib.error.HTTPError as problem:
        if problem.code == HTTP_NOT_FOUND:
            return None
        raise RegistryError(f"{url}: HTTP {problem.code}") from problem
    except (urllib.error.URLError, OSError) as problem:
        raise RegistryError(f"{url}: нет соединения ({problem})") from problem


def parse_dependency(raw):
    """Преобразовать JSON-описание зависимости в ``Dependency``."""
    return Dependency(
        name=raw.get("package") or raw["name"],
        requirement=raw.get("req", "*"),
        kind=raw.get("kind") or "normal",
        optional=bool(raw.get("optional")),
        target=raw.get("target") or "",
    )


def parse_index_file(text):
    """Разобрать файл индекса: словарь «версия → описание»."""
    versions = {}
    for line in text.splitlines():
        if line.strip():
            entry = json.loads(line)
            versions[entry["vers"]] = entry
    return versions


class CargoIndex:
    """Индекс пакетов Cargo, доступный по URL."""

    def __init__(self, url, fetch=http_fetch):
        """Запомнить адрес индекса и функцию загрузки."""
        self.url = url.rstrip("/")
        self.fetch = fetch
        self.cache = {}

    def versions(self, name):
        """Все версии пакета: словарь «строка версии → описание»."""
        if name not in self.cache:
            text = self.fetch(f"{self.url}/{index_path(name)}")
            if text is None:
                raise RegistryError(f"пакет {name!r} не найден в {self.url}")
            try:
                self.cache[name] = parse_index_file(text)
            except (ValueError, KeyError) as problem:
                raise RegistryError(f"неверный формат индекса для "
                                    f"{name!r}: {problem}") from problem
        return self.cache[name]

    def entry(self, name, version):
        """Описание конкретной версии пакета."""
        versions = self.versions(name)
        if version not in versions:
            latest = sorted(versions, key=Version)[-3:]
            raise RegistryError(f"версия {version} пакета {name!r} не "
                                f"найдена; последние: {', '.join(latest)}")
        return versions[version]

    def dependencies(self, name, version):
        """Все прямые зависимости версии пакета."""
        raw = self.entry(name, version).get("deps", [])
        return [parse_dependency(item) for item in raw]

    def resolve(self, name, requirement):
        """Наибольшая не отозванная версия, подходящая под требование."""
        try:
            wanted = Requirement(requirement)
        except VersionError as problem:
            raise RegistryError(f"{name}: {problem}") from problem
        candidates = [Version(v) for v, e in self.versions(name).items()
                      if not e.get("yanked")]
        found = best_match(wanted, candidates)
        if found is None:
            raise RegistryError(f"нет версии {name} под требование "
                                f"{requirement}")
        return str(found)
