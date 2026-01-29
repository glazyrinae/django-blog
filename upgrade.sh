#!/bin/bash
set -euo pipefail

ACTION=${1:-start}
ENV=${2:-dev}

load_env() {
    local env_file=$1
    if [[ -f "$env_file" ]]; then
        set -a
        source "$env_file"
        set +a
    else
        echo "Файл $env_file не найден" >&2
        exit 1
    fi
}

compose_cmd=(docker compose)
if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
    echo "docker compose (v2) не найден. Установи Docker Compose plugin." >&2
    exit 1
fi

compose_dev_files=(-f docker-compose.yml)
if [[ -f docker-compose.local.yml ]]; then
    compose_dev_files+=(-f docker-compose.local.yml)
fi

case "${ACTION} ${ENV}" in
  "start dev")
    load_env ".env.dev"
    "${compose_cmd[@]}" --env-file .env.dev "${compose_dev_files[@]}" up -d --build
    ;;
  "stop dev")
    load_env ".env.dev"
    "${compose_cmd[@]}" --env-file .env.dev "${compose_dev_files[@]}" down
    ;;
  "start prod")
    load_env ".env.prod"
    "${compose_cmd[@]}" --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.local.yml up -d --build
    ;;
  "stop prod")
    load_env ".env.prod"
    "${compose_cmd[@]}" --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.local.yml down
    ;;
  *)
    echo "Использование: ./upgrade.sh [start|stop] [dev|prod]"
    exit 1
    ;;
esac
