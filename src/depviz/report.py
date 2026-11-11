"""Текстовый отчёт о графе зависимостей."""

from .graph import find_cycles


def print_graph(graph, source, settings, out):
    """Вывести уровни, рёбра, циклы и исключённые пакеты."""
    label = source.label
    print(f"Граф зависимостей {label(graph.root)} "
          f"(max_depth={settings.max_depth}, "
          f"filter_substring={settings.exclude!r})", file=out)
    for depth, nodes in enumerate(graph.levels()):
        names = ", ".join(label(node) for node in nodes)
        print(f"  уровень {depth}: {names}", file=out)
    edges = graph.edge_list()
    print(f"Рёбра ({len(edges)}):", file=out)
    for parent, child in edges:
        print(f"  {label(parent)} -> {label(child)}", file=out)
    for cycle in find_cycles(graph):
        path = " -> ".join(label(node) for node in cycle)
        print(f"Циклическая зависимость: {path}", file=out)
    if graph.excluded:
        names = ", ".join(sorted(graph.excluded))
        print(f"Исключены фильтром: {names}", file=out)
