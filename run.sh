#!/bin/sh
# Запуск depviz: ./run.sh [-c config.yaml]
cd "$(dirname "$0")" || exit 1
PYTHONPATH=src exec python3 -m depviz "$@"
