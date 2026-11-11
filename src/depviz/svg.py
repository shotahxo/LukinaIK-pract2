"""Изображение графа зависимостей в формате SVG.

Раскладка послойная: уровень узла — расстояние от корня в BFS. Внутри
уровня узлы упорядочены по среднему положению их «родителей», чтобы
уменьшить пересечения рёбер. Обратные рёбра (циклы) рисуются дугами.
"""

import os
from xml.sax.saxutils import escape

CHAR_WIDTH = 7.5
BOX_PADDING = 24
BOX_HEIGHT = 34
LAYER_GAP = 90
NODE_GAP = 28
MARGIN = 30
FONT = "Menlo, Consolas, 'DejaVu Sans Mono', monospace"
ROOT_FILL = "#ffe9a8"
NODE_FILL = "#e8f1ff"
STROKE = "#3a5f9f"
EDGE = "#555555"
BACK_EDGE = "#c0392b"
CURVE = 60
LEVEL_SAME = 0

ARROW_DEFS = (
    '<defs><marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" '
    'markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
    '<path d="M 0 0 L 10 5 L 0 10 z" fill="#555555"/></marker></defs>'
)


def box_width(text):
    """Ширина прямоугольника под подпись."""
    return len(text) * CHAR_WIDTH + BOX_PADDING


def order_levels(graph):
    """Упорядочить узлы внутри уровней по положению родителей."""
    parents = {}
    for parent, child in graph.edge_list():
        parents.setdefault(child, []).append(parent)
    ordered = []
    position = {}
    for level in graph.levels():
        def weight(node):
            """Среднее место родителей из уже размещённых уровней."""
            known = [position[p] for p in parents.get(node, [])
                     if p in position]
            return sum(known) / len(known) if known else 0
        level = sorted(level, key=weight)
        position.update({node: index for index, node in enumerate(level)})
        ordered.append(level)
    return ordered


def layout(graph, label):
    """Координаты центров узлов и размер рисунка."""
    levels = order_levels(graph)
    widths = [sum(box_width(label(n)) for n in level)
              + NODE_GAP * (len(level) - 1) for level in levels]
    canvas = max(widths) + 2 * MARGIN
    centers = {}
    for depth, (level, width) in enumerate(zip(levels, widths)):
        x = (canvas - width) / 2
        y = MARGIN + depth * LAYER_GAP + BOX_HEIGHT / 2
        for node in level:
            size = box_width(label(node))
            centers[node] = (x + size / 2, y)
            x += size + NODE_GAP
    height = 2 * MARGIN + (len(levels) - 1) * LAYER_GAP + BOX_HEIGHT + CURVE
    return centers, canvas + 2 * CURVE, height


def _line(x1, y1, x2, y2):
    """Прямое ребро со стрелкой."""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" '
            f'y2="{y2:.1f}" stroke="{EDGE}" stroke-width="1.4" '
            f'marker-end="url(#arrow)"/>')


def _curve(path, color, dashed):
    """Кривое ребро со стрелкой."""
    dash = ' stroke-dasharray="5,4"' if dashed else ""
    return (f'<path d="{path}" fill="none" stroke="{color}" '
            f'stroke-width="1.4"{dash} marker-end="url(#arrow)"/>')


def down_edge(start, end):
    """Ребро на следующий уровень: от низа родителя к верху потомка."""
    (x1, y1), (x2, y2) = start, end
    half = BOX_HEIGHT / 2
    return _line(x1, y1 + half, x2, y2 - half)


def side_edge(start, end):
    """Ребро внутри уровня: дуга под прямоугольниками."""
    (x1, y1), (x2, y2) = start, end
    half = BOX_HEIGHT / 2
    middle = (x1 + x2) / 2
    path = (f"M {x1:.1f} {y1 + half:.1f} Q {middle:.1f} "
            f"{y1 + half + CURVE:.1f} {x2:.1f} {y2 + half:.1f}")
    return _curve(path, EDGE, False)


def back_edge(start, end, widths):
    """Ребро к узлу выше (цикл): дуга справа от узлов."""
    (x1, y1), (x2, y2) = start, end
    right1 = x1 + widths[0] / 2
    right2 = x2 + widths[1] / 2
    bend = max(right1, right2) + CURVE
    path = (f"M {right1:.1f} {y1:.1f} C {bend:.1f} {y1:.1f}, "
            f"{bend:.1f} {y2:.1f}, {right2:.1f} {y2:.1f}")
    return _curve(path, BACK_EDGE, True)


def self_loop(center, width):
    """Петля: пакет зависит сам от себя."""
    x, y = center
    right = x + width / 2
    shift = BOX_HEIGHT / 4
    path = (f"M {right:.1f} {y - shift:.1f} C {right + CURVE:.1f} "
            f"{y - BOX_HEIGHT:.1f}, {right + CURVE:.1f} {y + BOX_HEIGHT:.1f}"
            f", {right:.1f} {y + shift:.1f}")
    return _curve(path, BACK_EDGE, True)


def edge_markup(graph, centers, edge, label):
    """Выбрать вид ребра: вниз, внутри уровня, назад (цикл) или петля."""
    parent, child = edge
    start, end = centers[parent], centers[child]
    if parent == child:
        return self_loop(start, box_width(label(parent)))
    step = graph.depth[child] - graph.depth[parent]
    if step > LEVEL_SAME:
        return down_edge(start, end)
    if step == LEVEL_SAME:
        return side_edge(start, end)
    widths = (box_width(label(parent)), box_width(label(child)))
    return back_edge(start, end, widths)


def node_svg(center, text, is_root):
    """Прямоугольник с подписью."""
    x, y = center
    width = box_width(text)
    fill = ROOT_FILL if is_root else NODE_FILL
    return (f'<rect x="{x - width / 2:.1f}" y="{y - BOX_HEIGHT / 2:.1f}" '
            f'width="{width:.1f}" height="{BOX_HEIGHT}" rx="7" '
            f'fill="{fill}" stroke="{STROKE}" stroke-width="1.4"/>'
            f'<text x="{x:.1f}" y="{y + 4.5:.1f}" text-anchor="middle" '
            f'font-family="{FONT}" font-size="13">{escape(text)}</text>')


def to_svg(graph, label):
    """Полный текст SVG-документа."""
    centers, width, height = layout(graph, label)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
             f'height="{height:.0f}" viewBox="0 0 {width:.0f} '
             f'{height:.0f}">', ARROW_DEFS,
             f'<rect width="100%" height="100%" fill="white"/>']
    for parent, child in graph.edge_list():
        parts.append(edge_markup(graph, centers, (parent, child), label))
    for node, center in centers.items():
        parts.append(node_svg(center, label(node), node == graph.root))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def save_svg(graph, label, path):
    """Записать SVG в файл, создав каталог при необходимости."""
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(to_svg(graph, label))
