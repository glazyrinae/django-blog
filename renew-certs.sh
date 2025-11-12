#!/bin/bash

cd .

LOG_FILE="./certbot-renewal.log"

# Запускаем обновление (renew проверяет истекшие сертификаты)
docker-compose run --rm certbot renew --webroot -w /var/www/certbot

# Если сертификаты обновились, перезагружаем nginx
if [ $? -eq 0 ]; then
    docker-compose exec nginx nginx -s reload
    echo "$(date): Certificates renewed" >> $LOG_FILE
else
    echo "$(date): No renewal needed" >> $LOG_FILE
fi