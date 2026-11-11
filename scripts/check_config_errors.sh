#!/bin/sh
# Демонстрация обработки ошибок всех параметров конфигурации (этап 1).
cd "$(dirname "$0")/.." || exit 1
show() {
    printf '\n>>> %s\n' "$1"
    ./run.sh -c "$1"
    printf '<<< код завершения: %s\n' "$?"
}
show config.yaml
show examples/errors/no_such_config.yaml
for file in examples/errors/*.yaml; do
    show "$file"
done
