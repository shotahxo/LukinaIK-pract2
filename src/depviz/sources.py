"""Источник зависимостей на основе индекса Cargo."""


class CargoSource:
    """Узлы графа — пары (имя пакета, версия)."""

    def __init__(self, index, package, version):
        """Проверить, что версия существует, и запомнить корень."""
        index.entry(package, version)
        self.index = index
        self.root = (package, version)

    def children(self, node):
        """Прямые зависимости с выбранными версиями (normal и build)."""
        name, version = node
        result = []
        for dep in self.index.dependencies(name, version):
            if dep.is_required():
                resolved = self.index.resolve(dep.name, dep.requirement)
                result.append((dep.name, resolved))
        return sorted(set(result))

    def name(self, node):
        """Имя пакета без версии."""
        return node[0]

    def label(self, node):
        """Подпись узла, как в ``cargo tree``: ``имя vВЕРСИЯ``."""
        return f"{node[0]} v{node[1]}"
