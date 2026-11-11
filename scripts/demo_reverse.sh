#!/bin/sh
# Демонстрация обратных зависимостей на тестовых репозиториях (этап 4).
cd "$(dirname "$0")/.." || exit 1
for name in reverse_simple reverse_diamond reverse_cycle reverse_depth \
            reverse_filter reverse_root; do
    printf '\n>>> %s\n' "examples/configs/$name.yaml"
    ./run.sh -c "examples/configs/$name.yaml" "$@"
    printf '<<< код завершения: %s\n' "$?"
done
