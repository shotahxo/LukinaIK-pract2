"""Текстовое описание графа на языке диаграмм Mermaid."""

HEADER = "graph TD"
INDENT = "    "


def node_ids(graph):
    """Короткие идентификаторы узлов: n0, n1, ..."""
    return {node: f"n{index}" for index, node in enumerate(graph.depth)}


def escape_label(text):
    """Экранировать кавычки в подписи узла."""
    return text.replace('"', "#quot;")


def to_mermaid(graph, label):
    """Текст диаграммы Mermaid для графа зависимостей."""
    ids = node_ids(graph)
    lines = [HEADER]
    for node, node_id in ids.items():
        lines.append(f'{INDENT}{node_id}["{escape_label(label(node))}"]')
    for parent, child in graph.edge_list():
        lines.append(f"{INDENT}{ids[parent]} --> {ids[child]}")
    lines.append(f"{INDENT}style {ids[graph.root]} fill:#ffe9a8,"
                 f"stroke:#b8860b")
    return "\n".join(lines)
