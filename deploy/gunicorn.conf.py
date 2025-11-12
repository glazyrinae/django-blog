bind = "0.0.0.0:8000"
workers = 1
worker_class = "sync"
timeout = 120
preload_app = True
max_requests = 1000
max_requests_jitter = 100

# Логирование
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Дополнительные настройки
reload = False
daemon = False