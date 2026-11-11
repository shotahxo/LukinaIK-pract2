"""Обратные зависимости: пакеты, которые зависят от заданного."""

from .graph import build_graph


def reverse_edges(graph):
    """Перевернуть словарь «пакет → зависимости»."""
    reversed_graph = {}
    for package, deps in graph.items():
        reversed_graph.setdefault(package, [])
        for dep in deps:
            dependents = reversed_graph.setdefault(dep, [])
            if package not in dependents:
                dependents.append(package)
    return reversed_graph


class ReverseSource:
    """Источник, в котором «зависимости» — это пакеты-потребители."""

    def __init__(self, graph, package):
        """Построить обратный граф и запомнить исходный пакет."""
        self.graph = reverse_edges(graph)
        self.root = package

    def children(self, node):
        """Пакеты, которые напрямую зависят от ``node``."""
        return list(self.graph.get(node, []))

    def name(self, node):
        """Имя пакета."""
        return node

    def label(self, node):
        """Подпись узла."""
        return node


def build_reverse_graph(graph, package, settings):
    """Найти обратные зависимости тем же рекурсивным BFS, что и прямые."""
    source = ReverseSource(graph, package)
    return source, build_graph(source, settings)


def print_reverse(reverse_graph, out):
    """Вывести обратные зависимости по уровням и цепочки."""
    root = reverse_graph.root
    levels = reverse_graph.levels()[1:]
    print(f"Обратные зависимости {root} (пакеты, которые зависят "
          f"от {root}):", file=out)
    if not levels:
        print("  нет", file=out)
    for depth, nodes in enumerate(levels, start=1):
        print(f"  уровень {depth}: {', '.join(nodes)}", file=out)
    edges = reverse_graph.edge_list()
    if edges:
        print("Связи (кто от кого зависит):", file=out)
    for used, user in edges:
        print(f"  {user} -> {used}", file=out)
