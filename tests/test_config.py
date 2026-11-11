"""Тесты чтения YAML и проверки параметров (этап 1)."""

import io
import unittest

from depviz.cli import EXIT_CONFIG_ERROR, EXIT_OK, run
from depviz.config import ConfigError, build_config, load_config
from depviz.yaml_lite import YamlError, loads
from fixture_case import FixtureCase


class YamlTests(unittest.TestCase):
    """Разбор упрощённого YAML."""

    def test_scalars(self):
        """Строки, числа, логические значения, null и комментарии."""
        data = loads(
            "# comment\n"
            "a: text   # tail\n"
            "b: 'quoted # not comment'\n"
            "c: 42\n"
            "d: true\n"
            "e: no\n"
            "f:\n"
            "g: \"\"\n"
        )
        self.assertEqual(data, {
            "a": "text", "b": "quoted # not comment", "c": 42,
            "d": True, "e": False, "f": None, "g": "",
        })

    def test_version_stays_string(self):
        """Версия 1.0.120 остаётся строкой."""
        self.assertEqual(loads("version: 1.0.120"), {"version": "1.0.120"})

    def test_errors(self):
        """Синтаксические ошибки сообщают номер строки."""
        cases = ["just text", "a: 1\na: 2", "a:\n  b: 1", "a: [1, 2]",
                 "a: 'open"]
        for text in cases:
            with self.assertRaises(YamlError, msg=text):
                loads(text)


class ConfigTests(FixtureCase):
    """Проверка параметров конфигурации."""

    def prepare(self):
        """Тестовый репозиторий и корректный набор параметров."""
        self.repo = self.make_file("A: B\nB:\n")
        self.valid = {"package": "A", "repository": self.repo,
                      "test_mode": True}

    def config_with(self, **changes):
        """Собрать конфигурацию из корректного набора с изменениями."""
        data = dict(self.valid, **changes)
        return build_config({k: v for k, v in data.items() if v != "-"})

    def test_defaults(self):
        """Необязательные параметры получают значения по умолчанию."""
        config = self.config_with()
        self.assertEqual(config.output_image, "graph.svg")
        self.assertEqual(config.max_depth, 5)
        self.assertFalse(config.ascii_tree)

    def test_real_mode(self):
        """Обычный режим: URL и версия."""
        config = self.config_with(test_mode=False, version="1.0.120",
                                  repository="https://index.crates.io")
        self.assertEqual(config.version, "1.0.120")

    def test_describe(self):
        """Вывод всех параметров в формате ключ = значение."""
        lines = self.config_with().describe()
        self.assertEqual(len(lines), len(self.config_with().items()))
        self.assertIn("package = 'A'", lines)

    def test_invalid_values(self):
        """Ошибка для каждого параметра."""
        cases = [
            {"package": "-"},
            {"package": "bad name"},
            {"repository": "/no/such/file"},
            {"test_mode": False, "repository": "ftp://x", "version": "1.0.0"},
            {"test_mode": "maybe"},
            {"test_mode": False, "repository": "https://x", "version": "1.0"},
            {"output_image": "graph.png"},
            {"output_image": ".svg"},
            {"ascii_tree": 1},
            {"max_depth": 0},
            {"max_depth": True},
            {"max_depth": "deep"},
            {"filter_substring": 5},
            {"colour": "red"},
        ]
        for changes in cases:
            with self.assertRaises(ConfigError, msg=changes):
                self.config_with(**changes)

    def test_load_errors(self):
        """Отсутствующий файл и синтаксическая ошибка."""
        with self.assertRaises(ConfigError):
            load_config("/no/such/config.yaml")
        with self.assertRaises(ConfigError):
            load_config(self.make_file("oops", ".yaml"))


class CliTests(FixtureCase):
    """Запуск из командной строки."""

    def test_prints_parameters(self):
        """С ключом --show-config выводятся все параметры."""
        repo = self.make_file("A:\n")
        path = self.make_file(
            f"package: A\nrepository: {repo}\ntest_mode: true\n", ".yaml")
        out = io.StringIO()
        self.assertEqual(run(["-c", path, "--show-config"], out=out),
                         EXIT_OK)
        self.assertIn("max_depth = 5", out.getvalue())

    def test_error_exit_code(self):
        """Ошибка конфигурации — код 2 и сообщение в stderr."""
        err = io.StringIO()
        code = run(["-c", "/no/such.yaml"], err=err)
        self.assertEqual(code, EXIT_CONFIG_ERROR)
        self.assertIn("Ошибка конфигурации", err.getvalue())


if __name__ == "__main__":
    unittest.main()
