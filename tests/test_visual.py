"""Тесты визуализации: ASCII-дерево, Mermaid, SVG (этап 5)."""

import io
import os
import tempfile
import unittest
from xml.etree import ElementTree

from depviz.ascii_tree import ascii_tree
from depviz.cli import EXIT_OK, run
from depviz.graph import Settings, build_graph
from depviz.mermaid import to_mermaid
from depviz.svg import save_svg, to_svg
from depviz.test_repo import TestRepositorySource, parse_repository
from fixture_case import FixtureCase

REPO = "A: B C\nB: D\nC: D E\nE: A F\nF: F\n"


def sample_graph():
    """Граф с ромбом, циклом и петлёй."""
    source = TestRepositorySource(parse_repository(REPO), "A")
    return build_graph(source, Settings(10)), source.label


class AsciiTreeTests(unittest.TestCase):
    """ASCII-дерево."""

    def test_tree(self):
        """Ветви, повторы (*) и циклы."""
        graph, label = sample_graph()
        self.assertEqual(ascii_tree(graph, label), [
            "A",
            "├── B",
            "│   └── D",
            "└── C",
            "    ├── D (*)",
            "    └── E",
            "        ├── A (*)",
            "        └── F",
            "            └── F (*)",
        ])


class MermaidTests(unittest.TestCase):
    """Текст Mermaid."""

    def test_mermaid(self):
        """Заголовок, узлы с подписями и рёбра."""
        graph, label = sample_graph()
        text = to_mermaid(graph, label)
        lines = text.splitlines()
        self.assertEqual(lines[0], "graph TD")
        self.assertIn('    n0["A"]', lines)
        self.assertIn("    n4 --> n0", lines)
        self.assertEqual(text.count("-->"), len(graph.edge_list()))

    def test_quotes_escaped(self):
        """Кавычки в подписях экранируются."""
        graph, _label = sample_graph()
        text = to_mermaid(graph, lambda node: f'"{node}"')
        self.assertIn("#quot;A#quot;", text)


class SvgTests(FixtureCase):
    """Файл SVG."""

    def test_valid_xml(self):
        """SVG — корректный XML со всеми узлами и рёбрами."""
        graph, label = sample_graph()
        root = ElementTree.fromstring(to_svg(graph, label))
        texts = [node.text for node in root.iter()
                 if node.tag.endswith("text")]
        self.assertEqual(sorted(texts), list("ABCDEF"))
        shapes = [node for node in root.iter()
                  if node.tag.endswith(("line", "path"))]
        self.assertEqual(len(shapes) - 1, len(graph.edge_list()))

    def test_save_creates_folder(self):
        """Каталог для файла создаётся автоматически."""
        graph, label = sample_graph()
        folder = tempfile.mkdtemp()
        path = os.path.join(folder, "sub", "graph.svg")
        save_svg(graph, label, path)
        self.assertTrue(os.path.exists(path))

    def test_cli_visualization(self):
        """Полный запуск: дерево, Mermaid и файл SVG."""
        repo = self.make_file(REPO)
        image = os.path.join(tempfile.mkdtemp(), "out.svg")
        config = self.make_file(
            f"package: A\nrepository: {repo}\ntest_mode: true\n"
            f"ascii_tree: true\noutput_image: {image}\n", ".yaml")
        out = io.StringIO()
        self.assertEqual(run(["-c", config], out=out), EXIT_OK)
        text = out.getvalue()
        self.assertIn("└── C", text)
        self.assertIn("graph TD", text)
        self.assertIn("Циклическая зависимость: A -> C -> E -> A", text)
        self.assertTrue(os.path.exists(image))


if __name__ == "__main__":
    unittest.main()
