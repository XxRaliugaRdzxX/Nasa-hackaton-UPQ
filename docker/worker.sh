#!/usr/bin/env bash
# Worker: prepara los datos una vez y luego actualiza de forma incremental.
# Solo descarga lo que falta (las funciones del pipeline son idempotentes).
set -uo pipefail
INTERVAL_HOURS="${MECE_UPDATE_HOURS:-6}"

run() { echo "[$(date -u +%FT%TZ)] mece $*"; mece -v "$@" || echo "[$(date -u +%FT%TZ)] FALLÓ: mece $*"; }

run pipeline bootstrap
while true; do
  sleep "$((INTERVAL_HOURS * 3600))"
  run pipeline globe
  run pipeline fetch --dataset sst
  run pipeline fetch --dataset chl
  run pipeline precompute
done
