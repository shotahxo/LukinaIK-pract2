"""Вывод графа зависимостей в виде ASCII-дерева (как ``cargo tree``)."""

BRANCH = "├── "
LAST = "└── "
PIPE = "│   "
SPACE = "    "
SEEN_MARK = " (*)"


def ascii_tree(graph, label):
    """Строки дерева; повторно встреченные пакеты помечаются ``(*)``."""
    lines = [label(graph.root)]
    seen = {graph.root}
    _walk(graph, graph.root, "", seen, (lines, label))
    return lines


def _walk(graph, node, prefix, seen, sink):
    """Рекурсивно добавить потомков узла в строки дерева."""
    lines, label = sink
    children = graph.edges.get(node, [])
    for index, child in enumerate(children):
        last = index == len(children) - 1
        mark = SEEN_MARK if child in seen else ""
        lines.append(prefix + (LAST if last else BRANCH) + label(child)
                     + mark)
        if mark:
            continue
        seen.add(child)
        _walk(graph, child, prefix + (SPACE if last else PIPE), seen, sink)
