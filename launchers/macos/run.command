#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

if command -v python3 >/dev/null 2>&1; then
  exec python3 scripts/bootstrap.py run "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python scripts/bootstrap.py run "$@"
fi

echo "No se encontró un intérprete de Python para ejecutar la automatización." >&2
exit 1
