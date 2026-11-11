"""Базовый класс тестов с подготовкой окружения перед каждым тестом."""

import os
import tempfile
import unittest


class FixtureCase(unittest.TestCase):
    """Тест, который перед запуском вызывает метод ``prepare``.

    Используется вместо ``setUp``, чтобы имена методов соответствовали
    PEP8 (snake_case). Также умеет создавать временные файлы.
    """

    def prepare(self):
        """Подготовить окружение теста (по умолчанию ничего не делает)."""

    def run(self, result=None):
        """Подготовить окружение и выполнить тест."""
        self.prepare()
        return super().run(result)

    def make_file(self, text, suffix=".txt"):
        """Создать временный файл с текстом и вернуть путь к нему."""
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=suffix, delete=False, encoding="utf-8")
        with handle:
            handle.write(text)
        self.addCleanup(os.remove, handle.name)
        return handle.name
