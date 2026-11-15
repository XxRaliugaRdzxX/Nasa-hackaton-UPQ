#!/usr/bin/env bash
# Despliegue reproducible en el servidor. Uso: ./docker/deploy.sh [worker]
set -euo pipefail
cd "$(dirname "$0")"
DC=(docker compose --env-file ../.env -f docker-compose.yml)
if [[ "${1:-}" == "worker" ]]; then
  "${DC[@]}" --profile worker up -d --build
else
  "${DC[@]}" up -d --build app tunnel
fi
"${DC[@]}" ps
