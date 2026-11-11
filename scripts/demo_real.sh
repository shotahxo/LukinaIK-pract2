#!/bin/sh
# Визуализация трёх реальных пакетов crates.io (нужен интернет).
# Без интернета: make serve в другом окне и ./scripts/demo_real.sh mini
cd "$(dirname "$0")/.." || exit 1
mkdir -p output
if [ "$1" = "mini" ]; then
    names="mini_app mini_json mini_cli"
else
    names="real_log real_serde_json real_rand"
fi
for name in $names; do
    printf '\n>>> %s\n' "examples/configs/$name.yaml"
    ./run.sh -c "examples/configs/$name.yaml"
    printf '<<< код завершения: %s\n' "$?"
done
