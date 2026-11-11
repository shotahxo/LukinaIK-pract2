"""Тесты получения прямых зависимостей из индекса Cargo (этап 2)."""

import io
import unittest
from unittest import mock

from depviz.cargo_index import (CargoIndex, RegistryError, index_path,
                                parse_index_file)
from depviz.cli import execute
from depviz.config import Config
from sample_index import URL, make_index


class IndexPathTests(unittest.TestCase):
    """Пути к файлам в индексе crates.io."""

    def test_paths(self):
        """Правила для имён длиной 1, 2, 3 и больше."""
        self.assertEqual(index_path("a"), "1/a")
        self.assertEqual(index_path("ab"), "2/ab")
        self.assertEqual(index_path("abc"), "3/a/abc")
        self.assertEqual(index_path("Serde_JSON"), "se/rd/serde_json")


class DependencyTests(unittest.TestCase):
    """Разбор зависимостей."""

    def test_direct_dependencies(self):
        """Все зависимости версии и отбор нужных для сборки."""
        deps = make_index().dependencies("app", "2.0.0")
        names = {dep.name: dep for dep in deps}
        self.assertEqual(len(deps), 5)
        self.assertTrue(names["lib"].is_required())
        self.assertTrue(names["builder"].is_required())
        self.assertFalse(names["tester"].is_required())
        self.assertFalse(names["fancy"].is_required())

    def test_renamed_dependency(self):
        """Переименованная зависимость использует настоящее имя."""
        deps = make_index().dependencies("renamed", "1.0.0")
        self.assertEqual(deps[0].name, "util")

    def test_resolve(self):
        """Выбор наибольшей подходящей не отозванной версии."""
        index = make_index()
        self.assertEqual(index.resolve("lib", "^1.0"), "1.1.0")
        self.assertEqual(index.resolve("util", "^0.2"), "0.2.7")
        with self.assertRaises(RegistryError):
            index.resolve("util", "^5")

    def test_errors(self):
        """Нет пакета, нет версии, неверный формат."""
        index = make_index()
        with self.assertRaises(RegistryError):
            index.dependencies("missing", "1.0.0")
        with self.assertRaises(RegistryError):
            index.dependencies("app", "9.9.9")
        broken = CargoIndex(URL, fetch=lambda url: "not json")
        with self.assertRaises(RegistryError):
            broken.versions("app")

    def test_parse_file(self):
        """Пустые строки в файле индекса пропускаются."""
        text = '\n{"name": "x", "vers": "1.0.0", "deps": []}\n\n'
        self.assertEqual(list(parse_index_file(text)), ["1.0.0"])


class DirectOutputTests(unittest.TestCase):
    """Вывод прямых зависимостей."""

    def test_print_direct(self):
        """Выводятся только зависимости для сборки, остальные считаются."""
        out = io.StringIO()
        config = Config(package="app", repository=URL, version="2.0.0")
        with mock.patch("depviz.cli.CargoIndex",
                        lambda url: make_index()):
            execute(config, out, direct=True)
        text = out.getvalue()
        self.assertIn("Прямые зависимости: 3", text)
        self.assertIn("builder ^1 (build)", text)
        self.assertIn("Не учитываются (dev или optional): 2", text)


if __name__ == "__main__":
    unittest.main()
