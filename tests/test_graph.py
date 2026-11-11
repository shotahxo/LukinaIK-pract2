"""Тесты построения графа BFS, глубины, фильтра и циклов (этап 3)."""

import unittest

from depviz.graph import Settings, build_graph, find_cycles
from depviz.sources import CargoSource
from depviz.test_repo import (RepositoryError, TestRepositorySource,
                              parse_repository)
from fixture_case import FixtureCase
from sample_index import make_index

CYCLE = "A: B C\nB: D\nC: D E\nE: A F\nF: F\n"


def graph_of(text, package="A", depth=10, exclude=""):
    """Построить граф по тексту тестового репозитория."""
    source = TestRepositorySource(parse_repository(text), package)
    return build_graph(source, Settings(depth, exclude))


class RepositoryTests(FixtureCase):
    """Разбор файла тестового репозитория."""

    def test_parse(self):
        """Комментарии, пустые строки и пакеты без зависимостей."""
        repo = parse_repository("# c\nA: B C  # tail\n\nB:\n")
        self.assertEqual(repo, {"A": ["B", "C"], "B": []})

    def test_errors(self):
        """Строчные буквы, нет двоеточия, повтор пакета, нет корня."""
        for text in ("A: b", "A B", "A: B\nA: C", "a: B"):
            with self.assertRaises(RepositoryError, msg=text):
                parse_repository(text)
        with self.assertRaises(RepositoryError):
            TestRepositorySource({"A": []}, "Z")


class BfsTests(unittest.TestCase):
    """Обход в ширину."""

    def test_levels(self):
        """Узлы распределены по уровням BFS."""
        graph = graph_of("A: B C\nB: D\nC: E\n")
        self.assertEqual(graph.levels(), [["A"], ["B", "C"], ["D", "E"]])

    def test_diamond_has_single_node(self):
        """Общая зависимость появляется в графе один раз."""
        graph = graph_of("A: B C\nB: D\nC: D\n")
        self.assertEqual(list(graph.depth).count("D"), 1)
        self.assertIn(("C", "D"), graph.edge_list())

    def test_max_depth(self):
        """Узлы глубже max_depth не исследуются."""
        graph = graph_of("A: B\nB: C\nC: D\nD: E\n", depth=2)
        self.assertEqual(list(graph.depth), ["A", "B", "C"])
        self.assertEqual(graph.edges["C"], [])

    def test_filter(self):
        """Пакеты с подстрокой в имени не попадают в граф."""
        graph = graph_of("APP: LOG CORE\nCORE: LOGX UTIL\n", "APP",
                         exclude="LOG")
        self.assertNotIn("LOG", graph.depth)
        self.assertNotIn("LOGX", graph.depth)
        self.assertEqual(graph.excluded, {"LOG", "LOGX"})

    def test_cycles(self):
        """Циклы не зацикливают обход и находятся."""
        graph = graph_of(CYCLE)
        self.assertEqual(len(graph.depth), 6)
        cycles = find_cycles(graph)
        self.assertIn(["A", "C", "E", "A"], cycles)
        self.assertIn(["F", "F"], cycles)


class CargoGraphTests(unittest.TestCase):
    """Граф по индексу Cargo."""

    def test_transitive(self):
        """Транзитивные зависимости с выбранными версиями."""
        source = CargoSource(make_index(), "app", "1.0.0")
        graph = build_graph(source, Settings(5))
        labels = {source.label(node) for node in graph.depth}
        self.assertEqual(labels, {"app v1.0.0", "lib v1.1.0",
                                  "util v0.2.7", "log v0.4.9",
                                  "cfg v1.0.0"})
        self.assertTrue(find_cycles(graph))

    def test_dev_and_optional_ignored(self):
        """dev- и optional-зависимости не входят в граф."""
        source = CargoSource(make_index(), "app", "2.0.0")
        graph = build_graph(source, Settings(1))
        names = {node[0] for node in graph.depth}
        self.assertEqual(names, {"app", "lib", "log", "builder"})


if __name__ == "__main__":
    unittest.main()
