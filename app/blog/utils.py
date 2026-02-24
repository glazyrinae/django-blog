import re

from django.core.cache import cache
from django.utils.html import escape


def validate_search_query(query: str) -> str:
    """
    Валидация поискового запроса с удалением недопустимых символов.
    """
    if not query:
        return ""

    # Удаляем опасные паттерны
    patterns_to_remove = [
        r"<script.*?>.*?</script>",  # HTML script теги
        r"<iframe.*?>.*?</iframe>",  # HTML iframe теги
        r"javascript:",  # JS протокол
        r"vbscript:",  # VBScript протокол
        r"onload\s*=|onerror\s*=|onclick\s*=",  # HTML события
        r"--|\/\*|\*\/",  # SQL комментарии
        r";",  # Разделитель SQL
        r"union\s+select",  # UNION SELECT injection
        r"insert\s+into",  # INSERT injection
        r"drop\s+table",  # DROP TABLE injection
        r"update\s+.+\s+set",  # UPDATE injection
        r"delete\s+from",  # DELETE injection
        r"or\s+1\s*=\s*1",  # OR 1=1 injection
        r"and\s+1\s*=\s*1",  # AND 1=1 injection
    ]

    clean_query = query
    for pattern in patterns_to_remove:
        clean_query = re.sub(pattern, "", clean_query, flags=re.IGNORECASE)

    # Удаляем отдельные опасные символы
    clean_query = re.sub(r'[<>"\'\\]', "", clean_query)

    # Удаляем множественные пробелы
    clean_query = re.sub(r"\s+", " ", clean_query)

    # Очистка и ограничение длины
    clean_query = escape(clean_query.strip())[:100]

    return clean_query


def check_rate_limit(request, action="search", limit=10, window=60):
    """
    Простая защита от частых запросов.
    """
    ip = _get_client_ip(request)
    if not ip:
        return True

    cache_key = f"rate_limit_{action}_{ip}"
    count = cache.get(cache_key, 0)

    if count >= limit:
        return False

    cache.set(cache_key, count + 1, window)
    return True


def _get_client_ip(request):
    """Получение IP клиента."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")
