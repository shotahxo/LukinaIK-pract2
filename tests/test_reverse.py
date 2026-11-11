"""Тесты обратных зависимостей (этап 4)."""

import io
import unittest

from depviz.graph import Settings
from depviz.reverse import build_reverse_graph, print_reverse, reverse_edges
from depviz.test_repo import parse_repository

REPO = parse_repository("A: B C\nB: D\nC: D E\nE: A\nAPP: LOGGER D\n")


def reverse_of(package, depth=10, exclude=""):
    """Граф обратных зависимостей пакета."""
    _source, graph = build_reverse_graph(REPO, package,
                                         Settings(depth, exclude))
    return graph


class ReverseTests(unittest.TestCase):
    """Поиск пакетов, зависящих от заданного."""

    def test_reverse_edges(self):
        """Переворот рёбер."""
        reversed_graph = reverse_edges({"A": ["B"], "B": []})
        self.assertEqual(reversed_graph, {"A": [], "B": ["A"]})

    def test_levels(self):
        """Прямые и транзитивные потребители по уровням."""
        graph = reverse_of("D")
        self.assertEqual(graph.levels(),
                         [["D"], ["B", "C", "APP"], ["A"], ["E"]])

    def test_cycle(self):
        """Цикл A -> C -> E -> A не зацикливает обход."""
        graph = reverse_of("A")
        self.assertEqual(set(graph.depth), {"A", "E", "C"})

    def test_depth_and_filter(self):
        """Глубина и фильтр работают так же, как для прямых."""
        self.assertEqual(set(reverse_of("D", depth=1).depth),
                         {"D", "B", "C", "APP"})
        self.assertNotIn("APP", reverse_of("D", exclude="AP").depth)

    def test_no_dependents(self):
        """У корневого пакета нет потребителей."""
        out = io.StringIO()
        print_reverse(reverse_of("APP"), out)
        self.assertIn("нет", out.getvalue())


if __name__ == "__main__":
    unittest.main()
