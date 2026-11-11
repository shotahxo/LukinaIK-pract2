#!/bin/sh
# Визуализация трёх пакетов тестового репозитория (этап 5).
# Изображения сохраняются в каталог output/.
cd "$(dirname "$0")/.." || exit 1
mkdir -p output
for name in visual_simple visual_cycle visual_app; do
    printf '\n>>> %s\n' "examples/configs/$name.yaml"
    ./run.sh -c "examples/configs/$name.yaml" "$@"
    printf '<<< код завершения: %s\n' "$?"
done
