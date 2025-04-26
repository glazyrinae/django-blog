def global_context(request):
    from .models import Category, Post  # пример моделей

    url_parts = request.path.split("/")
    url_parts = [url_part for url_part in url_parts if url_part]
    active = url_parts[1] if len(url_parts) > 1 else "home"
    return {
        "categories": Category.objects.all(),
        "active": active,
        "cnt_posts": Post.published.count(),
    }
