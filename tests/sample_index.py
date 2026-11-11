"""Тестовый индекс Cargo в памяти (без сети)."""

import json

from depviz.cargo_index import CargoIndex, index_path

URL = "https://index.example"


def line(name, version, deps, yanked=False):
    """Строка индекса для одной версии пакета."""
    return json.dumps({"name": name, "vers": version, "deps": deps,
                       "yanked": yanked})


def dep(name, req, kind=None, optional=False, package=None):
    """Описание зависимости в формате индекса."""
    data = {"name": name, "req": req, "kind": kind, "optional": optional}
    if package:
        data["package"] = package
    return data


FILES = {
    "app": [
        line("app", "1.0.0", [dep("lib", "^1.0"), dep("util", "^0.2")]),
        line("app", "2.0.0", [
            dep("lib", "^1.1"), dep("log", "~0.4"),
            dep("tester", "^1", kind="dev"),
            dep("fancy", "^3", optional=True),
            dep("builder", "^1", kind="build"),
        ]),
    ],
    "lib": [
        line("lib", "1.0.0", [dep("util", "^0.2")]),
        line("lib", "1.1.0", [dep("util", "^0.2"), dep("log", "^0.4")]),
        line("lib", "1.2.0", [], yanked=True),
    ],
    "util": [line("util", "0.2.0", []), line("util", "0.2.7", []),
             line("util", "0.3.0", [])],
    "log": [line("log", "0.4.1", [dep("cfg", "^1")]),
            line("log", "0.4.9", [dep("cfg", "^1")])],
    "cfg": [line("cfg", "1.0.0", [dep("lib", "^1")])],
    "builder": [line("builder", "1.0.0", [])],
    "renamed": [line("renamed", "1.0.0",
                     [dep("alias", "^0.2", package="util")])],
}


def fake_fetch(url):
    """Вернуть содержимое файла индекса или None (как 404)."""
    for name, lines in FILES.items():
        if url == f"{URL}/{index_path(name)}":
            return "\n".join(lines) + "\n"
    return None


def make_index():
    """Индекс, работающий без сети."""
    return CargoIndex(URL, fetch=fake_fetch)
