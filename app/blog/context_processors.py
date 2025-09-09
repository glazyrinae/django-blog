def global_context(request):
    from .models import Category, Post, SocialMedia, BlogSettings # пример моделей

    url_parts = request.path.split("/")
    url_parts = [url_part for url_part in url_parts if url_part]
    active = url_parts[0] if len(url_parts) > 0 else "home"
    blog_settings = BlogSettings.objects.values().first()

    
    return {
        "categories": Category.objects.all(),
        "active": active,
        "cnt_posts": Post.published.count(),
        "title": blog_settings.get("blog_title", ""),
        "about": blog_settings.get("blog_desc", ""),
        "footer": blog_settings.get("blog_footer",""),
        "avatar": blog_settings.get("avatar",""),
        "social_media": SocialMedia.objects.all()
    }
