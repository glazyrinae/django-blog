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

compose_dev_files=(-f docker-compose.yml)
if [[ -f docker-compose.local.yml ]]; then
    compose_dev_files+=(-f docker-compose.local.yml)
fi

case "${ACTION} ${ENV}" in
  "start dev")
    load_env ".env.dev"
    docker-compose --env-file .env.dev "${compose_dev_files[@]}" up -d
    ;;
  "stop dev")
    load_env ".env.dev"
    docker-compose --env-file .env.dev "${compose_dev_files[@]}" down
    ;;
  "start prod")
    load_env ".env.prod"
    docker-compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d
    ;;
  "stop prod")
    load_env ".env.prod"
    docker-compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml down
    ;;
  *)
    echo "Использование: ./upgrade.sh [start|stop] [dev|prod]"
    exit 1
    ;;
esac
