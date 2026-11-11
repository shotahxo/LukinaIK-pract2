"""Чтение простого YAML-файла конфигурации без сторонних библиотек.

Поддерживается подмножество YAML, достаточное для файла настроек:
плоское отображение ``ключ: значение``, комментарии ``#``, пустые
строки, строки в одинарных и двойных кавычках, логические значения,
целые числа и ``null``. Вложенные структуры и списки не поддерживаются
и считаются ошибкой.
"""

import re

KEY_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:(.*)$")
INTEGER_PATTERN = re.compile(r"^[+-]?\d+$")
TRUE_WORDS = {"true", "yes", "on"}
FALSE_WORDS = {"false", "no", "off"}
NULL_WORDS = {"", "~", "null"}
QUOTES = ("'", '"')
COMMENT = "#"
MIN_QUOTED_LENGTH = 2
COMPLEX_MARKERS = "[{&*|>"


class YamlError(Exception):
    """Синтаксическая ошибка в файле конфигурации."""

    def __init__(self, line_number, message):
        """Сохранить номер строки и текст ошибки."""
        super().__init__(f"строка {line_number}: {message}")
        self.line_number = line_number


def strip_comment(text):
    """Удалить комментарий ``# ...`` вне кавычек."""
    quote = None
    for index, char in enumerate(text):
        if quote:
            quote = None if char == quote else quote
        elif char in QUOTES:
            quote = char
        elif char == COMMENT and (not index or text[index - 1].isspace()):
            return text[:index]
    return text


def parse_quoted(text, line_number):
    """Разобрать строку в кавычках."""
    quote = text[0]
    if len(text) < MIN_QUOTED_LENGTH or text[-1] != quote:
        raise YamlError(line_number, f"незакрытая кавычка: {text}")
    return text[1:-1]


def parse_scalar(text, line_number):
    """Преобразовать текст значения в str, int, bool или None."""
    if text[:1] in QUOTES:
        return parse_quoted(text, line_number)
    if text and text[0] in COMPLEX_MARKERS:
        raise YamlError(line_number, f"сложные значения не поддерживаются: "
                                     f"{text}")
    lowered = text.lower()
    if lowered in NULL_WORDS:
        return None
    if lowered in TRUE_WORDS:
        return True
    if lowered in FALSE_WORDS:
        return False
    if INTEGER_PATTERN.match(text):
        return int(text)
    return text


def parse_line(raw, line_number):
    """Разобрать одну строку; вернуть (ключ, значение) или None."""
    text = strip_comment(raw).rstrip()
    if not text.strip():
        return None
    if text[0].isspace():
        raise YamlError(line_number, "вложенные структуры не поддерживаются")
    match = KEY_PATTERN.match(text)
    if match is None:
        raise YamlError(line_number, f"ожидалось «ключ: значение»: {text}")
    key, value = match.group(1), match.group(2).strip()
    return key, parse_scalar(value, line_number)


def loads(text):
    """Разобрать текст YAML и вернуть словарь."""
    result = {}
    for line_number, raw in enumerate(text.splitlines(), start=1):
        pair = parse_line(raw, line_number)
        if pair is None:
            continue
        key, value = pair
        if key in result:
            raise YamlError(line_number, f"повторяющийся ключ: {key}")
        result[key] = value
    return result
