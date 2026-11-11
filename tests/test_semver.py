"""Тесты версий и требований SemVer."""

import unittest

from depviz.semver import Requirement, Version, VersionError, best_match

CASES = [
    ("^1.2.3", "1.9.0", True), ("^1.2.3", "2.0.0", False),
    ("^0.2.3", "0.2.9", True), ("^0.2.3", "0.3.0", False),
    ("^0.0.3", "0.0.4", False), ("1.0", "1.5.0", True),
    ("~1.2.3", "1.2.9", True), ("~1.2.3", "1.3.0", False),
    ("~1", "1.9.0", True), ("=1.2.3", "1.2.4", False),
    (">=1.0, <2.0", "1.5.0", True), (">=1.0, <2.0", "2.0.0", False),
    (">1.2", "1.2.9", False), ("<=1.2", "1.2.9", True),
    ("1.*", "1.4.0", True), ("1.2.*", "1.3.0", False),
    ("*", "9.9.9", True), ("^1.0", "1.1.0-beta", False),
]


class SemverTests(unittest.TestCase):
    """Сравнение версий и проверка требований."""

    def test_requirements(self):
        """Таблица требований и версий."""
        for req, version, expected in CASES:
            with self.subTest(req=req, version=version):
                self.assertEqual(
                    Requirement(req).matches(Version(version)), expected)

    def test_ordering(self):
        """Pre-release младше релиза."""
        versions = [Version(v) for v in ("1.0.0", "1.0.0-beta", "0.9.9")]
        self.assertEqual([str(v) for v in sorted(versions)],
                         ["0.9.9", "1.0.0-beta", "1.0.0"])

    def test_best_match(self):
        """Выбор наибольшей подходящей версии."""
        versions = [Version(v) for v in ("1.0.1", "1.4.2", "2.0.0")]
        self.assertEqual(str(best_match(Requirement("^1"), versions)),
                         "1.4.2")
        self.assertIsNone(best_match(Requirement("^3"), versions))

    def test_errors(self):
        """Неверные версии и требования."""
        with self.assertRaises(VersionError):
            Version("1.0")
        with self.assertRaises(VersionError):
            Requirement("abc")


if __name__ == "__main__":
    unittest.main()
