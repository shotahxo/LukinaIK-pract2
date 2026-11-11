"""Создать учебный мини-индекс пакетов в формате sparse-индекса Cargo.

Пакеты вымышленные (префикс ``mini-``), формат файлов такой же, как у
https://index.crates.io. Индекс нужен, чтобы показать работу с «реальным»
репозиторием без доступа к интернету::

    python3 examples/build_mini_index.py
    python3 -m http.server 8000 --directory examples/mini-index

и в config.yaml указать ``repository: http://localhost:8000``.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent
                       / "src"))

from depviz.cargo_index import index_path

TARGET = pathlib.Path(__file__).resolve().parent / "mini-index"


def dep(name, req, kind="normal", optional=False):
    """Описание зависимости в формате индекса."""
    return {"name": name, "req": req, "features": [], "optional": optional,
            "default_features": True, "target": None, "kind": kind}


PACKAGES = {
    "mini-app": {
        "1.0.0": [dep("mini-cli", "^0.3"), dep("mini-log", "^0.4")],
        "1.1.0": [dep("mini-cli", "^0.3"), dep("mini-json", "^1.2"),
                  dep("mini-log", "^0.4"), dep("mini-test", "^1", "dev"),
                  dep("mini-color", "^2", optional=True)],
    },
    "mini-cli": {
        "0.3.0": [dep("mini-str", "^1")],
        "0.3.4": [dep("mini-str", "^1"), dep("mini-log", "~0.4.1")],
        "0.4.0": [dep("mini-str", "^1")],
    },
    "mini-json": {
        "1.2.0": [dep("mini-str", "^1.1")],
        "1.2.5": [dep("mini-str", "^1.1"),
                  dep("mini-derive", "^1", "build")],
        "2.0.0": [dep("mini-str", "^1.1")],
    },
    "mini-log": {"0.4.20": [dep("mini-cfg", "^1")]},
    "mini-str": {"1.0.0": [], "1.1.3": []},
    "mini-derive": {"1.0.7": [dep("mini-str", "^1")]},
    "mini-cfg": {"1.0.0": []},
    "mini-test": {"1.0.0": []},
    "mini-color": {"2.1.0": []},
}

YANKED = {("mini-json", "2.0.0")}


def entry(name, version, deps):
    """Строка индекса для одной версии пакета."""
    return json.dumps({
        "name": name, "vers": version, "deps": deps, "cksum": "0" * 64,
        "features": {}, "yanked": (name, version) in YANKED,
    })


def main():
    """Записать файлы индекса."""
    for name, versions in PACKAGES.items():
        path = TARGET / index_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [entry(name, v, deps) for v, deps in versions.items()]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (TARGET / "config.json").write_text('{"dl": "http://localhost"}\n')
    print(f"мини-индекс создан: {TARGET}")


if __name__ == "__main__":
    main()
