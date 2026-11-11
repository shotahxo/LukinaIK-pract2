"""Версии и требования к версиям в формате Cargo (SemVer).

Поддерживаются требования, которые встречаются в индексе crates.io:
``^1.2.3``, ``1.2`` (то же, что ``^``), ``~1.2``, ``=1.2.3``,
``>=1.0, <2.0``, ``1.*``, ``*``.
"""

import re

VERSION_RE = re.compile(
    r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$"
)
COMPARATOR_RE = re.compile(
    r"^(\^|~|=|>=|<=|>|<)?\s*(\d+|\*|x|X)(?:\.(\d+|\*|x|X))?"
    r"(?:\.(\d+|\*|x|X))?(?:-([0-9A-Za-z.-]+))?$"
)
WILDCARDS = {"*", "x", "X"}
PARTS = 3
ONE_PART = 1
MAJOR, MINOR = range(ONE_PART + 1)


class VersionError(Exception):
    """Неверная запись версии или требования к версии."""


def _identifier_key(part):
    """Ключ сравнения одной части pre-release."""
    return (0, int(part), "") if part.isdigit() else (1, 0, part)


class Version:
    """Версия SemVer с поддержкой сравнения."""

    def __init__(self, text):
        """Разобрать строку вида ``1.2.3[-pre][+build]``."""
        match = VERSION_RE.match(text.strip())
        if match is None:
            raise VersionError(f"неверная версия: {text!r}")
        self.text = text.strip()
        self.numbers = tuple(int(match.group(i + 1)) for i in range(PARTS))
        self.pre = match.group(4) or ""

    def key(self):
        """Ключ для сравнения версий по правилам SemVer."""
        pre_key = tuple(_identifier_key(p) for p in self.pre.split("."))
        return self.numbers + ((0, pre_key) if self.pre else (1, ()),)

    def __lt__(self, other):
        """Сравнение «меньше»."""
        return self.key() < other.key()

    def __eq__(self, other):
        """Сравнение на равенство."""
        return isinstance(other, Version) and self.key() == other.key()

    def __hash__(self):
        """Хеш для использования в множествах."""
        return hash(self.key())

    def __repr__(self):
        """Отладочное представление."""
        return f"Version({self.text!r})"

    def __str__(self):
        """Строка версии."""
        return self.text


def _bound(numbers, pre=""):
    """Создать версию-границу из трёх чисел."""
    text = ".".join(str(n) for n in numbers)
    return Version(f"{text}-{pre}" if pre else text)


def _bump(numbers, index):
    """Увеличить часть ``index`` и обнулить следующие."""
    bumped = list(numbers[:index]) + [numbers[index] + 1]
    return _bound(bumped + [0] * (PARTS - len(bumped)))


def _caret_upper(numbers, given):
    """Верхняя граница для ``^``: увеличить первую ненулевую часть."""
    for index in range(given):
        if numbers[index]:
            return _bump(numbers, index)
    return _bump(numbers, given - 1)


def _parse_parts(match):
    """Числа версии, количество явных частей и признак шаблона ``*``."""
    numbers = []
    wildcard = False
    for part in (match.group(2), match.group(3), match.group(4)):
        if part is None:
            break
        if part in WILDCARDS:
            wildcard = True
            break
        numbers.append(int(part))
    given = len(numbers)
    return numbers + [0] * (PARTS - given), given, wildcard


def _exact(numbers, given, low):
    """Оператор ``=`` (и шаблоны ``1.*``)."""
    if given == PARTS:
        return [("=", low)]
    return [(">=", low), ("<", _bump(numbers, given - 1))]


def _tilde(numbers, given, low):
    """Оператор ``~``: разрешены изменения patch (или minor для ``~1``)."""
    index = MAJOR if given == ONE_PART else MINOR
    return [(">=", low), ("<", _bump(numbers, index))]


def _caret(numbers, given, low):
    """Оператор ``^`` (по умолчанию): совместимые версии."""
    return [(">=", low), ("<", _caret_upper(numbers, given))]


def _greater(numbers, given, low):
    """Оператор ``>``."""
    if given == PARTS:
        return [(">", low)]
    return [(">=", _bump(numbers, given - 1))]


def _less_equal(numbers, given, low):
    """Оператор ``<=``."""
    if given == PARTS:
        return [("<=", low)]
    return [("<", _bump(numbers, given - 1))]


OPERATORS = {
    "=": _exact,
    "~": _tilde,
    "^": _caret,
    ">": _greater,
    "<=": _less_equal,
    ">=": lambda numbers, given, low: [(">=", low)],
    "<": lambda numbers, given, low: [("<", low)],
}


class Requirement:
    """Требование к версии, например ``^1.0`` или ``>=1.2, <2``."""

    def __init__(self, text):
        """Разобрать требование."""
        self.text = text.strip() or "*"
        self.bounds = []
        self.allows_pre = "-" in self.text
        for item in self.text.split(","):
            self.bounds.extend(self._parse_item(item.strip()))

    def _parse_item(self, item):
        """Разобрать одно условие требования."""
        if item in WILDCARDS:
            return []
        match = COMPARATOR_RE.match(item)
        if match is None:
            raise VersionError(f"неверное требование: {self.text!r}")
        numbers, given, wildcard = _parse_parts(match)
        if not given:
            return []
        op = match.group(1) or ("=" if wildcard else "^")
        low = _bound(numbers, match.group(5) or "")
        return OPERATORS[op](numbers, given, low)

    def matches(self, version):
        """Проверить, подходит ли версия под требование."""
        if version.pre and not self.allows_pre:
            return False
        return all(_check(op, version, bound) for op, bound in self.bounds)

    def __str__(self):
        """Исходная запись требования."""
        return self.text


def _check(op, version, bound):
    """Проверить одно условие."""
    checks = {
        "=": version == bound,
        ">=": not version < bound,
        ">": bound < version,
        "<": version < bound,
        "<=": not bound < version,
    }
    return checks[op]


def best_match(requirement, versions):
    """Наибольшая версия из списка, подходящая под требование."""
    suitable = [v for v in versions if requirement.matches(v)]
    return max(suitable) if suitable else None
