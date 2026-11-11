#!/bin/sh
# Демонстрация построения графа на тестовых репозиториях (этап 3).
cd "$(dirname "$0")/.." || exit 1
for name in simple diamond cycle depth_3 depth_10 filter_log filter_test \
            start_inside invalid_repo unknown_package; do
    printf '\n>>> %s\n' "examples/configs/$name.yaml"
    ./run.sh -c "examples/configs/$name.yaml" "$@"
    printf '<<< код завершения: %s\n' "$?"
done
