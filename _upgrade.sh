#!/bin/bash
# project.sh - Управление Django проектом в разных окружениях

set -e  # Выход при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для цветного вывода
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Переменные
PROJECT_DIR=$(pwd)
COMPOSE_DEV="docker-compose.yml"
COMPOSE_PROD="docker-compose.prod.yml"
ENV_DEV=".env.dev"
ENV_PROD=".env.prod"

# Проверка существования файлов
check_files() {
    if [[ ! -f "$COMPOSE_DEV" ]]; then
        print_error "Файл $COMPOSE_DEV не найден!"
        exit 1
    fi
    
    if [[ "$1" == "prod" && ! -f "$COMPOSE_PROD" ]]; then
        print_error "Файл $COMPOSE_PROD не найден!"
        exit 1
    fi
}

# Функция помощи
show_help() {
    echo "Использование: ./project.sh [команда] [окружение]"
    echo ""
    echo "Команды:"
    echo "  up          - Запуск проекта"
    echo "  down        - Остановка проекта" 
    echo "  restart     - Перезапуск проекта"
    echo "  logs        - Просмотр логов"
    echo "  status      - Статус контейнеров"
    echo "  build       - Сборка образов"
    echo "  migrate     - Применение миграций"
    echo "  shell       - Вход в контейнер web"
    echo "  manage      - Выполнить manage.py команду"
    echo "  backup      - Бэкап базы данных"
    echo "  restore     - Восстановление базы данных"
    echo ""
    echo "Окружения:"
    echo "  dev         - Разработка (по умолчанию)"
    echo "  prod        - Продакшен"
    echo ""
    echo "Примеры:"
    echo "  ./project.sh up dev"
    echo "  ./project.sh up prod"
    echo "  ./project.sh migrate prod"
    echo "  ./project.sh logs dev"
}

# Получение compose команды в зависимости от окружения
get_compose_cmd() {
    local env=$1
    if [[ "$env" == "prod" ]]; then
        echo "docker-compose -f $COMPOSE_DEV -f $COMPOSE_PROD"
    else
        echo "docker-compose -f $COMPOSE_DEV"
    fi
}

# Запуск проекта
up() {
    local env=${1:-dev}
    check_files "$env"
    
    print_info "Запуск проекта в режиме: $env"
    
    # Проверка .env файла
    local env_file=".env.$env"
    if [[ ! -f "$env_file" ]]; then
        print_warning "Файл $env_file не найден, создаем из примера..."
        if [[ -f ".env.example" ]]; then
            cp .env.example "$env_file"
            print_success "Создан файл $env_file"
        else
            print_error "Нет .env.example для создания $env_file"
            exit 1
        fi
    fi
    
    local cmd=$(get_compose_cmd "$env")
    $cmd up -d
    print_success "Проект запущен в режиме: $env"
    
    # Дополнительные действия после запуска
    if [[ "$env" == "dev" ]]; then
        sleep 5
        migrate "$env"
    fi
}

# Остановка проекта
down() {
    local env=${1:-dev}
    check_files "$env"
    
    print_info "Остановка проекта в режиме: $env"
    
    local cmd=$(get_compose_cmd "$env")
    $cmd down
    print_success "Проект остановлен в режиме: $env"
}

# Перезапуск проекта
restart() {
    local env=${1:-dev}
    print_info "Перезапуск проекта в режиме: $env"
    
    down "$env"
    up "$env"
}

# Просмотр логов
logs() {
    local env=${1:-dev}
    check_files "$env"
    
    local cmd=$(get_compose_cmd "$env")
    $cmd logs -f --tail=100
}

# Статус контейнеров
status() {
    local env=${1:-dev}
    check_files "$env"
    
    local cmd=$(get_compose_cmd "$env")
    echo "Статус контейнеров ($env):"
    $cmd ps
}

# Сборка образов
build() {
    local env=${1:-dev}
    check_files "$env"
    
    print_info "Сборка образов в режиме: $env"
    
    local cmd=$(get_compose_cmd "$env")
    $cmd build --no-cache
    print_success "Образы собраны в режиме: $env"
}

