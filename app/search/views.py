# search/views.py
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from datetime import datetime
from .models import SearchConfig, SearchField


@require_POST
def api_search(request):
    """API endpoint для поиска"""

    try:
        data = json.loads(request.body)
        config_id = data.get("config_id")
        content_type_id = data.get("content_type_id")
        search_data = data.get("search_data", {})
        limit = data.get("limit", 10)
        limit = int(limit)

        # Получаем конфигурацию
        config = SearchConfig.objects.get(
            id=config_id, content_type_id=content_type_id, is_active=True
        )

        # Получаем модель
        model_class = config.content_type.model_class()

        # Строим запрос
        query = Q()
        search_fields = config.fields.filter(is_searchable=True)

        # Дополнительные фильтры
        for field in search_fields:
            field_name = field.field_name
            value = search_data.get(field_name)

            if not value and field.field_type != "date_range":
                continue

            if field.field_type == "text":
                field_lookup = f"{field_name}__icontains"
                query &= Q(**{field_lookup: value})

            # elif field.field_type == "checkbox":
            #     if value == "on" or value is True:
            #         query &= Q(**{field_name: True})
            #     elif value == "off" or value is False:
            #         query &= Q(**{field_name: False})

            elif field.field_type in ("select_multiple", "select"):
                if isinstance(value, list):
                    # OR запрос через | для каждого значения
                    select_q = Q()
                    for val in value:
                        select_q |= Q(**{field_name: val})
                    query &= select_q

            # elif field.field_type == "radio":
            #     query &= Q(**{field_name: value})

            # elif field.field_type == "number":
            #     query &= Q(**{field_name: value})

            elif field.field_type == "date_range":
                if date_min := search_data.get(f"{field_name}_min"):
                    date_min = datetime.strptime(date_min, "%d.%m.%Y").date()
                    query &= Q(**{f"{field_name}__gte": date_min})
                if date_max := search_data.get(f"{field_name}_max"):
                    date_max = datetime.strptime(date_max, "%d.%m.%Y").date()
                    query &= Q(**{f"{field_name}__lte": date_max})

            elif field.field_type == "range":
                if value[0]:
                    query &= Q(**{f"{field_name}__gte": value[0]})
                if value[1]:
                    query &= Q(**{f"{field_name}__lte": value[1]})

        # Выполняем поиск
        _q = model_class.objects.filter(query).query
        results = model_class.objects.filter(query)[:limit]

        # Формируем ответ
        formatted_results = []
        for obj in results:
            formatted_results.append(
                {
                    "id": obj.id,
                    "content_type": f"{obj._meta.app_label}.{obj._meta.model_name}",
                    "title": str(obj),
                    "description": (
                        getattr(obj, "description", "")[:100]
                        if hasattr(obj, "description")
                        else ""
                    ),
                    "url": (
                        obj.get_absolute_url()
                        if hasattr(obj, "get_absolute_url")
                        else None
                    ),
                }
            )

        return JsonResponse(
            {
                "success": True,
                "query": str(_q),
                "results": formatted_results,
                "total": results.count(),
                "has_more": results.count() >= limit,
                "show_count": config.show_results_count,
                "search_id": f"{config_id}_{content_type_id}",
            }
        )

    except SearchConfig.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "Конфигурация поиска не найдена"}, status=404
        )

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


def get_field_choices(request, config_id, field_id):
    """Получение вариантов выбора для поля из модели"""
    try:
        field = SearchField.objects.get(id=field_id, config_id=config_id)
        model_class = field.config.content_type.model_class()

        choices = []

        # Получаем поле модели
        try:
            model_field = model_class._meta.get_field(field.field_name)

            if hasattr(model_field, "choices") and model_field.choices:
                choices = [
                    {"value": choice[0], "label": choice[1]}
                    for choice in model_field.choices
                ]
            # Если поле BooleanField
            # Если поле ForeignKey
            elif hasattr(model_field, "related_model"):
                related_model = model_field.related_model
                # Берем все объекты или ограниченное количество
                objects = related_model.objects.all()[:100]
                choices = [{"value": obj.id, "label": str(obj)} for obj in objects]

            # Если поле с choices (TextChoices или Choices)
            elif hasattr(model_field, "choices") and model_field.choices:
                choices = [
                    {"value": choice[0], "label": choice[1]}
                    for choice in model_field.choices
                ]

            # Если поле BooleanField
            elif model_field.get_internal_type() == "BooleanField":
                choices = [
                    {"value": "true", "label": "Да"},
                    {"value": "false", "label": "Нет"},
                ]

            # Если в модели есть метод get_xxx_choices
            choices_method_name = f"get_{field.field_name}_choices"
            if hasattr(model_class, choices_method_name):
                choices_method = getattr(model_class, choices_method_name)
                custom_choices = choices_method()
                if isinstance(custom_choices, (list, tuple)):
                    choices = [
                        {"value": choice[0], "label": choice[1]}
                        for choice in custom_choices
                    ]

        except Exception as e:
            # Если не удалось получить из модели, используем сохраненные choices
            choices_dict = field.get_choices_dict()
            choices = [
                {"value": key, "label": label} for key, label in choices_dict.items()
            ]

        return JsonResponse(
            {
                "success": True,
                "choices": choices,
                "model": str(model_class),
                "field_type": field.field_type,
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)
