# search/templatetags/search_tags.py
from django import template
from django.contrib.contenttypes.models import ContentType
from ..models import SearchConfig

register = template.Library()


@register.inclusion_tag("search/search_panel.html", takes_context=True)
def render_search_panel(context, config_name=None, content_type=None):
    """Рендерит панель поиска"""

    request = context.get("request")
    base_context = context.flatten()

    # Ищем конфигурацию
    config = None
    if config_name:
        try:
            config = SearchConfig.objects.get(name=config_name, is_active=True)
        except SearchConfig.DoesNotExist:
            pass

    # Или по content_type
    if not config and content_type:
        try:
            if isinstance(content_type, str):
                app_label, model = content_type.split(".")
                ct = ContentType.objects.get(app_label=app_label, model=model)
            else:
                ct = content_type
            config = SearchConfig.objects.filter(
                content_type=ct, is_active=True
            ).first()
        except (ValueError, ContentType.DoesNotExist):
            pass

    if not config:
        return {"config": None}

    # Получаем поля
    fields = config.fields.filter(is_visible=True).order_by("order")

    # Генерируем ID для формы
    form_id = f"search-form-{config.id}"

    base_context.update(
        {
            "config": config,
            "fields": fields,
            "filters": context.get("filters", []),
            "form_id": form_id,
            "request": request,
        }
    )
    return base_context
