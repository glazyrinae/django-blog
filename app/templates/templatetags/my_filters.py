import markdown
from django import template
from django.utils.safestring import mark_safe
from django.utils.html import strip_tags

register = template.Library()


@register.filter
def strip_markdown(value):
    """Удаляет Markdown разметку из текста"""
    if not value:
        return ""
    # Конвертируем Markdown в HTML
    html_content = markdown.markdown(value)
    # Удаляем HTML теги
    clean_text = strip_tags(html_content)
    return clean_text


@register.filter(name="markdown")
def markdown_filter(value):
    if not value:
        return ""

    extensions = [
        "markdown.extensions.extra",
        "markdown.extensions.codehilite",
        "markdown.extensions.toc",
        "markdown.extensions.nl2br",
        "markdown.extensions.sane_lists",
        "markdown.extensions.fenced_code",
    ]

    # Дополнительные настройки
    extension_configs = {
        "markdown.extensions.codehilite": {
            "css_class": "highlight",
        },
        "markdown.extensions.toc": {
            "title": "Содержание",
        },
    }

    html = markdown.markdown(
        value, extensions=extensions, extension_configs=extension_configs
    )
    return mark_safe(html)


@register.filter(name="plural")
def choose_plural(amount: int, variants: list = ["пост", "поста", "постов"]) -> str:
    if isinstance(variants, list) and len(variants) == 3:
        if amount % 10 == 1 and amount % 100 != 11:
            variant = 0
        elif (
            amount % 10 >= 2
            and amount % 10 <= 4
            and (amount % 100 < 10 or amount % 100 >= 20)
        ):
            variant = 1
        else:
            variant = 2
        return f"{amount} {variants[variant]}"
    return ""
