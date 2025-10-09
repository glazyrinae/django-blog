def global_context(request):
    from .models import Category, Post, SocialMedia, BlogSettings  # пример моделей

    # Вычисляем активный раздел
    url_parts = request.path.strip("/").split("/")
    active_section = url_parts[0] if url_parts else "home"

    # Получаем настройки блога
    try:
        settings = (
            BlogSettings.objects.values(
                "blog_title", "blog_desc", "blog_footer", "avatar"
            ).first()
            or {}
        )
    except Exception as e:
        print(f"How exceptional! {e}")
        settings = {}

    return {
        "categories": Category.objects.all(),
        "active": active_section,
        "cnt_posts": Post.published.count(),
        "title": settings.get("blog_title", ""),
        "about": settings.get("blog_desc", ""),
        "footer": settings.get("blog_footer", ""),
        "avatar": settings.get("avatar", ""),
        "social_media": SocialMedia.objects.all(),
    }
