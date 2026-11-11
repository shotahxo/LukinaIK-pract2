"""Параметры приложения: чтение YAML-файла и проверка значений."""

import os
import re
from dataclasses import dataclass, fields

from .yaml_lite import YamlError, loads

PACKAGE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
VERSION_PATTERN = re.compile(
    r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$"
)
URL_PREFIXES = ("http://", "https://")
IMAGE_SUFFIX = ".svg"
MIN_DEPTH = 1
MAX_DEPTH = 100
DEFAULT_CONFIG = "config.yaml"


class ConfigError(Exception):
    """Ошибка в параметрах конфигурации."""


@dataclass
class Config:
    """Настройки анализа зависимостей."""

    package: str = ""
    repository: str = ""
    test_mode: bool = False
    version: str = ""
    output_image: str = "graph.svg"
    ascii_tree: bool = False
    max_depth: int = 5
    filter_substring: str = ""

    def items(self):
        """Пары (имя параметра, значение) в порядке объявления."""
        return [(item.name, getattr(self, item.name)) for item in fields(self)]

    def describe(self):
        """Строки вида ``ключ = значение`` для всех параметров."""
        return [f"{name} = {value!r}" for name, value in self.items()]


REQUIRED_KEYS = ("package", "repository")
TYPE_NAMES = {bool: "true или false", int: "целое число", str: "строка"}


def require_type(name, value, expected):
    """Проверить тип значения параметра."""
    wrong_bool = isinstance(value, bool) and expected is not bool
    if wrong_bool or not isinstance(value, expected):
        raise ConfigError(f"{name}: ожидается {TYPE_NAMES[expected]}, "
                          f"получено {value!r}")
    return value


def check_package(config):
    """Имя пакета: непустое, из букв, цифр, «_» и «-»."""
    if not PACKAGE_PATTERN.match(config.package):
        raise ConfigError(f"package: недопустимое имя пакета "
                          f"{config.package!r}")


def check_repository(config):
    """Репозиторий: URL в обычном режиме, файл — в тестовом."""
    if config.test_mode:
        if not os.path.isfile(config.repository):
            raise ConfigError(f"repository: файл тестового репозитория "
                              f"не найден: {config.repository}")
    elif not config.repository.startswith(URL_PREFIXES):
        raise ConfigError(f"repository: ожидался URL http(s)://, "
                          f"получено {config.repository!r}")


def check_version(config):
    """Версия: обязательна в обычном режиме, формат X.Y.Z."""
    if config.test_mode and not config.version:
        return
    if not VERSION_PATTERN.match(config.version):
        raise ConfigError(f"version: ожидалась версия вида 1.2.3, "
                          f"получено {config.version!r}")


def check_output_image(config):
    """Файл изображения: непустое имя с расширением .svg."""
    name = os.path.basename(config.output_image)
    if not name.lower().endswith(IMAGE_SUFFIX) or name == IMAGE_SUFFIX:
        raise ConfigError(f"output_image: ожидалось имя файла *.svg, "
                          f"получено {config.output_image!r}")


def check_max_depth(config):
    """Глубина анализа: целое число в допустимых пределах."""
    if not MIN_DEPTH <= config.max_depth <= MAX_DEPTH:
        raise ConfigError(f"max_depth: ожидалось число от {MIN_DEPTH} "
                          f"до {MAX_DEPTH}, получено {config.max_depth}")


CHECKS = (check_package, check_repository, check_version,
          check_output_image, check_max_depth)


def build_config(data):
    """Создать ``Config`` из словаря с проверкой всех параметров."""
    defaults = Config()
    known = {name for name, _value in defaults.items()}
    unknown = sorted(set(data) - known)
    if unknown:
        raise ConfigError(f"неизвестные параметры: {', '.join(unknown)}")
    missing = [key for key in REQUIRED_KEYS if data.get(key) is None]
    if missing:
        raise ConfigError(f"не заданы обязательные параметры: "
                          f"{', '.join(missing)}")
    values = {}
    for name, default in defaults.items():
        value = data.get(name)
        if value is None:
            value = default
        values[name] = require_type(name, value, type(default))
    config = Config(**values)
    for check in CHECKS:
        check(config)
    return config


def load_config(path=DEFAULT_CONFIG):
    """Прочитать и проверить файл конфигурации."""
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError as problem:
        raise ConfigError(f"не удалось открыть файл конфигурации "
                          f"{path}: {problem.strerror}") from problem
    try:
        data = loads(text)
    except YamlError as problem:
        raise ConfigError(f"ошибка в {path}, {problem}") from problem
    return build_config(data)
