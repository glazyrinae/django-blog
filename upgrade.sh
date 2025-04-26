#!/usr/bin/env /bin/bash
# settings
set -e

export $(cat .env | grep RUN_MODE)

(   # проверяем есть ли блокировка на файл
    flock -n 9 || { echo "upgrade.sh уже запущен"; exit 1; }

    # update git repo
    if [ $RUN_MODE != "dev" ]; then
        git -C ./smart_bps pull
    fi
    git pull

    dc="docker compose -f docker-compose.yml -f docker-compose.$RUN_MODE.yml -f docker-compose.local.yml --env-file .env"

    # rebuild images, containers (if image change only)
    ${dc} up --build --remove-orphans -d
    # ${dc} stop queue

    ${dc} exec back /app/manage.py syncdb
    ${dc} kill -s HUP back

    # ${dc} start queue
    ${dc} exec front npm run build

) 9>./upgrade_sh.lock
