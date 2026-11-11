"""Построение графа зависимостей обходом в ширину (BFS) с рекурсией."""

from dataclasses import dataclass, field

ROOT_DEPTH = 0


@dataclass
class Graph:
    """Граф зависимостей: узлы с уровнями и рёбра «пакет → зависимость»."""

    root: object
    depth: dict = field(default_factory=dict)
    edges: dict = field(default_factory=dict)
    excluded: set = field(default_factory=set)

    def add_node(self, node, depth):
        """Добавить узел, если его ещё нет; вернуть True для нового."""
        if node in self.depth:
            return False
        self.depth[node] = depth
        self.edges[node] = []
        return True

    def add_edge(self, parent, child):
        """Добавить ребро без повторов."""
        if child not in self.edges[parent]:
            self.edges[parent].append(child)

    def levels(self):
        """Узлы, сгруппированные по уровню удалённости от корня."""
        result = {}
        for node, depth in self.depth.items():
            result.setdefault(depth, []).append(node)
        return [result[key] for key in sorted(result)]

    def edge_list(self):
        """Все рёбра графа в порядке обхода."""
        return [(a, b) for a, children in self.edges.items() for b in children]


@dataclass
class Settings:
    """Параметры обхода: глубина и подстрока для исключения пакетов."""

    max_depth: int
    exclude: str = ""

    def is_excluded(self, name):
        """Нужно ли пропустить пакет с этим именем."""
        return bool(self.exclude) and self.exclude in name


def _visit_level(source, graph, level, depth, settings):
    """Рекурсивный шаг BFS: обработать уровень и перейти к следующему."""
    if not level or depth >= settings.max_depth:
        return
    next_level = []
    for node in level:
        for child in source.children(node):
            if settings.is_excluded(source.name(child)):
                graph.excluded.add(source.name(child))
                continue
            if graph.add_node(child, depth + 1):
                next_level.append(child)
            graph.add_edge(node, child)
    _visit_level(source, graph, next_level, depth + 1, settings)


def build_graph(source, settings, start=None):
    """Построить граф зависимостей от ``start`` (по умолчанию — корень)."""
    root = source.root if start is None else start
    graph = Graph(root)
    graph.add_node(root, ROOT_DEPTH)
    _visit_level(source, graph, [root], ROOT_DEPTH, settings)
    return graph


def find_cycles(graph):
    """Найти циклы: список путей вида [A, B, ..., A]."""
    cycles = []
    state = {}

    def walk(node, path):
        """Обход в глубину с отметкой узлов на текущем пути."""
        state[node] = path
        for child in graph.edges.get(node, []):
            if child in path:
                cycles.append(path[path.index(child):] + [child])
            elif child not in state:
                walk(child, path + [child])

    walk(graph.root, [graph.root])
    return cycles
