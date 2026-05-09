#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if command -v python3 >/dev/null 2>&1; then
  exec python3 scripts/bootstrap.py setup "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python scripts/bootstrap.py setup "$@"
fi

if command -v py >/dev/null 2>&1; then
  exec py scripts/bootstrap.py setup "$@"
fi

echo "No se encontró un intérprete de Python para ejecutar la automatización." >&2
exit 1