# Применение миграций
migrate() {
    local env=${1:-dev}
    check_files "$env"
    
    print_info "Применение миграций в режиме: $env"
    
    local cmd=$(get_compose_cmd "$env")
    $cmd exec web python manage.py migrate
    print_success "Миграции применены в режиме: $env"
}

# Создание миграций
makemigrations() {
    local env=${1:-dev}
    local message=${2:-"auto"}
    
    check_files "$env"
    print_info "Создание миграций в режиме: $env"
    
    local cmd=$(get_compose_cmd "$env")
    $cmd exec web python manage.py makemigrations --name "$message"
    print_success "Миграции созданы в режиме: $env"
}

# Вход в контейнер
shell() {
    local env=${1:-dev}
    check_files "$env"
    
    local cmd=$(get_compose_cmd "$env")
    $cmd exec web bash
}

# Выполнение manage.py команды
manage() {
    local env=${1:-dev}
    shift
    local command=$@
    
    if [[ -z "$command" ]]; then
        print_error "Укажите manage.py команду"
        exit 1
    fi
    
    check_files "$env"
    print_info "Выполнение: python manage.py $command (режим: $env)"
    
    local cmd=$(get_compose_cmd "$env")
    $cmd exec web python manage.py $command
}

# Бэкап базы данных
backup() {
    local env=${1:-dev}
    check_files "$env"
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="backup_${env}_${timestamp}.sql"
    
    print_info "Создание бэкапа БД в режиме: $env"
    
    local cmd=$(get_compose_cmd "$env")
    $cmd exec db pg_dump -U postgres -d app_db > "backups/$backup_file"
    
    # Создаем папку backups если её нет
    mkdir -p backups
    
    print_success "Бэкап создан: backups/$backup_file"
}

# Восстановление базы данных
restore() {
    local env=${1:-dev}
    local backup_file=$2
    
    if [[ -z "$backup_file" ]]; then
        print_error "Укажите файл для восстановления"
        echo "Доступные бэкапы:"
        ls -la backups/ | grep .sql
        exit 1
    fi
    
    check_files "$env"
    print_info "Восстановление БД из $backup_file в режиме: $env"
    
    local cmd=$(get_compose_cmd "$env")
    $cmd exec -T db psql -U postgres -d app_db < "backups/$backup_file"
    print_success "БД восстановлена из: $backup_file"
}

# Очистка (volumes, images)
clean() {
    local env=${1:-dev}
    
    print_warning "Очистка системы Docker (режим: $env)"
    read -p "Вы уверены? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        local cmd=$(get_compose_cmd "$env")
        $cmd down -v
        docker system prune -f
        print_success "Очистка завершена"
    else
        print_info "Очистка отменена"
    fi
}

# Основная логика
main() {
    local command=$1
    local environment=$2
    
    # Проверка аргументов
    if [[ -z "$command" ]]; then
        show_help
        exit 1
    fi
    
    # Если окружение не указано, используем dev
    if [[ -z "$environment" ]]; then
        environment="dev"
    fi
    
    # Проверка корректности окружения
    if [[ "$environment" != "dev" && "$environment" != "prod" ]]; then
        print_error "Неверное окружение: $environment"
        show_help
        exit 1
    fi
    
    case $command in
        "up")
            up "$environment"
            ;;
        "down")
            down "$environment"
            ;;
        "restart")
            restart "$environment"
            ;;
        "logs")
            logs "$environment"
            ;;
        "status")
            status "$environment"
            ;;
        "build")
            build "$environment"
            ;;
        "migrate")
            migrate "$environment"
            ;;
        "makemigrations")
            makemigrations "$environment" "$3"
            ;;
        "shell")
            shell "$environment"
            ;;
        "manage")
            manage "$environment" "${@:3}"
            ;;
        "backup")
            backup "$environment"
            ;;
        "restore")
            restore "$environment" "$3"
            ;;
        "clean")
            clean "$environment"
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Неизвестная команда: $command"
            show_help
            exit 1
            ;;
    esac
}

# Запуск основной функции
main "$@"